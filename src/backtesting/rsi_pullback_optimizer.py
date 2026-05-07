#!/usr/bin/env python3
"""
RSI Pullback Optimizer — Time-Exit Backtest
============================================
Signal: RSI crosses UP through threshold in EMA200 uptrend (long bias)
        OR RSI crosses DOWN through (100-threshold) in downtrend (short, optional)

Key insight from direct_wr analysis:
  M15 RSI_cross_40: WR=51.5% at 32-bar hold with 1.5R target
  → EV with 2:1 TP = 0.515×2 - 0.485×1 = +0.545R per trade
  → 20 T/M × 0.545R × 0.3% = 3.27%/month ✅

Backtest engine: Numba JIT with time-based exit
Grid search: rsi_thresh, slm, tp_r, max_hold, rp, session filters

Objectives: ≥2%/mes | DD≤7% | ≥7T/mes | peor_día≥-3%
"""

import itertools, json, random, time, warnings
from pathlib import Path

import numba
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MONTHS  = 123.6  # 10.3 years × 12
OBJ_M   = 2.0; OBJ_DD = -7.0; OBJ_TPM = 7.0; OBJ_WD = -3.0
INITIAL = 100_000.0


# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def _ema(s, n): return s.ewm(span=n, adjust=False).mean()

def _rsi(cl, n=14):
    d  = cl.diff()
    au = d.clip(lower=0).ewm(span=n, adjust=False).mean()
    ad = (-d).clip(lower=0).ewm(span=n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))

def _atr(df, n=14):
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"]  - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()

def _stoch_k(df, k=14, d=3):
    lo_k = df["low"].rolling(k).min()
    hi_k = df["high"].rolling(k).max()
    sk   = (df["close"] - lo_k) / (hi_k - lo_k + 1e-12) * 100
    sd   = sk.rolling(d).mean()
    return sk, sd

def _williams_r(df, n=14):
    hi_n = df["high"].rolling(n).max()
    lo_n = df["low"].rolling(n).min()
    return -100 * (hi_n - df["close"]) / (hi_n - lo_n + 1e-12)

