#!/usr/bin/env python3
"""
GVF Score Optimizer — Vectorized Gold Volume Fusion over 10.3 años Dukascopy data
==================================================================================
Replica el sistema de scoring GVF (Gold Volume Fusion) V3 en modo
completamente vectorizado (sin loops Python en la generación de señales).

Scoring: OBV, CMF, MFI, ChaikinOsc, VPT, VROC, EMA alignment, VWAP → 0..9 puntos
Backtest: Numba JIT (0.3ms/run)
Grid search: cmf_thr, min_score, sl_mult, tp1, tp2 × 7 timeframes

Objetivos: ≥2%/mes | DD≤7% | ≥7T/mes | peor_día≥-3%
"""

import itertools, json, random, time, warnings
from pathlib import Path

import numba
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MONTHS  = 10.3 * 12   # 123.6
OBJ_M   = 2.0; OBJ_DD = -7.0; OBJ_TPM = 7.0; OBJ_WD = -3.0
INITIAL = 100_000.0
RESAMPLE = {"15min":None,"30min":"30min","1h":"1h","2h":"2h","3h":"3h","4h":"4h","1D":"1D"}


# ─────────────────────────────────────────────────────────────────────────────
# VECTORIZED INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def _ema(s, n): return s.ewm(span=n, adjust=False).mean()
def _rsi_ema(s, n=14):
    d  = s.diff()
    au = d.clip(lower=0).ewm(span=n, adjust=False).mean()
    ad = (-d).clip(lower=0).ewm(span=n, adjust=False).mean()
    return 100 - 100 / (1 + au / ad.replace(0, np.nan))

def _atr(df, n=14):
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()

def _obv(df):
    d   = np.sign(df["close"].diff())
    return (d * df["volume"]).cumsum()

def _cmf(df, n=20):
    hl   = (df["high"] - df["low"]).replace(0, np.nan)
    clv  = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    return (clv * df["volume"]).rolling(n).sum() / df["volume"].rolling(n).sum()

def _mfi(df, n=14):
    tp   = (df["high"] + df["low"] + df["close"]) / 3
    mf   = tp * df["volume"]
    d    = tp.diff()
    ppos = mf.where(d > 0, 0.0).rolling(n).sum()
    pneg = mf.where(d < 0, 0.0).rolling(n).sum().abs()
    return 100 - 100 / (1 + ppos / pneg.replace(0, np.nan))

def _chaikin_osc(df, fast=3, slow=10):
    hl   = (df["high"] - df["low"]).replace(0, np.nan)
    clv  = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    ad   = (clv * df["volume"]).cumsum()
    return _ema(ad, fast) - _ema(ad, slow)

def _vpt(df, n=14):
    vpt  = (df["close"].pct_change() * df["volume"]).cumsum()
    return vpt, _ema(vpt, n)

def _vwap_daily(df):
    """Approximate daily VWAP — reset per calendar date."""
    tp   = (df["high"] + df["low"] + df["close"]) / 3
    tpv  = tp * df["volume"]
    date = df.index.normalize()
    return tpv.groupby(date).cumsum() / df["volume"].groupby(date).cumsum()

