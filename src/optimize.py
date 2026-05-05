"""
src/optimize.py
---------------
Optuna-based hyperparameter optimization for the MA-cross strategy.

Searches fast_window × slow_window × ma_type until constraints are met
or budget is exhausted.

Constraints (from configs/objectives.yaml)
------------------------------------------
  Sharpe >= min_sharpe
  Max Drawdown <= max_drawdown  (%)
  Total Trades >= min_trades

Objective (single-objective Optuna study)
-----------------------------------------
  score = w_sharpe * sharpe
        + w_return * total_return_%
        - w_drawdown * max_drawdown_%

  Infeasible trials return -inf and are excluded from leaderboard / best params.

Early stopping
--------------
  Stops at whichever comes first:
    (a) n_feasible constraint-satisfying trials found
    (b) max_trials total trials executed

Outputs
-------
  results/best_params.json    — best params per timeframe
  results/leaderboard.csv     — top-N trials across all timeframes

CLI usage
---------
    python -m src.optimize
    python -m src.optimize --timeframes 1D 1h
    python -m src.optimize --max-trials 300 --n-feasible 30
    python -m src.optimize --config configs/objectives.yaml \
                           --backtest-config configs/backtest.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import optuna
import pandas as pd
import vectorbt as vbt
import yaml

from src.run_backtest import _infer_freq, _load_ohlcv
from src.strategies.ma_cross import MACrossStrategy

# Suppress Optuna's verbose per-trial logs; we handle summary ourselves.
optuna.logging.set_verbosity(optuna.logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_OBJ_CFG_PATH = Path(__file__).parent.parent / "configs" / "objectives.yaml"
_BT_CFG_PATH  = Path(__file__).parent.parent / "configs" / "backtest.yaml"

# Sentinel value returned for infeasible / errored trials
_INFEASIBLE = -1e12


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Extra metrics computed from the Portfolio object
# ---------------------------------------------------------------------------

def _compute_extra_metrics(pf: vbt.Portfolio) -> dict:
    """
    Compute per-day and per-month metrics that vbt.stats() does not expose.

    Returns
    -------
    dict with keys:
        max_daily_loss_pct   — worst single-day loss (%, positive = loss)
        min_monthly_return   — worst calendar-month return (%)
        min_trades_per_month — minimum number of trades in any calendar month
    """
    result: dict = {
        "max_daily_loss_pct":   math.nan,
        "min_monthly_return":   math.nan,
        "min_trades_per_month": 0,
    }

    try:
        daily_ret = pf.returns()
        if len(daily_ret) > 0:
            # Worst single-period loss (positive value = loss magnitude)
            worst = float(daily_ret.min())
            result["max_daily_loss_pct"] = abs(worst) * 100 if worst < 0 else 0.0

            # Monthly compounded returns
            monthly = (
                daily_ret
                .resample("ME")
                .apply(lambda x: (1 + x).prod() - 1)
                * 100
            )
            if len(monthly) > 0:
                result["min_monthly_return"] = float(monthly.min())
    except Exception:  # noqa: BLE001
        pass  # leave as nan — _is_feasible will mark it infeasible

    try:
        trades_readable = pf.trades.records_readable
        if len(trades_readable) > 0:
            exit_col = next(
                (c for c in trades_readable.columns
                 if "exit" in c.lower() and "time" in c.lower()),
                None,
            )
            if exit_col:
                exit_ts = pd.to_datetime(trades_readable[exit_col])
                monthly_counts = exit_ts.dt.to_period("M").value_counts()
                result["min_trades_per_month"] = int(monthly_counts.min())
    except Exception:  # noqa: BLE001
        pass

    return result


# ---------------------------------------------------------------------------
# Constraint checker
# ---------------------------------------------------------------------------

def _is_feasible(
    stats: pd.Series,
    extra: dict,
    constraints: dict,
) -> tuple[bool, str]:
    """
    Check whether a stats Series (+ extra metrics) satisfies all constraints.

    Returns
    -------
    (feasible: bool, reason: str)
        reason is empty when feasible, or describes the first violated constraint.
    """
    sharpe   = stats.get("Sharpe Ratio",     math.nan)
    drawdown = stats.get("Max Drawdown [%]", math.nan)

    if math.isnan(sharpe) or math.isinf(sharpe):
        return False, "Sharpe is NaN/Inf"
    if sharpe < constraints["min_sharpe"]:
        return False, f"Sharpe {sharpe:.3f} < {constraints['min_sharpe']}"

    if math.isnan(drawdown):
        return False, "Max Drawdown is NaN"
    if abs(drawdown) > constraints["max_drawdown"]:
        return False, f"Drawdown {abs(drawdown):.2f}% > {constraints['max_drawdown']}%"

    # --- new per-day / per-month constraints ---
    max_daily_loss = extra.get("max_daily_loss_pct", math.nan)
    if math.isnan(max_daily_loss):
        return False, "max_daily_loss_pct is NaN"
    if max_daily_loss > constraints["max_daily_loss"]:
        return False, (
            f"Worst day loss {max_daily_loss:.2f}% > {constraints['max_daily_loss']}%"
        )

    min_monthly_ret = extra.get("min_monthly_return", math.nan)
    if math.isnan(min_monthly_ret):
        return False, "min_monthly_return is NaN"
    if min_monthly_ret < constraints["min_monthly_return"]:
        return False, (
            f"Worst month return {min_monthly_ret:.2f}% < "
            f"{constraints['min_monthly_return']}%"
        )

    min_trades_mo = extra.get("min_trades_per_month", 0)
    if min_trades_mo < constraints["min_trades_per_month"]:
        return False, (
            f"Min trades/month {min_trades_mo} < {constraints['min_trades_per_month']}"
        )

    return True, ""


# ---------------------------------------------------------------------------
# Composite score (primary objective passed to Optuna)
# ---------------------------------------------------------------------------

def _composite_score(stats: pd.Series, weights: dict) -> float:
    sharpe   = float(stats.get("Sharpe Ratio",        0.0) or 0.0)
    ret_pct  = float(stats.get("Total Return [%]",    0.0) or 0.0)
    dd_pct   = abs(float(stats.get("Max Drawdown [%]", 0.0) or 0.0))

    w_s = float(weights.get("sharpe",   1.0))
    w_r = float(weights.get("return",   0.005))
    w_d = float(weights.get("drawdown", 0.002))

    return w_s * sharpe + w_r * ret_pct - w_d * dd_pct


# ---------------------------------------------------------------------------
# Early-stopping callback
# ---------------------------------------------------------------------------

class _EarlyStopCallback:
    """
    Stops the Optuna study when *n_feasible* constraint-passing trials
    have been found OR when *max_trials* total trials are done.

    Feasibility is signalled by a score > _INFEASIBLE.
    """

    def __init__(self, n_feasible: int, max_trials: int) -> None:
        self._n_feasible = n_feasible
        self._max_trials = max_trials
        self._feasible_count = 0

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        if trial.value is not None and trial.value > _INFEASIBLE:
            self._feasible_count += 1

        if self._feasible_count >= self._n_feasible:
            logger.info(
                "Early stop: %d feasible trials found (target %d).",
                self._feasible_count, self._n_feasible,
            )
            study.stop()
            return

        if trial.number + 1 >= self._max_trials:
            logger.info(
                "Early stop: max_trials (%d) reached.", self._max_trials
            )
            study.stop()


# ---------------------------------------------------------------------------
# Objective factory
# ---------------------------------------------------------------------------

def _make_objective(
    close: pd.Series,
    freq: str,
    portfolio_cfg: dict,
    constraints: dict,
    weights: dict,
    search_space: dict,
    trial_records: list[dict],
    timeframe: str,
) -> Any:
    """
    Return an Optuna objective callable closed over the close series.

    Each trial appends a record to *trial_records* (shared list) so we
    can build the leaderboard without re-running anything.
    """

    def objective(trial: optuna.Trial) -> float:
        # --- sample hyperparameters --------------------------------------
        ss = search_space
        fast = trial.suggest_int(
            "fast_window",
            ss["fast_window"]["low"],
            ss["fast_window"]["high"],
            step=ss["fast_window"].get("step", 1),
        )
        slow = trial.suggest_int(
            "slow_window",
            ss["slow_window"]["low"],
            ss["slow_window"]["high"],
            step=ss["slow_window"].get("step", 1),
        )
        ma_type = trial.suggest_categorical(
            "ma_type", ss["ma_type"]["choices"]
        )

        # fast must be < slow; prune immediately if not
        if fast >= slow:
            trial.set_user_attr("infeasible_reason", f"fast({fast}) >= slow({slow})")
            return _INFEASIBLE

        # --- run strategy ------------------------------------------------
        try:
            strategy = MACrossStrategy(
                {"fast_window": fast, "slow_window": slow, "ma_type": ma_type}
            )
            signals = strategy.generate(close)
        except ValueError as exc:
            trial.set_user_attr("infeasible_reason", str(exc))
            return _INFEASIBLE

        # --- build portfolio ---------------------------------------------
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pf = vbt.Portfolio.from_signals(
                    close=close,
                    entries=signals.entries,
                    exits=signals.exits,
                    init_cash=float(portfolio_cfg.get("init_cash", 100_000)),
                    fees=float(portfolio_cfg.get("fees", 0.0002)),
                    slippage=float(portfolio_cfg.get("slippage", 0.0001)),
                    size=float(portfolio_cfg.get("size", 1.0)),
                    size_type=portfolio_cfg.get("size_type", "percent"),
                    freq=freq,
                )
            stats = pf.stats()
            extra = _compute_extra_metrics(pf)
        except Exception as exc:  # noqa: BLE001
            trial.set_user_attr("infeasible_reason", f"vbt error: {exc}")
            return _INFEASIBLE

        # --- constraint check --------------------------------------------
        feasible, reason = _is_feasible(stats, extra, constraints)
        if not feasible:
            trial.set_user_attr("infeasible_reason", reason)
            score = _INFEASIBLE
        else:
            score = _composite_score(stats, weights)

        # --- store record for leaderboard --------------------------------
        sharpe   = float(stats.get("Sharpe Ratio",        math.nan) or math.nan)
        dd       = float(stats.get("Max Drawdown [%]",    math.nan) or math.nan)
        ret_pct  = float(stats.get("Total Return [%]",    math.nan) or math.nan)
        n_trades = int(stats.get("Total Trades", 0) or 0)

        trial_records.append({
            "timeframe":            timeframe,
            "trial":                trial.number,
            "fast_window":          fast,
            "slow_window":          slow,
            "ma_type":              ma_type,
            "sharpe":               sharpe,
            "max_drawdown":         abs(dd) if not math.isnan(dd) else math.nan,
            "total_return":         ret_pct,
            "n_trades":             n_trades,
            "max_daily_loss_pct":   extra.get("max_daily_loss_pct",   math.nan),
            "min_monthly_return":   extra.get("min_monthly_return",   math.nan),
            "min_trades_per_month": extra.get("min_trades_per_month", 0),
            "score":                score,
            "feasible":             feasible,
        })

        return score

    return objective


# ---------------------------------------------------------------------------
# Per-timeframe optimization
# ---------------------------------------------------------------------------

def optimize_timeframe(
    timeframe: str,
    obj_cfg: dict,
    bt_cfg: dict,
    trial_records: list[dict],
) -> dict | None:
    """
    Run Optuna study for one timeframe.

    Returns best params dict or None if no feasible trial found.
    """
    logger.info("── Optimizing timeframe: %s ──────────────────────", timeframe)

    # Load price data
    try:
        ohlcv = _load_ohlcv(bt_cfg, timeframe)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return None

    close = ohlcv["Close"].dropna()
    freq  = bt_cfg["portfolio"].get("freq") or _infer_freq(close.index)
    logger.info("  %d bars loaded, freq=%s", len(close), freq)

    # Config sections
    constraints  = obj_cfg["constraints"]
    weights      = obj_cfg["objective"]["weights"]
    search_space = obj_cfg["search_space"]
    stopping     = obj_cfg["stopping"]
    optuna_cfg   = obj_cfg.get("optuna", {})

    # Sampler
    sampler_name = optuna_cfg.get("sampler", "tpe").lower()
    seed         = optuna_cfg.get("seed", 42)
    if sampler_name == "tpe":
        sampler = optuna.samplers.TPESampler(seed=seed)
    elif sampler_name == "cmaes":
        sampler = optuna.samplers.CmaEsSampler(seed=seed)
    else:
        sampler = optuna.samplers.RandomSampler(seed=seed)

    study = optuna.create_study(
        direction="maximize",
        sampler=sampler,
        study_name=f"ma_cross_{timeframe}",
    )

    callback = _EarlyStopCallback(
        n_feasible=stopping["n_feasible"],
        max_trials=stopping["max_trials"],
    )

    objective_fn = _make_objective(
        close=close,
        freq=freq,
        portfolio_cfg=bt_cfg["portfolio"],
        constraints=constraints,
        weights=weights,
        search_space=search_space,
        trial_records=trial_records,
        timeframe=timeframe,
    )

    study.optimize(
        objective_fn,
        n_trials=stopping["max_trials"],
        callbacks=[callback],
        show_progress_bar=optuna_cfg.get("show_progress_bar", True),
        catch=(Exception,),
    )

    # Extract best feasible trial
    feasible_trials = [
        t for t in study.trials
        if t.value is not None and t.value > _INFEASIBLE
    ]
    if not feasible_trials:
        logger.warning("No feasible trials found for timeframe %s.", timeframe)
        return None

    best = max(feasible_trials, key=lambda t: t.value)
    logger.info(
        "  Best trial #%d: score=%.4f  params=%s",
        best.number, best.value, best.params,
    )

    # Attach metrics from records
    best_record = next(
        (r for r in trial_records
         if r["timeframe"] == timeframe and r["trial"] == best.number),
        {},
    )

    return {
        "timeframe":            timeframe,
        "trial":                best.number,
        "score":                best.value,
        **best.params,
        "sharpe":               best_record.get("sharpe"),
        "max_drawdown":         best_record.get("max_drawdown"),
        "max_daily_loss_pct":   best_record.get("max_daily_loss_pct"),
        "min_monthly_return":   best_record.get("min_monthly_return"),
        "min_trades_per_month": best_record.get("min_trades_per_month"),
        "total_return":         best_record.get("total_return"),
        "n_trades":             best_record.get("n_trades"),
        "n_feasible":           len(feasible_trials),
        "n_total":              len(study.trials),
    }


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _save_best_params(best_per_tf: dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing file so we can merge (preserve other timeframes)
    existing: dict = {}
    if path.exists():
        try:
            with path.open() as fh:
                existing = json.load(fh)
        except (json.JSONDecodeError, OSError):
            existing = {}

    existing.update(best_per_tf)
    with path.open("w") as fh:
        json.dump(existing, fh, indent=2, default=str)
    logger.info("Best params → %s", path)


def _save_leaderboard(
    trial_records: list[dict],
    path: Path,
    top_n: int,
) -> None:
    if not trial_records:
        logger.warning("No trial records to build leaderboard.")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(trial_records)

    # Load existing leaderboard and merge
    if path.exists():
        try:
            old = pd.read_csv(path)
            df = pd.concat([old, df], ignore_index=True)
        except (pd.errors.EmptyDataError, OSError):
            pass

    df = (
        df[df["feasible"]]
        .sort_values("score", ascending=False)
        .drop_duplicates(subset=["timeframe", "fast_window", "slow_window", "ma_type"])
        .head(top_n)
        .reset_index(drop=True)
    )
    df.to_csv(path, index=False)
    logger.info("Leaderboard (top %d) → %s", len(df), path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_optimization(
    timeframes: list[str],
    obj_cfg: dict,
    bt_cfg: dict,
) -> tuple[dict[str, dict], list[dict]]:
    """
    Optimize across all *timeframes*.

    Returns
    -------
    best_per_tf : dict[timeframe → best params dict]
    trial_records : list of all trial record dicts
    """
    trial_records: list[dict] = []
    best_per_tf: dict[str, dict] = {}

    for tf in timeframes:
        result = optimize_timeframe(tf, obj_cfg, bt_cfg, trial_records)
        if result is not None:
            best_per_tf[tf] = result

    return best_per_tf, trial_records


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.optimize",
        description="Optuna optimization of MA-cross strategy on GOLD data.",
    )
    parser.add_argument(
        "--config",
        default=str(_OBJ_CFG_PATH),
        help=f"Path to objectives.yaml (default: {_OBJ_CFG_PATH})",
    )
    parser.add_argument(
        "--backtest-config",
        default=str(_BT_CFG_PATH),
        help=f"Path to backtest.yaml (default: {_BT_CFG_PATH})",
    )
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=None,
        metavar="TF",
        help="Timeframes to optimize, e.g. --timeframes 1D 1h (overrides yaml)",
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Hard cap on total trials per timeframe (overrides yaml)",
    )
    parser.add_argument(
        "--n-feasible",
        type=int,
        default=None,
        help="Early-stop after this many feasible trials (overrides yaml)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    obj_cfg = _load_yaml(Path(args.config))
    bt_cfg  = _load_yaml(Path(args.backtest_config))

    # CLI overrides
    timeframes = args.timeframes or obj_cfg["timeframes"]
    if args.max_trials is not None:
        obj_cfg["stopping"]["max_trials"] = args.max_trials
    if args.n_feasible is not None:
        obj_cfg["stopping"]["n_feasible"] = args.n_feasible

    logger.info(
        "Optimizing %d timeframe(s): %s | max_trials=%d | n_feasible=%d",
        len(timeframes), timeframes,
        obj_cfg["stopping"]["max_trials"],
        obj_cfg["stopping"]["n_feasible"],
    )

    best_per_tf, trial_records = run_optimization(timeframes, obj_cfg, bt_cfg)

    if not best_per_tf:
        logger.error("No feasible results found across all timeframes.")
        sys.exit(1)

    out_cfg  = obj_cfg["output"]
    _save_best_params(best_per_tf, Path(out_cfg["best_params_json"]))
    _save_leaderboard(
        trial_records,
        Path(out_cfg["leaderboard_csv"]),
        top_n=out_cfg.get("leaderboard_top_n", 50),
    )

    # Summary table
    print("\n── Optimization Summary ─────────────────────────────────")
    for tf, p in best_per_tf.items():
        print(
            f"  {tf:>4}  fast={p.get('fast_window'):>3}  slow={p.get('slow_window'):>3}"
            f"  ma={p.get('ma_type','?'):<12}"
            f"  sharpe={p.get('sharpe', float('nan')):.3f}"
            f"  dd={p.get('max_drawdown', float('nan')):.1f}%"
            f"  worst_day={p.get('max_daily_loss_pct', float('nan')):.2f}%"
            f"  worst_mo={p.get('min_monthly_return', float('nan')):.1f}%"
            f"  min_trades/mo={p.get('min_trades_per_month', '?')}"
            f"  ret={p.get('total_return', float('nan')):.1f}%"
            f"  feasible={p.get('n_feasible','?')}/{p.get('n_total','?')}"
        )
    print("─────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
