#!/usr/bin/env python3
"""
Iterative Strategy Optimizer — XAUUSD 2016-2026
================================================
Objetivos por timeframe:
  monthly_return >= 2.0%
  max_drawdown   >= -7.0%   (DD <= 7%)
  trades/month   >= 7
  worst_day      >= -3.0%   (more conservative than prop firm 5%)

Enfoque:
  MA Cross (alta frecuencia de trades) +
  EMA(200) filtro macro (no shortear en bull market) +
  ATR-based SL/TP (evitar "Gold Trap") +
  Filtros de sesión/día/ADR

Itera parámetros via grid search y registra la mejor combinación
por cada timeframe. Si no alcanza el objetivo, intenta combinaciones
más agresivas/conservadoras y reporta lo más cercano.
"""

import itertools
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# OBJETIVOS
# ─────────────────────────────────────────────────────────────────────────────
OBJ_MONTHLY   = 2.0     # >= 2% mensual
OBJ_DD        = -7.0    # >= -7% (MaxDD)
OBJ_TRADES    = 7.0     # >= 7 trades/mes
OBJ_WORST_DAY = -3.0    # >= -3% peor día

YEARS  = 10.3
MONTHS = YEARS * 12     # 123.6 meses

# ─────────────────────────────────────────────────────────────────────────────
# RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────
RESAMPLE_RULES = {
    "15min": None,
    "30min": "30min",
    "1h":    "1h",
    "2h":    "2h",
    "3h":    "3h",
    "4h":    "4h",
    "1D":    "1D",
}


def resample_ohlcv(df_m15: pd.DataFrame, rule: str | None) -> pd.DataFrame:
    if rule is None:
        return df_m15.copy()
    agg = {"open": "first", "high": "max", "low": "min",
           "close": "last", "volume": "sum"}
    return df_m15.resample(rule).agg(agg).dropna(subset=["close"])


# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    return pd.concat([hl, hc, lc], axis=1).max(axis=1).ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d  = s.diff()
    up = d.clip(lower=0)
    dn = (-d).clip(lower=0)
    rs = up.ewm(span=n, adjust=False).mean() / dn.ewm(span=n, adjust=False).mean()
    return 100 - 100 / (1 + rs)


