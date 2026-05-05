"""
src/run_backtest.py
-------------------
CLI runner for strategy backtests.

Usage
-----
    # Uses all defaults from configs/backtest.yaml
    python -m src.run_backtest

    # Override strategy windows and timeframe at runtime
    python -m src.run_backtest --fast 10 --slow 30 --timeframe 1D

    # Point to a custom config
    python -m src.run_backtest --config configs/backtest.yaml

Outputs (in results/)
---------------------
    {run_id}_stats.csv     — full vbt stats table
    {run_id}_equity.html   — interactive Plotly equity curve
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import vectorbt as vbt
import yaml

from src.strategies.ma_cross import MACrossStrategy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "backtest.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_cfg(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


def _load_ohlcv(cfg: dict, timeframe: str) -> pd.DataFrame:
    """Read the Parquet produced by data_pipeline for *timeframe*."""
    template: str = cfg["data"]["parquet"]
    parquet_path = Path(template.format(timeframe=timeframe))
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Parquet not found: {parquet_path}\n"
            f"Run the data pipeline first:\n"
            f"  python -m src.data_pipeline --provider yfinance --start 2015-01-01"
        )
    df = pd.read_parquet(parquet_path)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, utc=True)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    logger.info("Loaded %d bars from %s", len(df), parquet_path)
    return df


def _build_run_id(strategy_name: str, timeframe: str, fast: int, slow: int) -> str:
    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{strategy_name}_{timeframe}_{fast}x{slow}_{date_tag}"


def _infer_freq(index: pd.DatetimeIndex) -> str:
    """
    Infer a pandas frequency string from an unevenly-spaced DatetimeIndex.
    Falls back to the most common gap if pd.infer_freq returns None.
    """
    freq = pd.infer_freq(index)
    if freq is not None:
        return freq
    # Fallback: use the median timedelta
    deltas = index.to_series().diff().dropna()
    median_delta = deltas.median()
    total_seconds = int(median_delta.total_seconds())
    mapping = {
        60:      "1min",
        300:     "5min",
        900:     "15min",
        3600:    "1h",
        14400:   "4h",
        86400:   "1D",
    }
    return mapping.get(total_seconds, "1D")


# ---------------------------------------------------------------------------
# Core backtest
# ---------------------------------------------------------------------------

def run_backtest(
    cfg: dict,
    fast_window: int | None = None,
    slow_window: int | None = None,
    timeframe: str | None = None,
) -> tuple[pd.Series, vbt.Portfolio]:
    """
    Execute the MA-cross backtest.

    Parameters
    ----------
    cfg : dict
        Full config from backtest.yaml.
    fast_window, slow_window : int, optional
        Override strategy windows from config.
    timeframe : str, optional
        Override data.timeframe from config (e.g. ``"1h"``).

    Returns
    -------
    stats : pd.Series
        Full vbt stats.
    pf : vbt.Portfolio
        Portfolio object (for further analysis / plotting).
    """
    # --- resolve effective config values ---------------------------------
    strat_cfg  = cfg["strategy"]
    port_cfg   = cfg["portfolio"]
    tf         = timeframe or cfg["data"]["timeframe"]
    fast       = fast_window or strat_cfg["fast_window"]
    slow       = slow_window or strat_cfg["slow_window"]

    # --- load data -------------------------------------------------------
    ohlcv = _load_ohlcv(cfg, tf)
    close = ohlcv["Close"].dropna()

    # --- generate signals ------------------------------------------------
    strategy = MACrossStrategy(strat_cfg, fast_window=fast, slow_window=slow)
    signals  = strategy.generate(close)
    logger.info(signals.summary())

    # --- infer frequency -------------------------------------------------
    freq = port_cfg.get("freq") or _infer_freq(close.index)
    logger.info("Using frequency: %s", freq)

    # --- build portfolio -------------------------------------------------
    fees     = float(port_cfg.get("fees", 0.0002))
    slippage = float(port_cfg.get("slippage", 0.0001))

    # vbt applies slippage as a price multiplier offset; convert to a
    # simple callable that bumps fills by `slippage` fraction.
    pf = vbt.Portfolio.from_signals(
        close=close,
        entries=signals.entries,
        exits=signals.exits,
        init_cash=float(port_cfg.get("init_cash", 100_000)),
        fees=fees,
        slippage=slippage,
        size=float(port_cfg.get("size", 1.0)),
        size_type=port_cfg.get("size_type", "percent"),
        freq=freq,
    )

    stats = pf.stats()
    return stats, pf


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _save_outputs(
    pf: vbt.Portfolio,
    stats: pd.Series,
    cfg: dict,
    run_id: str,
    fast: int,
    slow: int,
) -> None:
    results_dir = Path(cfg["output"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    # Stats CSV
    stats_path = Path(cfg["output"]["stats_csv"].format(run_id=run_id))
    stats.to_csv(stats_path, header=["value"])
    logger.info("Stats saved → %s", stats_path)

    # Equity curve HTML
    equity_path = Path(cfg["output"]["equity_html"].format(run_id=run_id))

    fig = pf.plot(
        subplots=["cum_returns", "trade_pnl", "drawdowns"],
    )
    fig.update_layout(
        title=dict(
            text=f"MA Cross  fast={fast}  slow={slow}  |  "
                 f"Total Return: {stats.get('Total Return [%]', float('nan')):.2f}%  "
                 f"Sharpe: {stats.get('Sharpe Ratio', float('nan')):.2f}",
            x=0.5,
        ),
        template="plotly_dark",
    )
    fig.write_html(str(equity_path))
    logger.info("Equity curve saved → %s", equity_path)


def _print_stats(stats: pd.Series) -> None:
    keys = [
        "Start", "End", "Period",
        "Total Return [%]", "Benchmark Return [%]",
        "Max Drawdown [%]", "Max Drawdown Duration",
        "Sharpe Ratio", "Calmar Ratio", "Omega Ratio",
        "Total Trades", "Win Rate [%]",
        "Avg Winning Trade [%]", "Avg Losing Trade [%]",
        "Profit Factor",
    ]
    print("\n── Backtest Results ──────────────────────────────────")
    for k in keys:
        if k in stats.index:
            print(f"  {k:<35} {stats[k]}")
    print("─────────────────────────────────────────────────────\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.run_backtest",
        description="Run MA crossover backtest on GOLD OHLCV data.",
    )
    parser.add_argument(
        "--config",
        default=str(_CONFIG_PATH),
        help=f"Path to backtest.yaml (default: {_CONFIG_PATH})",
    )
    parser.add_argument(
        "--fast",
        type=int,
        default=None,
        help="Fast MA window (overrides config)",
    )
    parser.add_argument(
        "--slow",
        type=int,
        default=None,
        help="Slow MA window (overrides config)",
    )
    parser.add_argument(
        "--timeframe",
        default=None,
        help="Timeframe folder to use, e.g. 1D, 1h, 4h (overrides config)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    cfg = _load_cfg(Path(args.config))

    # Resolve effective params for run_id
    fast = args.fast or cfg["strategy"]["fast_window"]
    slow = args.slow or cfg["strategy"]["slow_window"]
    tf   = args.timeframe or cfg["data"]["timeframe"]

    run_id = _build_run_id(cfg["strategy"]["name"], tf, fast, slow)
    logger.info("Run ID: %s", run_id)

    try:
        stats, pf = run_backtest(cfg, fast_window=args.fast, slow_window=args.slow, timeframe=args.timeframe)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        sys.exit(1)

    _print_stats(stats)
    _save_outputs(pf, stats, cfg, run_id, fast, slow)


if __name__ == "__main__":
    main()