def precompute(df_m15, rule):
    """Resample M15 data and compute all needed arrays."""
    if rule is None:
        d = df_m15.copy()
    else:
        agg = {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        d   = df_m15.resample(rule).agg(agg).dropna(subset=["close"])

    cl = d["close"]
    atr14 = _atr(d, 14)

    # Day ADR (fast: resample to 1D → reindex)
    d1       = d[["high","low"]].resample("1D").agg({"high":"max","low":"min"}).dropna()
    d1["adr"] = (d1["high"] - d1["low"]).rolling(14).mean()
    adr_arr  = d1["adr"].reindex(d.index, method="ffill").fillna(10.0).to_numpy(float)

    # Day range (cummax - cummin from daily open)
    dates     = d.index.floor("D")
    day_range = (d["high"].groupby(dates).cummax()
                 - d["low"].groupby(dates).cummin()).to_numpy(float)

    # Factorised day index for per-day counters in Numba
    day_idx   = pd.factorize(d.index.normalize())[0].astype(np.int32)

    return {
        "n":        len(d),
        "op":       d["open"].values,
        "hi":       d["high"].values,
        "lo":       d["low"].values,
        "cl":       cl.values,
        "atr14":    atr14.values,
        "ema20":    _ema(cl, 20).values,
        "ema50":    _ema(cl, 50).values,
        "ema200":   _ema(cl, 200).values,
        "rsi14":    _rsi(cl, 14).values,
        "rsi7":     _rsi(cl, 7).values,
        "stoch_k":  _stoch_k(d, 14, 3)[0].values,
        "stoch_d":  _stoch_k(d, 14, 3)[1].values,
        "willr":    _williams_r(d, 14).values,
        "hour":     d.index.hour.values.astype(np.int32),
        "wday":     d.index.dayofweek.values.astype(np.int32),
        "day_idx":  day_idx,
        "day_range": day_range,
        "adr":      adr_arr,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL GENERATION — vectorized
# ─────────────────────────────────────────────────────────────────────────────

def make_signals(cache, p):
    """
    Generate long/short signals using RSI pullback pattern.
    Signal types:
      "rsi_cross"   : RSI crosses up through rsi_lo (cross up = bull pullback recovery)
      "rsi_double"  : RSI < rsi_lo on bar-2, bar-1 AND then cross upward
      "stoch_cross" : Stoch %K crosses up through 20 (OS)
      "willr_cross" : Williams %R crosses up through -80
      "dual_conf"   : RSI cross + stochastic confirming
    """
    n       = cache["n"]
    cl      = cache["cl"]
    em200   = cache["ema200"]
    em50    = cache["ema50"]
    em20    = cache["ema20"]
    rsi     = cache[p.get("rsi_col", "rsi14")]
    sk      = cache["stoch_k"]
    sd_     = cache["stoch_d"]
    wr      = cache["willr"]
    hrs     = cache["hour"]
    wds     = cache["wday"]
    drng    = cache["day_range"]
    adr     = cache["adr"]

    rsi_lo   = p.get("rsi_lo",  40.0)
    rsi_hi   = p.get("rsi_hi",  60.0)   # for shorts
    lo_only  = p.get("lo_only", True)
    use_sess = p.get("use_sess", False)
    sh, se   = p.get("sh", 7), p.get("se", 18)
    av_m     = p.get("avoid_m", False)
    adr_cap  = p.get("adr_cap", 0.85)
    sig_type = p.get("sig_type", "rsi_cross")
    trend_f  = p.get("trend_filter", "ema200")   # "ema200","ema50","none"

    WU = 250  # warmup bars

    # ── Trend filter ──────────────────────────────────────────────
    if trend_f == "ema200":
        bull = cl > em200
        bear = cl < em200
    elif trend_f == "ema50":
        bull = cl > em50
        bear = cl < em50
    else:
        bull = np.ones(n, dtype=bool)
        bear = np.ones(n, dtype=bool)

    # ── Oscillator signals ────────────────────────────────────────
    def safe(arr): return np.where(np.isnan(arr), 50.0, arr)
    rsi_s = safe(rsi)
    rsi_prev = np.roll(rsi_s, 1); rsi_prev[0] = 50.0

    if sig_type == "rsi_cross":
        long_raw  = (rsi_s > rsi_lo)  & (rsi_prev <= rsi_lo)
        short_raw = (rsi_s < (100-rsi_lo)) & (rsi_prev >= (100-rsi_lo))

    elif sig_type == "rsi_double":
        # Was below rsi_lo for ≥1 bar then crossed up → confirmed
        rsi_p2 = np.roll(rsi_s, 2); rsi_p2[:2] = 50.0
        long_raw  = (rsi_s > rsi_lo) & (rsi_prev <= rsi_lo) & (rsi_p2 <= rsi_lo)
        short_raw = (rsi_s < (100-rsi_lo)) & (rsi_prev >= (100-rsi_lo)) & (rsi_p2 >= (100-rsi_lo))

    elif sig_type == "stoch_cross":
        sk_s = safe(sk); sk_p = np.roll(sk_s, 1); sk_p[0] = 50.0
        sd_s = safe(sd_)
        long_raw  = (sk_s > 20) & (sk_p <= 20) & (sk_s > sd_s)
        short_raw = (sk_s < 80) & (sk_p >= 80) & (sk_s < sd_s)

    elif sig_type == "willr_cross":
        wr_s = safe(wr); wr_p = np.roll(wr_s, 1); wr_p[0] = -50.0
        long_raw  = (wr_s > -80) & (wr_p <= -80)
        short_raw = (wr_s < -20) & (wr_p >= -20)

    elif sig_type == "dual_conf":
        # RSI cross + stochastic both oversold → higher confidence
        sk_s = safe(sk); sk_p = np.roll(sk_s, 1); sk_p[0] = 50.0
        long_raw  = (rsi_s > rsi_lo) & (rsi_prev <= rsi_lo) & (sk_s < 40)
        short_raw = (rsi_s < (100-rsi_lo)) & (rsi_prev >= (100-rsi_lo)) & (sk_s > 60)

    elif sig_type == "rsi_extreme":
        # RSI < extreme threshold directly (no cross)
        long_raw  = rsi_s < rsi_lo
        short_raw = rsi_s > (100-rsi_lo)

    elif sig_type == "rsi_cross_ema":
        # RSI cross AND EMA20 above EMA50 (strong trend)
        ema_bull = (em20 > em50)
        ema_bear = (em20 < em50)
        long_raw  = (rsi_s > rsi_lo) & (rsi_prev <= rsi_lo) & ema_bull
        short_raw = (rsi_s < (100-rsi_lo)) & (rsi_prev >= (100-rsi_lo)) & ema_bear
    else:
        long_raw  = np.zeros(n, dtype=bool)
        short_raw = np.zeros(n, dtype=bool)

    # ── Apply trend filter ────────────────────────────────────────
    long_sig  = long_raw  & bull
    short_sig = short_raw & bear if not lo_only else np.zeros(n, dtype=bool)

    # ── Session filter ────────────────────────────────────────────
    valid = np.ones(n, dtype=bool)
    valid[:WU] = False; valid[-5:] = False
    if av_m: valid &= (wds != 0)
    valid &= (wds < 5)   # no weekend
    if use_sess: valid &= (hrs >= sh) & (hrs < se)

    # ── ADR cap ──────────────────────────────────────────────────
    with np.errstate(invalid="ignore", divide="ignore"):
        adr_ratio = np.where(adr > 0, drng / adr, 0)
    valid &= (adr_ratio <= adr_cap)

    # ── Final signal ──────────────────────────────────────────────
    sig = np.zeros(n, dtype=np.int8)
    sig[valid & long_sig]  = 1
    sig[valid & short_sig] = -1
    return sig


# ─────────────────────────────────────────────────────────────────────────────
# NUMBA BACKTEST WITH TIME-BASED EXIT
# ─────────────────────────────────────────────────────────────────────────────

@numba.njit(cache=True)
def _bt(op, hi, lo, at, sig, rp, dl, slm, tp_r, mtd, max_hold, day_idx):
    """
    Backtest with:
    - ATR-based SL and TP (single TP)
    - Time-based exit after max_hold bars (close at open of exit bar)
    - Daily loss limit and max trades per day
    """
    n   = len(op)
    eq  = np.empty(n); eq[0] = INITIAL = 100_000.0; cap = INITIAL
    nd  = day_idx[-1] + 2
    dpnl = np.zeros(nd)
    dcnt = np.zeros(nd, dtype=numba.int32)
    pos  = 0; ep = sl = tp = ru = 0.0; entry_bar = 0
    buf  = np.zeros(50000); nt = 0

    for i in range(1, n):
        d = day_idx[i]

        # ── Manage open position ──────────────────────────────
        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            held = i - entry_bar

            # Time exit: close at this bar's open
            if held >= max_hold:
                if pos == 1:
                    pnl = (bo - ep) / (ep - sl + 1e-12) * ru
                else:
                    pnl = (ep - bo) / (sl - ep + 1e-12) * ru
                pnl = min(max(pnl, -ru), ru * tp_r * 2)  # clamp
                cap += pnl; dpnl[d] += pnl
                if nt < 50000: buf[nt] = pnl; nt += 1
                pos = 0; eq[i] = cap; continue

            if pos == 1:   # long
                if bo <= sl or bl <= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 50000: buf[nt] = -ru; nt += 1
                    pos = 0; eq[i] = cap; continue
                if bo >= tp or bh >= tp:
                    win = ru * tp_r
                    cap += win; dpnl[d] += win
                    if nt < 50000: buf[nt] = win; nt += 1
                    pos = 0; eq[i] = cap; continue

            else:           # short
                if bo >= sl or bh >= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 50000: buf[nt] = -ru; nt += 1
                    pos = 0; eq[i] = cap; continue
                if bo <= tp or bl <= tp:
                    win = ru * tp_r
                    cap += win; dpnl[d] += win
                    if nt < 50000: buf[nt] = win; nt += 1
                    pos = 0; eq[i] = cap; continue

        # ── Open new position ─────────────────────────────────
        if pos == 0 and sig[i-1] != 0:
            if dpnl[d] / (cap + 1e-12) <= -dl: eq[i] = cap; continue
            if dcnt[d] >= mtd:                  eq[i] = cap; continue
            ati = at[i]
            if ati <= 0.0 or ati != ati:        eq[i] = cap; continue  # nan check

            ep  = op[i]; sd = slm * ati; ru = rp * cap; entry_bar = i
            if sig[i-1] == 1:
                sl = ep - sd; tp = ep + sd * tp_r; pos = 1
            else:
                sl = ep + sd; tp = ep - sd * tp_r; pos = -1
            dcnt[d] += 1

        eq[i] = cap

    return eq, buf[:nt], nt


@numba.njit(cache=True)
def _bt_adaptive(op, hi, lo, at, sig, rp, dl, slm, tp_r, mtd, max_hold, day_idx,
                 dd_half=0.03, dd_quarter=0.06, max_cl=5, cl_pause=2):
    """
    Enhanced backtest with:
    - Adaptive position sizing: reduce rp when in drawdown
      * dd < dd_half:    rp_eff = rp (full)
      * dd_half <= dd < dd_quarter: rp_eff = rp * 0.5
      * dd >= dd_quarter: rp_eff = rp * 0.25
    - Consecutive loss circuit breaker: pause max_cl trades after cl_pause losses
    """
    n   = len(op)
    eq  = np.empty(n); eq[0] = INITIAL = 100_000.0; cap = INITIAL
    peak_eq = INITIAL
    nd  = day_idx[-1] + 2
    dpnl = np.zeros(nd)
    dcnt = np.zeros(nd, dtype=numba.int32)
    pos  = 0; ep = sl = tp = ru = 0.0; entry_bar = 0
    buf  = np.zeros(50000); nt = 0
    consec_losses = 0; skip_count = 0

    for i in range(1, n):
        d = day_idx[i]

        # Update peak equity
        if cap > peak_eq:
            peak_eq = cap

        # ── Manage open position ──────────────────────────────
        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            held = i - entry_bar

            if held >= max_hold:
                if pos == 1:
                    pnl = (bo - ep) / (ep - sl + 1e-12) * ru
                else:
                    pnl = (ep - bo) / (sl - ep + 1e-12) * ru
                pnl = min(max(pnl, -ru), ru * tp_r * 2)
                cap += pnl; dpnl[d] += pnl
                if nt < 50000: buf[nt] = pnl; nt += 1
                if pnl < 0: consec_losses += 1
                else: consec_losses = 0
                pos = 0; eq[i] = cap; continue

            if pos == 1:
                if bo <= sl or bl <= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 50000: buf[nt] = -ru; nt += 1
                    consec_losses += 1
                    pos = 0; eq[i] = cap; continue
                if bo >= tp or bh >= tp:
                    win = ru * tp_r
                    cap += win; dpnl[d] += win
                    if nt < 50000: buf[nt] = win; nt += 1
                    consec_losses = 0
                    pos = 0; eq[i] = cap; continue
            else:
                if bo >= sl or bh >= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 50000: buf[nt] = -ru; nt += 1
                    consec_losses += 1
                    pos = 0; eq[i] = cap; continue
                if bo <= tp or bl <= tp:
                    win = ru * tp_r
                    cap += win; dpnl[d] += win
                    if nt < 50000: buf[nt] = win; nt += 1
                    consec_losses = 0
                    pos = 0; eq[i] = cap; continue

        # ── Open new position ─────────────────────────────────
        if pos == 0 and sig[i-1] != 0:
            if dpnl[d] / (cap + 1e-12) <= -dl: eq[i] = cap; continue
            if dcnt[d] >= mtd:                  eq[i] = cap; continue
            ati = at[i]
            if ati <= 0.0 or ati != ati:        eq[i] = cap; continue

            # Circuit breaker: skip after too many consecutive losses
            if consec_losses >= max_cl:
                if skip_count < cl_pause:
                    skip_count += 1
                    eq[i] = cap; continue
                else:
                    skip_count = 0; consec_losses = 0  # reset

            # Adaptive position sizing based on drawdown
            dd_frac = (peak_eq - cap) / (peak_eq + 1e-12)
            if dd_frac < dd_half:
                rp_eff = rp
            elif dd_frac < dd_quarter:
                rp_eff = rp * 0.5
            else:
                rp_eff = rp * 0.25

            ep  = op[i]; sd = slm * ati; ru = rp_eff * cap; entry_bar = i
            if sig[i-1] == 1:
                sl = ep - sd; tp = ep + sd * tp_r; pos = 1
            else:
                sl = ep + sd; tp = ep - sd * tp_r; pos = -1
            dcnt[d] += 1

        eq[i] = cap

    return eq, buf[:nt], nt


@numba.njit(cache=True)
def _bt_trail(op, hi, lo, at, sig, rp, dl, slm, mtd, max_hold, day_idx,
              trail_start=1.0, trail_dist=1.5):
    """
    Backtest with TRAILING ATR STOP (no fixed TP).
    - Initial SL: slm × ATR
    - When price moves trail_start × ATR in favor: SL moves to breakeven
    - Then trail_dist × ATR behind peak price (only moves forward, never back)
    - Backstop time exit at max_hold bars
    """
    n   = len(op)
    eq  = np.empty(n); eq[0] = INITIAL = 100_000.0; cap = INITIAL
    nd  = day_idx[-1] + 2
    dpnl = np.zeros(nd)
    dcnt = np.zeros(nd, dtype=numba.int32)
    pos  = 0; ep = sl = ru = peak_p = 0.0; entry_bar = 0; init_sl = 0.0
    buf  = np.zeros(50000); nt = 0

    for i in range(1, n):
        d = day_idx[i]

        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            held = i - entry_bar

            if pos == 1:  # long
                # Update peak and trail SL
                if bh > peak_p:
                    peak_p = bh
                # Compute new_sl based on trail
                sl_dist = slm * at[entry_bar]  # use ATR at entry for trail calc
                favorable = peak_p - ep
                if favorable >= trail_start * sl_dist:
                    # Trail at trail_dist × ATR behind peak
                    new_sl = peak_p - trail_dist * sl_dist
                    if new_sl > sl:  # only move forward
                        sl = new_sl

                # Time exit
                if held >= max_hold:
                    pnl = (bo - ep) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue

                # Stop hit: check open first then bar low
                if bo <= sl:
                    pnl = (bo - ep) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue
                if bl <= sl:
                    pnl = (sl - ep) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue

            else:  # short
                if bl < peak_p:
                    peak_p = bl
                sl_dist = slm * at[entry_bar]
                favorable = ep - peak_p
                if favorable >= trail_start * sl_dist:
                    new_sl = peak_p + trail_dist * sl_dist
                    if new_sl < sl:
                        sl = new_sl

                if held >= max_hold:
                    pnl = (ep - bo) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue

                if bo >= sl:
                    pnl = (ep - bo) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue
                if bh >= sl:
                    pnl = (ep - sl) / (init_sl + 1e-12) * ru
                    pnl = min(max(pnl, -ru), ru * 10.0)
                    cap += pnl; dpnl[d] += pnl
                    if nt < 50000: buf[nt] = pnl; nt += 1
                    pos = 0; eq[i] = cap; continue

        # ── Open new position ─────────────────────────────────
        if pos == 0 and sig[i-1] != 0:
            if dpnl[d] / (cap + 1e-12) <= -dl: eq[i] = cap; continue
            if dcnt[d] >= mtd:                  eq[i] = cap; continue
            ati = at[i]
            if ati <= 0.0 or ati != ati:        eq[i] = cap; continue

            ep = op[i]; init_sl = slm * ati; ru = rp * cap; entry_bar = i
            if sig[i-1] == 1:
                sl = ep - init_sl; peak_p = ep; pos = 1
            else:
                sl = ep + init_sl; peak_p = ep; pos = -1
            dcnt[d] += 1

        eq[i] = cap

    return eq, buf[:nt], nt


def run_bt(cache, sig, p):
    eq, raw_pnl, _ = _bt(
        cache["op"], cache["hi"], cache["lo"], cache["atr14"],
        sig.astype(np.int8),
        float(p["rp"]), float(p["dl"]),
        float(p["slm"]), float(p["tp_r"]),
        int(p["mtd"]), int(p["max_hold"]),
        cache["day_idx"],
    )
    return raw_pnl, eq


def mets(pnl, eq):
    n = len(pnl)
    if n == 0:
        return dict(m=0,dd=0,tpm=0,wd=0,wr=0,sh=0,passed=False,score=-999,n=0)
    fin     = eq[-1]
    monthly = ((fin / 100_000.0) ** (1.0 / MONTHS) - 1.0) * 100.0
    tpm     = n / MONTHS
    rm      = np.maximum.accumulate(eq)
    max_dd  = float(((eq - rm) / rm * 100.0).min())
    wins    = int(np.sum(pnl > 0))
    wr      = wins / n * 100.0
    dr      = np.diff(eq) / eq[:-1]
    wd      = float(dr.min()) * 100.0 if len(dr) else 0.0
    sh      = float(dr.mean() / (dr.std() + 1e-12) * (252**0.5))
    passed  = (monthly >= OBJ_M and max_dd >= OBJ_DD
               and tpm >= OBJ_TPM and wd >= OBJ_WD)
    score   = (monthly * 2.0
               + max(0.0, max_dd - OBJ_DD) * 0.3
               + min(tpm, 60.0) * 0.05
               + sh * 0.4
               + (30.0 if passed else 0.0))
    return dict(m=round(monthly,3), dd=round(max_dd,2), tpm=round(tpm,1),
                wd=round(wd,2), wr=round(wr,1), sh=round(sh,3),
                passed=bool(passed), score=round(score,3), n=n)


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH SPACES
# ─────────────────────────────────────────────────────────────────────────────

# For each TF, max_hold is in BARS of that TF
# M15: 32 bars = 8h | 1H: 16 bars = 16h | 4H: 8 bars = 32h | 1D: 5 bars = 1wk
TF_SEARCH = {
    "15min": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross","dual_conf"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [30, 35, 40, 45],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [True, False],
        sh         = [7], se=[18],
        avoid_m    = [False],
        adr_cap    = [0.80, 0.90],
        slm        = [1.2, 1.5, 2.0, 2.5],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0],
        max_hold   = [16, 24, 32, 48, 64],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [3, 5, 8],
    ),
    "30min": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [30, 35, 40, 45],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [True, False],
        sh=[7], se=[18],
        avoid_m    = [False],
        adr_cap    = [0.80, 0.90],
        slm        = [1.2, 1.5, 2.0, 2.5],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0],
        max_hold   = [12, 16, 24, 32, 48],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [3, 5],
    ),
    "1h": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross","willr_cross"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [30, 35, 40, 45],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [True, False],
        sh=[7], se=[20],
        avoid_m    = [False],
        adr_cap    = [0.90],
        slm        = [1.2, 1.5, 2.0, 2.5, 3.0],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
        max_hold   = [8, 12, 16, 24, 32],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [2, 3, 5],
    ),
    "2h": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross","willr_cross"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [25, 30, 35, 40],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [False],
        sh=[0], se=[24],
        avoid_m    = [False],
        adr_cap    = [0.90],
        slm        = [1.5, 2.0, 2.5, 3.0],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
        max_hold   = [6, 8, 12, 16, 24],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [2, 3],
    ),
    "3h": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross","willr_cross"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [25, 30, 35, 40],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [False],
        sh=[0], se=[24],
        avoid_m    = [False],
        adr_cap    = [0.90],
        slm        = [1.5, 2.0, 2.5, 3.0],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
        max_hold   = [5, 8, 10, 12, 16],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [2, 3],
    ),
    "4h": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","stoch_cross","willr_cross"],
        rsi_col    = ["rsi14","rsi7"],
        rsi_lo     = [25, 30, 35, 40],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [False],
        sh=[0], se=[24],
        avoid_m    = [False],
        adr_cap    = [0.90],
        slm        = [1.5, 2.0, 2.5, 3.0, 4.0],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0],
        max_hold   = [4, 6, 8, 10, 12],
        rp         = [0.003, 0.005, 0.008],
        dl         = [0.015, 0.020],
        mtd        = [1, 2, 3],
    ),
    "1D": dict(
        sig_type   = ["rsi_cross","rsi_double","rsi_cross_ema","willr_cross"],
        rsi_col    = ["rsi14"],
        rsi_lo     = [25, 30, 35, 40, 45],
        trend_filter=["ema200","ema50"],
        lo_only    = [True, False],
        use_sess   = [False],
        sh=[0], se=[24],
        avoid_m    = [False],
        adr_cap    = [1.00],
        slm        = [1.5, 2.0, 2.5, 3.0],
        tp_r       = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0],
        max_hold   = [3, 5, 7, 10, 15],
        rp         = [0.005, 0.008, 0.010, 0.012],
        dl         = [0.015, 0.020, 0.025],
        mtd        = [1, 2, 3],
    ),
}