def precompute(df_m15, rule):
    if rule is None:
        df = df_m15.copy()
    else:
        agg = {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        df  = df_m15.resample(rule).agg(agg).dropna(subset=["close"])

    vol    = df["volume"] if "volume" in df.columns else pd.Series(np.ones(len(df)), index=df.index)
    df["volume"] = vol

    cl = df["close"]
    obv = _obv(df)
    vpt, vpt_ma = _vpt(df, 14)

    day_idx = pd.factorize(df.index.normalize())[0].astype(np.int32)

    # ADR rolling 14 days — fast: resample to 1D then reindex
    df_d      = df[["high","low"]].resample("1D").agg({"high":"max","low":"min"}).dropna()
    df_d["adr"] = (df_d["high"] - df_d["low"]).rolling(14).mean()
    adr_arr   = df_d["adr"].reindex(df.index, method="ffill").values.astype(float)

    # Day range (cummax/cummin from day open) — fast vectorized
    dates     = df.index.floor("D")
    day_range = (df["high"].groupby(dates).cummax() - df["low"].groupby(dates).cummin()).to_numpy()

    return {
        "n":       len(df),
        "op":      df["open"].values,
        "hi":      df["high"].values,
        "lo":      df["low"].values,
        "cl":      cl.values,
        "atr14":   _atr(df, 14).values,
        "ema20":   _ema(cl, 20).values,
        "ema50":   _ema(cl, 50).values,
        "ema200":  _ema(cl, 200).values,
        "obv":     obv.values,
        "obv_ma":  _ema(obv, 30).values,
        "cmf":     _cmf(df, 20).values,
        "mfi":     _mfi(df, 14).values,
        "chaik":   _chaikin_osc(df, 3, 10).values,
        "vpt":     vpt.values,
        "vpt_ma":  vpt_ma.values,
        "vroc":    df["volume"].pct_change(14).values * 100,
        "vwap":    _vwap_daily(df).values,
        "hour":    df.index.hour.values.astype(np.int32),
        "wday":    df.index.dayofweek.values.astype(np.int32),
        "day_idx": day_idx,
        "day_range": day_range,
        "adr":     adr_arr,
    }


# ─────────────────────────────────────────────────────────────────────────────
# VECTORIZED SCORE + SIGNALS
# ─────────────────────────────────────────────────────────────────────────────

def make_signals(cache, p):
    """
    Compute vectorized GVF score for each bar and emit signal when
    score >= min_score (long) or <= -min_score (short).
    Max possible score: 9 (OBV, VWAP, CMF, MFI, Chaikin, VPT, VROC, EMA_align, EMA200)
    """
    n      = cache["n"]
    cl     = cache["cl"]
    em200  = cache["ema200"]
    em50   = cache["ema50"]
    em20   = cache["ema20"]
    obv    = cache["obv"]
    obvm   = cache["obv_ma"]
    cmf    = cache["cmf"]
    mfi    = cache["mfi"]
    chk    = cache["chaik"]
    vpt    = cache["vpt"]
    vptm   = cache["vpt_ma"]
    vroc   = cache["vroc"]
    vwap   = cache["vwap"]
    hrs    = cache["hour"]
    wds    = cache["wday"]
    drng   = cache["day_range"]
    adr    = cache["adr"]

    cmf_thr  = p.get("cmf_thr", 0.08)
    min_sc   = p.get("min_score", 6)
    lo_only  = p.get("lo_only", False)
    use_sess = p.get("use_sess", False)
    sh, se   = p.get("sh", 7), p.get("se", 18)
    av_m     = p.get("avoid_m", False)
    av_f     = p.get("avoid_f", False)
    adr_cap  = p.get("adr_cap", 0.80)
    mfi_os   = p.get("mfi_os", 30.0)   # oversold threshold
    mfi_ob   = p.get("mfi_ob", 70.0)   # overbought threshold

    WU = 270   # warmup period

    # ── Score components (all vectorized) ─────────────────────────
    # Each component: +1 = bullish, -1 = bearish
    s_obv   = np.where(obv  > obvm, 1, -1)
    s_vwap  = np.where(cl   > vwap, 1, -1)
    s_cmf   = np.where(cmf  > cmf_thr, 1, np.where(cmf < -cmf_thr, -1, 0))
    s_chk   = np.where(chk  > 0, 1, -1)
    s_vpt   = np.where(vpt  > vptm, 1, -1)
    s_vroc  = np.where(vroc > 0, 1, -1)
    # MFI: +1 if oversold, -1 if overbought, else 0
    s_mfi   = np.where(mfi < mfi_os, 1, np.where(mfi > mfi_ob, -1, 0))
    # EMA alignment
    s_ema   = np.where((em20 > em50) & (em50 > em200), 1,
              np.where((em20 < em50) & (em50 < em200), -1, 0))
    # EMA200 macro: extra +1 for longs above, -1 for shorts below
    s_em200 = np.where(cl > em200, 1, -1)

    # Handle NaN
    def safe(arr):
        return np.where(np.isnan(arr), 0, arr)

    score = (safe(s_obv) + safe(s_vwap) + safe(s_cmf) + safe(s_chk)
             + safe(s_vpt) + safe(s_vroc) + safe(s_mfi) + safe(s_ema)
             + safe(s_em200))

    # ── Filters ────────────────────────────────────────────────────
    valid = np.ones(n, dtype=bool)
    valid[:WU] = False; valid[-1] = False

    if av_m: valid &= (wds != 0)
    if av_f: valid &= (wds != 4)
    if use_sess: valid &= (hrs >= sh) & (hrs < se)

    # ADR cap (skip if day already moved > adr_cap * ADR)
    with np.errstate(invalid="ignore", divide="ignore"):
        adr_ratio = np.where(adr > 0, drng / adr, 0)
    valid &= adr_ratio <= adr_cap

    # ── Signal ─────────────────────────────────────────────────────
    sig = np.zeros(n, dtype=np.int8)
    sig[valid & (score >= min_sc)] = 1
    sig[valid & (score <= -min_sc)] = -1

    # Long-only: kill short signals in bull market
    if lo_only:
        sig[(sig == -1) & (cl > em200)] = 0

    return sig


# ─────────────────────────────────────────────────────────────────────────────
# NUMBA BACKTEST
# ─────────────────────────────────────────────────────────────────────────────

@numba.njit(cache=True)
def _bt(op, hi, lo, at, sig, rp, dl, slm, tp1r, tp2r, mtd, day_idx):
    n = len(op); eq = np.empty(n); eq[0] = 100_000.0; cap = 100_000.0
    nd = day_idx[-1] + 2; dpnl = np.zeros(nd); dcnt = np.zeros(nd, dtype=numba.int32)
    pos = 0; ep = sl = tp1 = tp2 = ru = 0.0; td = False
    buf = np.zeros(30000); nt = 0

    for i in range(1, n):
        d = day_idx[i]
        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            if pos == 1:
                if bo <= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 30000: buf[nt] = -ru; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if bl <= sl:
                    pnl = 0.0 if td else -ru
                    cap += pnl; dpnl[d] += pnl
                    if nt < 30000: buf[nt] = pnl; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if not td and bh >= tp1:
                    p1 = ru * tp1r * 0.5
                    cap += p1; dpnl[d] += p1; sl = ep; td = True
                    if bh >= tp2:
                        p2 = ru * tp2r * 0.5
                        cap += p2; dpnl[d] += p2
                        if nt < 30000: buf[nt] = p1 + p2; nt += 1
                        pos = 0; td = False; eq[i] = cap; continue
                if td and bh >= tp2:
                    p2 = ru * tp2r * 0.5
                    cap += p2; dpnl[d] += p2
                    if nt < 30000: buf[nt] = p2; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
            else:
                if bo >= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 30000: buf[nt] = -ru; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if bh >= sl:
                    pnl = 0.0 if td else -ru
                    cap += pnl; dpnl[d] += pnl
                    if nt < 30000: buf[nt] = pnl; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if not td and bl <= tp1:
                    p1 = ru * tp1r * 0.5
                    cap += p1; dpnl[d] += p1; sl = ep; td = True
                    if bl <= tp2:
                        p2 = ru * tp2r * 0.5
                        cap += p2; dpnl[d] += p2
                        if nt < 30000: buf[nt] = p1 + p2; nt += 1
                        pos = 0; td = False; eq[i] = cap; continue
                if td and bl <= tp2:
                    p2 = ru * tp2r * 0.5
                    cap += p2; dpnl[d] += p2
                    if nt < 30000: buf[nt] = p2; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue

        if pos == 0 and sig[i-1] != 0:
            if dpnl[d] / cap <= -dl: eq[i] = cap; continue
            if dcnt[d] >= mtd:       eq[i] = cap; continue
            ati = at[i]
            if ati <= 0.0:           eq[i] = cap; continue
            ep = op[i]; sd = slm * ati; ru = rp * cap
            if sig[i-1] == 1:
                sl = ep - sd; tp1 = ep + sd * tp1r; tp2 = ep + sd * tp2r; pos = 1
            else:
                sl = ep + sd; tp1 = ep - sd * tp1r; tp2 = ep - sd * tp2r; pos = -1
            td = False; dcnt[d] += 1
        eq[i] = cap

    return eq, buf[:nt], nt


def run_bt(cache, sig, p):
    eq, pnl, _ = _bt(
        cache["op"], cache["hi"], cache["lo"], cache["atr14"],
        sig.astype(np.int8),
        p["rp"], p["dl"], p["slm"], p["tp1"], p["tp2"],
        int(p.get("mtd", 5)), cache["day_idx"],
    )
    return pnl, eq


def mets(pnl, eq):
    n = len(pnl)
    if n == 0:
        return {"m":0,"dd":0,"tpm":0,"wd":0,"wr":0,"sh":0,"pass":False,"score":-999,"n":0}
    fin     = eq[-1]
    monthly = ((fin / INITIAL) ** (1/MONTHS) - 1) * 100
    tpm     = n / MONTHS
    rm      = np.maximum.accumulate(eq)
    max_dd  = float(((eq - rm) / rm * 100).min())
    wins    = int(np.sum(pnl > 0))
    wr      = wins / n * 100
    dr      = np.diff(eq) / eq[:-1]
    wd      = float(dr.min()) * 100
    sh      = float(dr.mean() / (dr.std() + 1e-12) * np.sqrt(252))
    passed  = monthly >= OBJ_M and max_dd >= OBJ_DD and tpm >= OBJ_TPM and wd >= OBJ_WD
    score   = monthly*2.0 + max(0, max_dd - OBJ_DD)*0.5 + min(tpm,50)*0.05 + sh*0.5 + (20 if passed else 0)
    return {"m":round(monthly,3),"dd":round(max_dd,2),"tpm":round(tpm,1),
            "wd":round(wd,2),"wr":round(wr,1),"sh":round(sh,3),
            "pass":bool(passed),"score":round(score,3),"n":n}


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH SPACES — adapted per TF
# ─────────────────────────────────────────────────────────────────────────────

TF_SEARCH = {
    "15min": dict(
        cmf_thr=[0.05,0.08,0.10,0.12],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[True], sh=[7], se=[18],
        avoid_m=[True,False], avoid_f=[False],
        adr_cap=[0.70,0.80],
        slm=[1.5,2.0,2.5], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[3,5,8],
    ),
    "30min": dict(
        cmf_thr=[0.05,0.08,0.10,0.12],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[True,False], sh=[7], se=[18],
        avoid_m=[True,False], avoid_f=[False],
        adr_cap=[0.70,0.80],
        slm=[1.5,2.0,2.5], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[3,5],
    ),
    "1h": dict(
        cmf_thr=[0.05,0.08,0.10,0.12],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[True,False], sh=[7], se=[18],
        avoid_m=[False], avoid_f=[False],
        adr_cap=[0.80],
        slm=[1.5,2.0,2.5], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0,6.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[3,5],
    ),
    "2h": dict(
        cmf_thr=[0.05,0.08,0.10],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        adr_cap=[0.80],
        slm=[1.5,2.0,2.5], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0,6.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[2,3],
    ),
    "3h": dict(
        cmf_thr=[0.05,0.08,0.10],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        adr_cap=[0.80],
        slm=[1.5,2.0,2.5], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0,6.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[2,3],
    ),
    "4h": dict(
        cmf_thr=[0.05,0.08,0.10],
        min_score=[4,5,6,7],
        mfi_os=[25,30,35], mfi_ob=[65,70,75],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        adr_cap=[0.80],
        slm=[1.5,2.0,2.5,3.0], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0,6.0,7.0],
        rp=[0.005,0.008], dl=[0.015], mtd=[1,2,3],
    ),
    "1D": dict(
        cmf_thr=[0.05,0.08,0.10,0.12],
        min_score=[4,5,6,7,8],
        mfi_os=[25,30,35,40], mfi_ob=[60,65,70,75],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        adr_cap=[0.90],
        slm=[1.5,2.0,2.5,3.0], tp1=[1.5,2.0,2.5], tp2=[3.0,4.0,5.0,6.0,7.0,8.0],
        rp=[0.005,0.008,0.010], dl=[0.015,0.020], mtd=[1,2,3],
    ),
}