def cmf(df: pd.DataFrame, n: int = 20) -> pd.Series:
    denom  = (df["high"] - df["low"]).replace(0, np.nan)
    mf_mul = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / denom
    return (mf_mul * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum().replace(0, np.nan)


def add_indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    df = df.copy()
    df["ema_f"]   = ema(df["close"], p["ema_fast"])
    df["ema_s"]   = ema(df["close"], p["ema_slow"])
    df["ema_200"] = ema(df["close"], 200)
    df["atr14"]   = atr(df, 14)
    df["rsi14"]   = rsi(df["close"], 14)
    df["cmf20"]   = cmf(df, 20)
    # ADR (average daily range rolling)
    daily_hl = df.groupby(df.index.date).apply(lambda g: g["high"].max() - g["low"].min())
    daily_hl.index = pd.to_datetime(daily_hl.index)
    adr_roll = daily_hl.rolling(14).mean()
    bar_dates = pd.to_datetime(df.index.date)
    df["adr"] = bar_dates.map(adr_roll.to_dict()).values
    # Intraday range so far (vectorized)
    date_col = df.index.normalize()
    day_hi   = df.groupby(date_col)["high"].cummax()
    day_lo   = df.groupby(date_col)["low"].cummin()
    df["day_range"] = day_hi - day_lo
    df["hour"]    = df.index.hour
    df["weekday"] = df.index.dayofweek
    return df


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL GENERATION
# MA Cross as primary signal + multi-filter system
# ─────────────────────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame, p: dict) -> np.ndarray:
    """
    Signal on bar i → entry on bar i+1 open.
    +1 = long, -1 = short, 0 = flat
    """
    n     = len(df)
    sig   = np.zeros(n, dtype=np.int8)
    wu    = max(210, p["ema_slow"] + 5)

    ef    = df["ema_f"].values
    es    = df["ema_s"].values
    em200 = df["ema_200"].values
    cl    = df["close"].values
    at    = df["atr14"].values
    rs    = df["rsi14"].values
    cm    = df["cmf20"].values
    adr_v = df["adr"].values
    drng  = df["day_range"].values
    hrs   = df["hour"].values
    wds   = df["weekday"].values

    use_session  = p.get("use_session", False)
    sess_start   = p.get("sess_start", 7)
    sess_end     = p.get("sess_end", 18)
    avoid_monday = p.get("avoid_monday", False)
    avoid_friday = p.get("avoid_friday", False)
    adr_cap      = p.get("adr_cap", 0.80)
    rsi_filter   = p.get("rsi_filter", False)
    cmf_filter   = p.get("cmf_filter", False)
    macro_filter = p.get("macro_filter", True)
    long_only    = p.get("long_only", False)   # no shorts in bull market

    for i in range(wu, n - 1):
        if np.isnan(ef[i]) or np.isnan(es[i]) or np.isnan(em200[i]):
            continue

        # ── Day/session filters ──────────────────────────────────────
        if avoid_monday and wds[i] == 0:
            continue
        if avoid_friday and wds[i] == 4:
            continue
        if use_session:
            if not (sess_start <= hrs[i] < sess_end):
                continue

        # ── ADR filter ────────────────────────────────────────────────
        if not np.isnan(adr_v[i]) and adr_v[i] > 0:
            if drng[i] / adr_v[i] > adr_cap:
                continue

        # ── MA Cross signal ───────────────────────────────────────────
        cross_up   = ef[i] > es[i] and ef[i-1] <= es[i-1]
        cross_down = ef[i] < es[i] and ef[i-1] >= es[i-1]

        # ── Macro filter EMA(200) ─────────────────────────────────────
        # In strong bull market: don't short at all (long_only mode)
        bull_macro = cl[i] > em200[i]
        bear_macro = cl[i] < em200[i]

        if macro_filter:
            if cross_down and bull_macro and long_only:
                continue   # skip shorts in bull market

        # ── RSI filter (avoid entering in extreme zones) ──────────────
        if rsi_filter:
            rsi_v = rs[i]
            if cross_up  and rsi_v > 75:   continue   # overbought on cross
            if cross_down and rsi_v < 25:  continue   # oversold on cross

        # ── CMF filter (volume confirmation) ─────────────────────────
        if cmf_filter and not np.isnan(cm[i]):
            if cross_up   and cm[i] < -0.05: continue
            if cross_down and cm[i] >  0.05: continue

        # ── Emit signal ───────────────────────────────────────────────
        if cross_up:
            if not macro_filter or not long_only or bull_macro:
                sig[i] = 1
        elif cross_down:
            if not (macro_filter and long_only and bull_macro):
                sig[i] = -1

    return sig


# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST ENGINE — ATR-based SL/TP with partial close
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame, sig: np.ndarray, p: dict,
                 initial: float = 100_000.0) -> tuple[list, np.ndarray]:
    """
    Entry: bar i+1 open when sig[i] != 0.
    SL = sl_mult × ATR  (dynamic)
    TP1 = tp1_ratio × SL_dist  (close 50%, move SL to BE)
    TP2 = tp2_ratio × SL_dist  (close remaining 50%)
    Risk per trade = risk_pct × capital
    Max daily loss = daily_limit × capital
    """
    n        = len(df)
    op       = df["open"].values
    hi       = df["high"].values
    lo       = df["low"].values
    at       = df["atr14"].values
    dates    = [idx.date() for idx in df.index]

    capital  = initial
    eq       = initial
    pos      = 0
    entry_p  = sl = tp1 = tp2 = risk_usd = 0.0
    tp1_done = False

    trades     = []
    equity_arr = np.full(n, initial, dtype=float)
    day_pnl    = {}
    day_cnt    = {}

    rp      = p["risk_pct"]
    dl      = p["daily_limit"]
    max_td  = p.get("max_trades_day", 99)
    sl_m    = p["sl_mult"]
    tp1_r   = p["tp1_ratio"]
    tp2_r   = p["tp2_ratio"]

    def gd(d):
        if d not in day_pnl:
            day_pnl[d] = 0.0; day_cnt[d] = 0

    for i in range(1, n):
        d = dates[i]
        gd(d)

        # ── Manage open position ──────────────────────────────────────
        if pos != 0:
            bop = op[i]; bhi = hi[i]; blo = lo[i]

            def _close(exit_p, pnl, etype):
                nonlocal eq, capital, pos, tp1_done
                eq += pnl; capital += pnl
                day_pnl[d] += pnl
                trades.append({"dir": "L" if pos == 1 else "S",
                                "entry": entry_p, "exit": exit_p,
                                "pnl_usd": pnl, "type": etype, "date": d})
                pos = 0; tp1_done = False

            if pos == 1:
                # Gap-through SL
                if bop <= sl:
                    _close(sl, -risk_usd, "SL_GAP"); continue
                # SL hit intrabar
                if blo <= sl:
                    if tp1_done:
                        _close(entry_p, 0.0, "BE")   # 2nd half at BE
                    else:
                        _close(sl, -risk_usd, "SL")
                    continue
                # TP1
                if not tp1_done and bhi >= tp1:
                    pnl1 = risk_usd * tp1_r * 0.5
                    eq += pnl1; capital += pnl1; day_pnl[d] += pnl1
                    sl = entry_p; tp1_done = True
                    if bhi >= tp2:
                        pnl2 = risk_usd * tp2_r * 0.5
                        _close(tp2, pnl2, "TP2")
                        trades[-1]["pnl_usd"] += pnl1  # merge
                        continue
                # TP2
                if tp1_done and bhi >= tp2:
                    _close(tp2, risk_usd * tp2_r * 0.5, "TP2")
                    continue

            else:  # SHORT
                if bop >= sl:
                    _close(sl, -risk_usd, "SL_GAP"); continue
                if bhi >= sl:
                    if tp1_done:
                        _close(entry_p, 0.0, "BE")
                    else:
                        _close(sl, -risk_usd, "SL")
                    continue
                if not tp1_done and blo <= tp1:
                    pnl1 = risk_usd * tp1_r * 0.5
                    eq += pnl1; capital += pnl1; day_pnl[d] += pnl1
                    sl = entry_p; tp1_done = True
                    if blo <= tp2:
                        pnl2 = risk_usd * tp2_r * 0.5
                        _close(tp2, pnl2, "TP2")
                        trades[-1]["pnl_usd"] += pnl1
                        continue
                if tp1_done and blo <= tp2:
                    _close(tp2, risk_usd * tp2_r * 0.5, "TP2"); continue

        # ── Entry check ───────────────────────────────────────────────
        if pos == 0:
            s = sig[i - 1]
            if s == 0:
                equity_arr[i] = eq; continue

            # Daily loss limit
            if day_pnl.get(d, 0) / capital <= -dl:
                equity_arr[i] = eq; continue
            # Daily trade limit
            if day_cnt.get(d, 0) >= max_td:
                equity_arr[i] = eq; continue

            at_i = at[i]
            if np.isnan(at_i) or at_i <= 0:
                equity_arr[i] = eq; continue

            entry_p  = op[i]
            sl_dist  = sl_m * at_i
            risk_usd = rp * capital

            if s == 1:
                sl = entry_p - sl_dist
                tp1 = entry_p + sl_dist * tp1_r
                tp2 = entry_p + sl_dist * tp2_r
                pos = 1
            else:
                sl = entry_p + sl_dist
                tp1 = entry_p - sl_dist * tp1_r
                tp2 = entry_p - sl_dist * tp2_r
                pos = -1

            tp1_done = False
            day_cnt[d] = day_cnt.get(d, 0) + 1

        equity_arr[i] = eq

    # Close remaining at end
    if pos != 0:
        lc  = df["close"].iloc[-1]
        pnl = (lc - entry_p) / entry_p * pos * risk_usd / (sl_m * at[-1] / entry_p + 1e-9)
        pnl = float(np.clip(pnl, -risk_usd * 2, risk_usd * 8))
        eq += pnl
        trades.append({"dir": "L" if pos == 1 else "S", "entry": entry_p,
                       "exit": lc, "pnl_usd": pnl, "type": "EOD", "date": dates[-1]})
        equity_arr[-1] = eq

    return trades, equity_arr


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(trades: list, equity_arr: np.ndarray,
                    initial: float = 100_000.0) -> dict:
    if not trades:
        return {"monthly": 0, "total": 0, "dd": 0, "sharpe": 0,
                "tpm": 0, "wr": 0, "worst_day": 0, "passed": False, "score": -999}

    eq = equity_arr[equity_arr > 0]
    if len(eq) < 2:
        eq = np.array([initial, equity_arr[-1]])

    total = (eq[-1] - initial) / initial * 100
    monthly = (((eq[-1] / initial) ** (1 / MONTHS)) - 1) * 100
    tpm = len(trades) / MONTHS

    run_max = np.maximum.accumulate(eq)
    dd_arr  = (eq - run_max) / run_max * 100
    max_dd  = float(dd_arr.min())

    # win = any trade where we got at least TP1 (pnl_usd > 0) OR BE (pnl=0 after TP1)
    wins = sum(1 for t in trades if t["pnl_usd"] > 0)
    wr   = wins / len(trades) * 100

    day_pnl: dict = {}
    for t in trades:
        ds = str(t["date"])
        day_pnl[ds] = day_pnl.get(ds, 0) + t["pnl_usd"]
    worst_day = min(day_pnl.values()) / initial * 100 if day_pnl else 0

    dret = np.diff(eq) / eq[:-1]
    sharpe = float(dret.mean() / (dret.std() + 1e-12) * np.sqrt(252)) if len(dret) > 1 else 0

    passed = (monthly >= OBJ_MONTHLY and max_dd >= OBJ_DD
              and tpm >= OBJ_TRADES and worst_day >= OBJ_WORST_DAY)

    # Score for ranking (even when not passing)
    score = (
        monthly * 1.0
        + (max_dd - OBJ_DD) * 0.3     # bonus for low DD
        + min(tpm, 50) * 0.05
        + sharpe * 0.5
        + (10 if passed else 0)
    )

    return dict(monthly=round(monthly, 3), total=round(total, 2),
                dd=round(max_dd, 2), sharpe=round(sharpe, 3),
                tpm=round(tpm, 1), wr=round(wr, 1),
                worst_day=round(worst_day, 2), passed=passed,
                score=round(score, 3), n=len(trades))


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETER SEARCH SPACE
# ─────────────────────────────────────────────────────────────────────────────