def build_combos(tf, max_n=3000):
    pp   = TF_SEARCH[tf]
    keys = list(pp.keys())
    combos = []
    for vals in itertools.product(*[pp[k] for k in keys]):
        d = dict(zip(keys, vals))
        combos.append(d)
    random.shuffle(combos)
    return combos[:max_n]


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZE
# ─────────────────────────────────────────────────────────────────────────────

def optimize_tf(cache, tf, max_n=3000, verbose=False):
    combos     = build_combos(tf, max_n)
    best_score = -999.0; best_p = {}; best_m = {}; passed = 0

    # Warmup Numba JIT
    dummy = np.zeros(min(cache["n"], 600), dtype=np.int8); dummy[300] = 1
    _bt(cache["op"][:600], cache["hi"][:600], cache["lo"][:600],
        cache["atr14"][:600], dummy, 0.005, 0.02, 1.5, 2.0, 3, 32,
        cache["day_idx"][:600])

    for idx, p in enumerate(combos):
        bt_p = {"rp": p["rp"], "dl": p["dl"], "slm": p["slm"],
                "tp_r": p["tp_r"], "mtd": p["mtd"], "max_hold": p["max_hold"]}
        try:
            sig     = make_signals(cache, p)
            pnl, eq = run_bt(cache, sig, bt_p)
            m       = mets(pnl, eq)
        except Exception:
            continue

        if m["score"] > best_score:
            best_score = m["score"]; best_p = {**p}; best_m = m
        if m["passed"]:
            passed += 1
            if verbose:
                pp = (f'sc={m["score"]:.1f} M={m["m"]:.2f}% DD={m["dd"]:.2f}% '
                      f'WR={m["wr"]:.1f}% T/M={m["tpm"]:.1f} '
                      f'sig={p["sig_type"]} rsi_lo={p["rsi_lo"]} '
                      f'slm={p["slm"]} tp={p["tp_r"]} hold={p["max_hold"]} rp={p["rp"]}')
                print(f"    ✅ {pp}")

    return best_p, best_m, passed


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    path = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
    print(f"Loading {path} …")
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if "volume" not in df.columns or (df["volume"] == 0).mean() > 0.5:
        df["volume"] = 1.0
    print(f"  {len(df):,} M15 bars | {df.index[0].date()} → {df.index[-1].date()}\n")

    TFS = ["15min","30min","1h","2h","3h","4h","1D"]
    RULES = {"15min":None,"30min":"30min","1h":"1h","2h":"2h","3h":"3h","4h":"4h","1D":"1D"}

    W = 120
    print("=" * W)
    print(f"{'RSI PULLBACK TIME-EXIT OPTIMIZER — XAUUSD 2016-2026':^{W}}")
    print(f"{'Objetivos: ≥2%/mes | DD≤7% | ≥7T/mes | peorDía≥-3%':^{W}}")
    print("=" * W)
    print(f"{'TF':<7} {'Mon%':>7} {'DD%':>7} {'Shr':>6} {'T/M':>6} "
          f"{'WR':>6} {'WDay':>7} {'N':>6} {'✓':>3}  best_params")
    print("-" * W)

    all_res = []; all_params = {}

    for tf in TFS:
        rule = RULES[tf]
        t0   = time.time()
        print(f"  ⏳ {tf} precomputing …", end="", flush=True)
        cache = precompute(df, rule)
        print(f" {cache['n']:,} bars → optimizing …", end="", flush=True)

        bp, bm, pc = optimize_tf(cache, tf, max_n=5000)
        elapsed = time.time() - t0

        ok = "✅" if bm.get("passed") else "✗ "
        pp = (f"sig={bp.get('sig_type','?')} rsi_lo={bp.get('rsi_lo','?')} "
              f"slm={bp.get('slm','?')} tp={bp.get('tp_r','?')} "
              f"hold={bp.get('max_hold','?')} rp={bp.get('rp','?')} "
              f"trend={bp.get('trend_filter','?')} lo={bp.get('lo_only','?')}")
        print(f"\r{tf:<7} {bm.get('m',0):>7.2f} {bm.get('dd',0):>7.2f} "
              f"{bm.get('sh',0):>6.3f} {bm.get('tpm',0):>6.1f} "
              f"{bm.get('wr',0):>6.1f} {bm.get('wd',0):>7.2f} "
              f"{bm.get('n',0):>6} {ok}  {pp}  [{pc}✓ {elapsed:.0f}s]")

        all_res.append({"TF": tf, **bm, "params": bp})
        all_params[tf] = bp

    print("=" * W)
    passed = sum(1 for r in all_res if r.get("passed"))
    print(f"\n✅ {passed}/{len(TFS)} timeframes pasan objetivos\n")

    Path("results").mkdir(exist_ok=True)
    rows = [{"TF": r["TF"], "Monthly%": r["m"], "MaxDD%": r["dd"],
             "Sharpe": r["sh"], "T/Mes": r["tpm"], "WR%": r["wr"],
             "WorstDay%": r["wd"], "N": r["n"],
             "Passed": "YES" if r["passed"] else "NO", **r["params"]}
            for r in all_res]
    pd.DataFrame(rows).to_csv("results/rsi_pullback_optimizer.csv", index=False)
    with open("results/rsi_pullback_params.json", "w") as f:
        json.dump(all_params, f, indent=2, default=str)
    print("💾 results/rsi_pullback_optimizer.csv")
    print("💾 results/rsi_pullback_params.json")


if __name__ == "__main__":
    main()