def build_combos(tf, max_n=3000):
    pp = TF_SEARCH[tf]
    keys = list(pp.keys())
    combos = []
    for vals in itertools.product(*[pp[k] for k in keys]):
        d = dict(zip(keys, vals))
        if d["tp1"] >= d["tp2"]: continue
        if d["mfi_os"] >= d["mfi_ob"]: continue
        combos.append(d)
    random.shuffle(combos)
    return combos[:max_n]


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZE
# ─────────────────────────────────────────────────────────────────────────────

def optimize_tf(cache, tf, max_n=3000):
    combos = build_combos(tf, max_n)
    best_score = -999.0; best_p = {}; best_m = {}; passed = 0

    # Warmup Numba with a dummy call
    dummy_sig = np.zeros(cache["n"], dtype=np.int8)
    dummy_sig[300] = 1
    _bt(cache["op"], cache["hi"], cache["lo"], cache["atr14"], dummy_sig,
        0.005, 0.015, 1.5, 1.5, 3.0, 5, cache["day_idx"])

    for idx, p in enumerate(combos):
        bt_p = {"rp": p["rp"], "dl": p["dl"], "slm": p["slm"],
                "tp1": p["tp1"], "tp2": p["tp2"], "mtd": p["mtd"]}
        try:
            sig      = make_signals(cache, p)
            pnl, eq  = run_bt(cache, sig, bt_p)
            m        = mets(pnl, eq)
        except Exception as exc:
            if idx == 0:
                import traceback; traceback.print_exc()
            continue

        if m["score"] > best_score:
            best_score = m["score"]; best_p = {**p}; best_m = m
        if m["pass"]: passed += 1

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
    if "volume" not in df.columns:
        df["volume"] = 1.0
        print("  WARNING: no volume data — using 1.0 (affects OBV/CMF/MFI)")
    else:
        vz = (df["volume"] == 0).sum()
        if vz > len(df) * 0.5:
            df["volume"] = 1.0
            print("  WARNING: >50% volume zeros — using 1.0")
    print(f"  {len(df):,} M15 bars | {df.index[0].date()} → {df.index[-1].date()}\n")

    TFS = ["15min","30min","1h","2h","3h","4h","1D"]

    print("=" * 115)
    print(f"{'GVF SCORE OPTIMIZER — XAUUSD 2016-2026':^115}")
    print(f"{'Objetivos: ≥2%/mes | DD≤7% | ≥7T/mes | peor_día≥-3%':^115}")
    print("=" * 115)
    print(f"{'TF':<8} {'Mon%':>7} {'DD%':>7} {'Shr':>6} {'T/M':>6} "
          f"{'WR':>6} {'WDay':>7} {'N':>6} {'✓':>3}  best_params")
    print("-" * 115)

    all_res = []; all_params = {}

    for tf in TFS:
        rule = RESAMPLE[tf]
        t0   = time.time()
        print(f"  ⏳ {tf} precomputing …", end="", flush=True)
        cache = precompute(df, rule)
        print(f" {cache['n']:,} bars → grid search …", end="", flush=True)

        bp, bm, pc = optimize_tf(cache, tf, max_n=3000)
        elapsed = time.time() - t0

        ok = "✅" if bm.get("pass") else "✗ "
        pp = (f"sc≥{bp.get('min_score','?')} cmf={bp.get('cmf_thr','?')} "
              f"sl={bp.get('slm','?')} tp1={bp.get('tp1','?')} tp2={bp.get('tp2','?')} "
              f"lo={bp.get('lo_only','?')} s={bp.get('use_sess','?')} "
              f"rp={bp.get('rp','?')} mtd={bp.get('mtd','?')}")
        print(f"\r{tf:<8} {bm.get('m',0):>7.2f} {bm.get('dd',0):>7.2f} "
              f"{bm.get('sh',0):>6.3f} {bm.get('tpm',0):>6.1f} "
              f"{bm.get('wr',0):>6.1f} {bm.get('wd',0):>7.2f} "
              f"{bm.get('n',0):>6} {ok}  {pp}  [{elapsed:.0f}s,{pc}✓]")

        all_res.append({"TF":tf,**bm,"params":bp})
        all_params[tf] = bp

    print("=" * 115)
    passed = sum(1 for r in all_res if r.get("pass"))
    print(f"\n✅ {passed}/{len(TFS)} timeframes pasan objetivos\n")

    Path("results").mkdir(exist_ok=True)
    rows = [{"TF":r["TF"],"Monthly%":r["m"],"MaxDD%":r["dd"],"Sharpe":r["sh"],
             "T/Mes":r["tpm"],"WR%":r["wr"],"WorstDay%":r["wd"],"N":r["n"],
             "Passed":"YES" if r["pass"] else "NO",**r["params"]}
            for r in all_res]
    pd.DataFrame(rows).to_csv("results/gvf_optimizer.csv", index=False)
    with open("results/gvf_optimizer_params.json","w") as f:
        json.dump(all_params, f, indent=2, default=str)
    print("💾 results/gvf_optimizer.csv")
    print("💾 results/gvf_optimizer_params.json")


if __name__ == "__main__":
    main()