def build_search_space(tf: str) -> list[dict]:
    """
    Build all parameter combinations to try for a given timeframe.
    Prioritise fast-trading combos for intraday, slower for higher TFs.
    """
    if tf == "15min":
        fast_range  = [5, 8, 10, 12, 15]
        slow_range  = [20, 26, 30, 40]
        sl_range    = [1.0, 1.5, 2.0]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 4.0]
        session     = [True]
        sess_params = [(7, 18)]
        max_td      = [3, 5]
        long_only   = [True, False]
        avoid_mon   = [True, False]
        avoid_fri   = [True, False]
        rsi_f       = [False, True]
        cmf_f       = [False, True]

    elif tf == "30min":
        fast_range  = [8, 10, 12, 15, 20]
        slow_range  = [20, 26, 30, 40, 50]
        sl_range    = [1.0, 1.5, 2.0]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 4.0]
        session     = [True, False]
        sess_params = [(7, 18)]
        max_td      = [3, 5]
        long_only   = [True, False]
        avoid_mon   = [True, False]
        avoid_fri   = [True, False]
        rsi_f       = [False, True]
        cmf_f       = [False]

    elif tf == "1h":
        fast_range  = [5, 8, 10, 12, 15, 20]
        slow_range  = [15, 20, 26, 30, 40, 50]
        sl_range    = [1.0, 1.5, 2.0]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 4.0]
        session     = [True, False]
        sess_params = [(7, 18)]
        max_td      = [3, 5]
        long_only   = [True, False]
        avoid_mon   = [False]
        avoid_fri   = [False]
        rsi_f       = [False, True]
        cmf_f       = [False]

    elif tf in ("2h", "3h"):
        fast_range  = [5, 8, 10, 12, 15, 20]
        slow_range  = [15, 20, 26, 30, 40, 50]
        sl_range    = [1.0, 1.5, 2.0, 2.5]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 4.0, 5.0]
        session     = [False]
        sess_params = [(0, 24)]
        max_td      = [2, 3]
        long_only   = [True, False]
        avoid_mon   = [False]
        avoid_fri   = [False]
        rsi_f       = [False, True]
        cmf_f       = [False]

    elif tf == "4h":
        fast_range  = [5, 8, 10, 12, 15, 20]
        slow_range  = [15, 20, 26, 30, 40, 50]
        sl_range    = [1.5, 2.0, 2.5]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 4.0, 5.0]
        session     = [False]
        sess_params = [(0, 24)]
        max_td      = [2, 3]
        long_only   = [True, False]
        avoid_mon   = [False]
        avoid_fri   = [False]
        rsi_f       = [False, True]
        cmf_f       = [False]

    else:  # 1D
        fast_range  = [5, 8, 10, 12, 15, 20]
        slow_range  = [20, 26, 30, 40, 50]
        sl_range    = [1.5, 2.0, 2.5]
        tp1_range   = [1.0, 1.5]
        tp2_range   = [2.0, 3.0, 5.0, 7.0]
        session     = [False]
        sess_params = [(0, 24)]
        max_td      = [1, 2]
        long_only   = [True, False]
        avoid_mon   = [False]
        avoid_fri   = [False]
        rsi_f       = [False]
        cmf_f       = [False]

    combos = []
    for fast, slow, slm, tp1, tp2, use_s, lo, am, af, rsi_flt, cmf_flt, mtd in itertools.product(
        fast_range, slow_range, sl_range, tp1_range, tp2_range,
        session, long_only, avoid_mon, avoid_fri, rsi_f, cmf_f, max_td
    ):
        if fast >= slow:
            continue

        sp = sess_params[0]
        combos.append({
            "ema_fast": fast, "ema_slow": slow,
            "sl_mult": slm, "tp1_ratio": tp1, "tp2_ratio": tp2,
            "risk_pct": 0.005, "daily_limit": 0.015,
            "use_session": use_s, "sess_start": sp[0], "sess_end": sp[1],
            "max_trades_day": mtd,
            "long_only": lo, "macro_filter": True,
            "avoid_monday": am, "avoid_friday": af,
            "rsi_filter": rsi_flt, "cmf_filter": cmf_flt,
            "adr_cap": 0.80,
        })

    return combos


# ─────────────────────────────────────────────────────────────────────────────
# PER-TIMEFRAME OPTIMIZER
# ─────────────────────────────────────────────────────────────────────────────

def optimize_tf(df_m15: pd.DataFrame, tf: str,
                max_trials: int = 2000,
                verbose: bool = False) -> tuple[dict, dict]:
    """
    Run grid search over parameter space for one timeframe.
    Returns (best_params, best_metrics).
    """
    rule   = RESAMPLE_RULES[tf]
    df_tf  = resample_ohlcv(df_m15, rule)

    combos = build_search_space(tf)
    # Shuffle to get diverse early results, then cap
    import random; random.shuffle(combos)
    combos = combos[:max_trials]

    best_score   = -999.0
    best_params  = {}
    best_metrics = {}
    passed_count = 0

    for idx, p in enumerate(combos):
        try:
            df_ind = add_indicators(df_tf, p)
            sig    = generate_signals(df_ind, p)
            trades, eq = run_backtest(df_ind, sig, p)
            m = compute_metrics(trades, eq)
        except Exception:
            continue

        if m["score"] > best_score:
            best_score   = m["score"]
            best_params  = p
            best_metrics = m

        if m["passed"]:
            passed_count += 1

        if verbose and idx % 200 == 0 and idx > 0:
            print(f"    {tf} [{idx}/{len(combos)}] best so far: "
                  f"{best_metrics.get('monthly', 0):.2f}%/mes  "
                  f"DD={best_metrics.get('dd', 0):.2f}%  "
                  f"tpm={best_metrics.get('tpm', 0):.1f}  "
                  f"passed={passed_count}")

    return best_params, best_metrics


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    data_path = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
    if not data_path.exists():
        raise FileNotFoundError(f"No encontrado: {data_path}")

    print(f"📂 Cargando {data_path}")
    df_m15 = pd.read_parquet(data_path)
    df_m15.index = pd.to_datetime(df_m15.index)
    df_m15.columns = [c.lower() for c in df_m15.columns]
    if "volume" not in df_m15.columns:
        df_m15["volume"] = 1.0

    print(f"   {len(df_m15):,} barras  |  "
          f"{df_m15.index[0].date()} → {df_m15.index[-1].date()}\n")

    TIMEFRAMES = ["15min", "30min", "1h", "2h", "3h", "4h", "1D"]
    all_results = []
    all_params  = {}

    print("=" * 110)
    print(f"{'ITERATIVE OPTIMIZER — XAUUSD 2016-2026':^110}")
    print(f"{'Objetivos: ≥2%/mes | DD≤7% | ≥7 trd/mes | peor_día≥-3%':^110}")
    print("=" * 110)
    print(f"{'TF':<8} {'Mensual':>8} {'DD':>8} {'Sharpe':>8} "
          f"{'Trd/Mes':>8} {'WR':>7} {'PeorDía':>9} {'Trades':>8} {'✓?':>4}  "
          f"{'ema_f/s':>10}  {'sl':>5}  {'tp1':>5}  {'tp2':>5}  {'lo':>5}")
    print("-" * 110)

    for tf in TIMEFRAMES:
        print(f"  🔍 Optimizando {tf}...", end="", flush=True)
        bp, bm = optimize_tf(df_m15, tf, max_trials=2000, verbose=False)
        print(f"\r", end="")

        passed = "✅" if bm.get("passed") else "✗ "
        fa = bp.get("ema_fast", "?"); sl = bp.get("ema_slow", "?")
        print(
            f"{tf:<8} {bm.get('monthly', 0):>7.2f}%  {bm.get('dd', 0):>7.2f}%  "
            f"{bm.get('sharpe', 0):>7.3f}  {bm.get('tpm', 0):>7.1f}  "
            f"{bm.get('wr', 0):>6.1f}%  {bm.get('worst_day', 0):>8.2f}%  "
            f"{bm.get('n', 0):>7}  {passed}  "
            f"{fa}/{sl:>3}  {bp.get('sl_mult', '?'):>5}  "
            f"{bp.get('tp1_ratio', '?'):>5}  {bp.get('tp2_ratio', '?'):>5}  "
            f"{'Y' if bp.get('long_only') else 'N':>5}"
        )

        row = {
            "Timeframe": tf,
            "Monthly %": bm.get("monthly", 0),
            "Total %": bm.get("total", 0),
            "MaxDD %": bm.get("dd", 0),
            "Sharpe": bm.get("sharpe", 0),
            "Trades/Mes": bm.get("tpm", 0),
            "Win Rate %": bm.get("wr", 0),
            "Worst Day %": bm.get("worst_day", 0),
            "N Trades": bm.get("n", 0),
            "Passed": "✅" if bm.get("passed") else "✗",
            "EMA fast": bp.get("ema_fast"),
            "EMA slow": bp.get("ema_slow"),
            "SL mult": bp.get("sl_mult"),
            "TP1 ratio": bp.get("tp1_ratio"),
            "TP2 ratio": bp.get("tp2_ratio"),
            "Long only": bp.get("long_only"),
            "Session": bp.get("use_session"),
            "Avoid Mon": bp.get("avoid_monday"),
            "Avoid Fri": bp.get("avoid_friday"),
            "RSI filter": bp.get("rsi_filter"),
            "Max trades/day": bp.get("max_trades_day"),
        }
        all_results.append(row)
        all_params[tf] = bp

    print("=" * 110)

    # ── Save ───────────────────────────────────────────────────────
    out_dir = Path("results")
    out_dir.mkdir(exist_ok=True)

    csv_path = out_dir / "iterative_optimizer_results.csv"
    pd.DataFrame(all_results).to_csv(csv_path, index=False)
    print(f"\n💾 CSV: {csv_path}")

    json_path = out_dir / "iterative_optimizer_params.json"
    with open(json_path, "w") as f:
        json.dump(all_params, f, indent=2, default=str)
    print(f"💾 Params JSON: {json_path}")

    passed = sum(1 for r in all_results if r["Passed"] == "✅")
    print(f"\n📊 {passed}/{len(all_results)} timeframes cumplen objetivos")

    near = [r for r in all_results
            if r["Monthly %"] >= 1.5 and r["MaxDD %"] >= -9]
    print(f"   {len(near)} timeframes MUY CERCA (≥1.5% mensual, DD≤9%)")


if __name__ == "__main__":
    main()
