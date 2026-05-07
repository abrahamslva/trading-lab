#!/usr/bin/env python3
"""
XAUUSD Breakout Strategy Optimizer — 2016-2026
==============================================
Basado en biblia_oro.txt: Asian Breakout tiene 70-80% WR en XAUUSD
Estrategia:
  • Señal: Breakout de rango N-barra (high/low del periodo anterior)
  • Confirmación: ATR filter (no entrar si rango < 0.5 ATR — rango pequeño)
  • Filtro macro: EMA(200)
  • Exits: ATR SL + partial TP

Objetivos: ≥2%/mes | DD≤7% | ≥7 trades/mes | peor día ≥-3%
"""

import itertools, json, random, time, warnings
from pathlib import Path

import numba
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MONTHS  = 10.3 * 12
OBJ_M   = 2.0; OBJ_DD = -7.0; OBJ_TPM = 7.0; OBJ_WD = -3.0
INITIAL = 100_000.0

RESAMPLE = {"15min":None,"30min":"30min","1h":"1h","2h":"2h","3h":"3h","4h":"4h","1D":"1D"}


# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────────────────────────────────────

def ema_v(s, n):
    return s.ewm(span=n, adjust=False).mean().values

def atr_v(df, n=14):
    hi, lo, cl = df["high"].values, df["low"].values, df["close"].values
    tr = np.maximum(hi - lo, np.maximum(np.abs(hi - np.roll(cl,1)),
                                         np.abs(lo - np.roll(cl,1))))
    tr[0] = hi[0] - lo[0]
    return pd.Series(tr).ewm(span=n, adjust=False).mean().values

def precompute(df_m15, rule):
    if rule is None:
        df = df_m15.copy()
    else:
        agg = {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        df  = df_m15.resample(rule).agg(agg).dropna(subset=["close"])

    cl = df["close"].values
    date_col   = df.index.normalize()
    day_idx    = pd.factorize(date_col)[0].astype(np.int32)

    # Rolling N-bar high/low for breakout signal
    # Precompute for multiple lookback periods
    hi_arr = df["high"].values
    lo_arr = df["low"].values

    return {
        "n":      len(df),
        "op":     df["open"].values,
        "hi":     hi_arr,
        "lo":     lo_arr,
        "cl":     cl,
        "atr14":  atr_v(df, 14),
        "ema200": ema_v(df["close"], 200),
        "hour":   df.index.hour.values.astype(np.int32),
        "wday":   df.index.dayofweek.values.astype(np.int32),
        "day_idx":day_idx,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL: N-bar breakout (vectorized)
# ─────────────────────────────────────────────────────────────────────────────

def make_signals_breakout(cache, p):
    """
    Breakout + Retest strategy:
    1. Price breaks above N-bar high (close > roll_hi) → mark level
    2. Next bar retest: price dips back to the breakout level ± tolerance
    3. Enter LONG if price recovers above it
    
    OR simpler version that increases WR:
    Use MOMENTUM: enter when CLOSE is above HIGH of N bars ago (immediate)
    but only if ATR-relative bar is large (real breakout, not noise)
    AND price did not already move > atr_ratio*ATR from level (not chasing)
    """
    n     = cache["n"]
    hi    = cache["hi"]
    lo    = cache["lo"]
    cl    = cache["cl"]
    op    = cache["op"]
    at    = cache["atr14"]
    em200 = cache["ema200"]
    hrs   = cache["hour"]
    wds   = cache["wday"]

    lb      = p["lookback"]
    ar      = p.get("atr_ratio", 0.3)
    lo_only = p.get("lo_only", True)
    use_s   = p.get("use_sess", False)
    sh, se  = p.get("sh", 7), p.get("se", 18)
    av_m    = p.get("avoid_m", False)
    av_f    = p.get("avoid_f", False)
    retest  = p.get("retest", False)  # Use retest mode

    # Rolling N-bar high/low (on close, shifted 1 so current bar not included)
    # Use shift(1) so we're looking at the PRIOR N bars
    roll_hi = pd.Series(cl).shift(1).rolling(lb).max().values
    roll_lo = pd.Series(cl).shift(1).rolling(lb).min().values

    wu   = max(215, lb + 2)
    sig  = np.zeros(n, dtype=np.int8)

    valid = np.ones(n, dtype=bool)
    valid[:wu] = False; valid[-1] = False

    if av_m: valid &= (wds != 0)
    if av_f: valid &= (wds != 4)
    if use_s: valid &= (hrs >= sh) & (hrs < se)

    if retest:
        # Retest mode: wait for price to touch the breakout level from above/below
        # Step 1: detect breakout (close > roll_hi)
        broke_hi = np.zeros(n, dtype=bool)
        broke_lo = np.zeros(n, dtype=bool)
        broke_hi_level = np.full(n, np.nan)
        broke_lo_level = np.full(n, np.nan)

        # Mark breakout events
        bup_event = (cl > roll_hi) & ~np.isnan(roll_hi)
        bdn_event = (cl < roll_lo) & ~np.isnan(roll_lo)

        # Propagate breakout state for max N bars looking for retest
        active_hi = np.full(n, np.nan)  # level of pending long retest
        active_lo = np.full(n, np.nan)  # level of pending short retest
        
        for i in range(wu, n-1):
            if bup_event[i]:
                active_hi[i] = roll_hi[i]   # save breakout level
            else:
                if i > 0 and not np.isnan(active_hi[i-1]):
                    # Check retest: low touches the level
                    lv = active_hi[i-1]
                    if lo[i] <= lv * 1.001 and cl[i] >= lv * 0.999:
                        # Retest complete — enter long
                        if valid[i]:
                            sig[i] = 1
                        active_hi[i] = np.nan   # consumed
                    elif cl[i] < lv * 0.995:    # broke down — cancel
                        active_hi[i] = np.nan
                    else:
                        active_hi[i] = active_hi[i-1]  # keep waiting

            if bdn_event[i]:
                active_lo[i] = roll_lo[i]
            else:
                if i > 0 and not np.isnan(active_lo[i-1]):
                    lv = active_lo[i-1]
                    if hi[i] >= lv * 0.999 and cl[i] <= lv * 1.001:
                        if valid[i]:
                            sig[i] = -1
                        active_lo[i] = np.nan
                    elif cl[i] > lv * 1.005:
                        active_lo[i] = np.nan
                    else:
                        active_lo[i] = active_lo[i-1]
    else:
        # Direct breakout mode with ATR confirmation
        bar_range = hi - lo
        # Only enter if bar range is meaningful (confirms momentum)
        with np.errstate(invalid="ignore"):
            strong_bar = bar_range > ar * at

        bup = valid & strong_bar & (cl > roll_hi) & ~np.isnan(roll_hi)
        bdn = valid & strong_bar & (cl < roll_lo) & ~np.isnan(roll_lo)

        # Don't chase: close not too far from level
        with np.errstate(invalid="ignore"):
            not_chasing_up = (cl - roll_hi) < 2.0 * at   # max 2 ATR above level
            not_chasing_dn = (roll_lo - cl) < 2.0 * at

        bup &= not_chasing_up
        bdn &= not_chasing_dn

        # Macro filter
        bull = cl > em200
        if lo_only:
            bdn &= ~bull

        bup &= ~bdn
        sig[bup] = 1
        sig[bdn] = -1

    # Final macro filter for retest mode too
    if lo_only and retest:
        bull = cl > em200
        sig[(sig == -1) & bull] = 0

    return sig


# ─────────────────────────────────────────────────────────────────────────────
# NUMBA BACKTEST
# ─────────────────────────────────────────────────────────────────────────────

@numba.njit(cache=True)
def _bt(op, hi, lo, at, sig, rp, dl, slm, tp1r, tp2r, mtd, day_idx):
    n        = len(op)
    eq       = np.empty(n); eq[0] = 100_000.0
    cap      = 100_000.0
    nd       = day_idx[-1] + 2
    dpnl     = np.zeros(nd)
    dcnt     = np.zeros(nd, dtype=numba.int32)

    pos = 0; ep = sl = tp1 = tp2 = ru = 0.0; td = False
    buf = np.zeros(20000); nt = 0

    for i in range(1, n):
        d = day_idx[i]

        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            if pos == 1:
                if bo <= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 20000: buf[nt] = -ru; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if bl <= sl:
                    pnl = 0.0 if td else -ru
                    cap += pnl; dpnl[d] += pnl
                    if nt < 20000: buf[nt] = pnl; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if not td and bh >= tp1:
                    p1 = ru * tp1r * 0.5
                    cap += p1; dpnl[d] += p1; sl = ep; td = True
                    if bh >= tp2:
                        p2 = ru * tp2r * 0.5
                        cap += p2; dpnl[d] += p2
                        if nt < 20000: buf[nt] = p1 + p2; nt += 1
                        pos = 0; td = False; eq[i] = cap; continue
                if td and bh >= tp2:
                    p2 = ru * tp2r * 0.5
                    cap += p2; dpnl[d] += p2
                    if nt < 20000: buf[nt] = p2; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
            else:
                if bo >= sl:
                    cap += -ru; dpnl[d] += -ru
                    if nt < 20000: buf[nt] = -ru; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if bh >= sl:
                    pnl = 0.0 if td else -ru
                    cap += pnl; dpnl[d] += pnl
                    if nt < 20000: buf[nt] = pnl; nt += 1
                    pos = 0; td = False; eq[i] = cap; continue
                if not td and bl <= tp1:
                    p1 = ru * tp1r * 0.5
                    cap += p1; dpnl[d] += p1; sl = ep; td = True
                    if bl <= tp2:
                        p2 = ru * tp2r * 0.5
                        cap += p2; dpnl[d] += p2
                        if nt < 20000: buf[nt] = p1 + p2; nt += 1
                        pos = 0; td = False; eq[i] = cap; continue
                if td and bl <= tp2:
                    p2 = ru * tp2r * 0.5
                    cap += p2; dpnl[d] += p2
                    if nt < 20000: buf[nt] = p2; nt += 1
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
    score   = monthly*1.5 + max(0, max_dd - OBJ_DD)*0.4 + min(tpm,60)*0.05 + sh*0.5 + (15 if passed else 0)
    return {"m":round(monthly,3),"dd":round(max_dd,2),"tpm":round(tpm,1),
            "wd":round(wd,2),"wr":round(wr,1),"sh":round(sh,3),
            "pass":bool(passed),"score":round(score,3),"n":n}


# ─────────────────────────────────────────────────────────────────────────────
# SEARCH SPACES
# ─────────────────────────────────────────────────────────────────────────────

TF_SEARCH = {
    "15min": dict(
        lookback=[3,5,8,12,16,20],
        atr_ratio=[0.1,0.2,0.3,0.5],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[True], sh=[7], se=[18],
        avoid_m=[True,False], avoid_f=[False],
        slm=[1.0,1.5,2.0], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0],
        rp=[0.005], dl=[0.015], mtd=[3,5,8],
    ),
    "30min": dict(
        lookback=[3,5,8,12,16,20],
        atr_ratio=[0.1,0.2,0.3,0.5],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[True,False], sh=[7], se=[18],
        avoid_m=[True,False], avoid_f=[False],
        slm=[1.0,1.5,2.0], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0],
        rp=[0.005], dl=[0.015], mtd=[3,5],
    ),
    "1h": dict(
        lookback=[3,5,8,12,16,20,24],
        atr_ratio=[0.1,0.2,0.3,0.5],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[True,False], sh=[7], se=[18],
        avoid_m=[False], avoid_f=[False],
        slm=[1.0,1.5,2.0,2.5], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0],
        rp=[0.005], dl=[0.015], mtd=[3,5],
    ),
    "2h": dict(
        lookback=[3,5,8,12,16,20],
        atr_ratio=[0.1,0.2,0.3],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        slm=[1.0,1.5,2.0,2.5], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0,6.0],
        rp=[0.005], dl=[0.015], mtd=[2,3],
    ),
    "3h": dict(
        lookback=[3,5,8,12,16,20],
        atr_ratio=[0.1,0.2,0.3],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        slm=[1.0,1.5,2.0,2.5], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0,6.0],
        rp=[0.005], dl=[0.015], mtd=[2,3],
    ),
    "4h": dict(
        lookback=[3,5,8,10,12,15,20],
        atr_ratio=[0.1,0.2,0.3],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        slm=[1.5,2.0,2.5], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0,6.0],
        rp=[0.005], dl=[0.015], mtd=[1,2,3],
    ),
    "1D": dict(
        lookback=[3,5,8,10,12,15,20],
        atr_ratio=[0.0,0.1,0.2],
        retest=[False, True],
        lo_only=[True,False],
        use_sess=[False], sh=[0], se=[24],
        avoid_m=[False], avoid_f=[False],
        slm=[1.5,2.0,2.5,3.0], tp1=[1.0,1.5,2.0], tp2=[2.0,3.0,4.0,5.0,7.0],
        rp=[0.005], dl=[0.015], mtd=[1,2],
    ),
}

def build_combos(tf, max_n=3000):
    pp = TF_SEARCH[tf]
    keys = list(pp.keys())
    combos = []
    for vals in itertools.product(*[pp[k] for k in keys]):
        d = dict(zip(keys, vals))
        if d["tp1"] >= d["tp2"]: continue
        combos.append(d)
    random.shuffle(combos)
    return combos[:max_n]


# ─────────────────────────────────────────────────────────────────────────────
# OPTIMIZE
# ─────────────────────────────────────────────────────────────────────────────

def optimize_tf(cache, tf, max_n=3000):
    combos = build_combos(tf, max_n)
    best_score = -999.0; best_p = {}; best_m = {}; passed = 0

    for idx, p in enumerate(combos):
        bt_p = {"rp": p["rp"], "dl": p["dl"], "slm": p["slm"],
                "tp1": p["tp1"], "tp2": p["tp2"], "mtd": p["mtd"]}
        try:
            sig      = make_signals_breakout(cache, p)
            pnl, eq  = run_bt(cache, sig, bt_p)
            m        = mets(pnl, eq)
        except Exception as exc:
            if idx == 0: import traceback; traceback.print_exc()
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
    if "volume" not in df.columns: df["volume"] = 1.0
    print(f"  {len(df):,} M15 bars | {df.index[0].date()} → {df.index[-1].date()}\n")

    TFS = ["15min","30min","1h","2h","3h","4h","1D"]

    print("=" * 110)
    print(f"{'BREAKOUT OPTIMIZER — XAUUSD 2016-2026':^110}")
    print(f"{'Objetivos: ≥2%/mes | DD≤7% | ≥7T/mes | peor_día≥-3%':^110}")
    print("=" * 110)
    hdr = (f"{'TF':<8} {'Mon%':>7} {'DD%':>7} {'Shr':>6} {'T/M':>6} "
           f"{'WR':>6} {'WDay':>7} {'N':>6} {'✓':>3}  best_params")
    print(hdr); print("-" * 110)

    all_res = []; all_params = {}

    for tf in TFS:
        rule = RESAMPLE[tf]
        t0   = time.time()
        print(f"  ⏳ {tf} precomputing …", end="", flush=True)
        cache = precompute(df, rule)
        print(f" {cache['n']:,} bars → searching …", end="", flush=True)

        bp, bm, pc = optimize_tf(cache, tf, max_n=3000)
        elapsed = time.time() - t0

        ok = "✅" if bm.get("pass") else "✗ "
        pp = (f"lb={bp.get('lookback','?')} ar={bp.get('atr_ratio','?')} "
              f"sl={bp.get('slm','?')} tp1={bp.get('tp1','?')} tp2={bp.get('tp2','?')} "
              f"lo={bp.get('lo_only','?')} s={bp.get('use_sess','?')} "
              f"mtd={bp.get('mtd','?')}")
        print(f"\r{tf:<8} {bm.get('m',0):>7.2f} {bm.get('dd',0):>7.2f} "
              f"{bm.get('sh',0):>6.3f} {bm.get('tpm',0):>6.1f} "
              f"{bm.get('wr',0):>6.1f} {bm.get('wd',0):>7.2f} "
              f"{bm.get('n',0):>6} {ok}  {pp}  [{elapsed:.0f}s,{pc}✓]")

        all_res.append({"TF":tf,**bm,"params":bp})
        all_params[tf] = bp

    print("=" * 110)
    passed = sum(1 for r in all_res if r.get("pass"))
    print(f"\n✅ {passed}/{len(TFS)} timeframes pasan objetivos\n")

    Path("results").mkdir(exist_ok=True)
    rows = [{"TF":r["TF"],"Monthly%":r["m"],"MaxDD%":r["dd"],"Sharpe":r["sh"],
             "T/Mes":r["tpm"],"WR%":r["wr"],"WorstDay%":r["wd"],"N":r["n"],
             "Passed":"YES" if r["pass"] else "NO",**r["params"]}
            for r in all_res]
    pd.DataFrame(rows).to_csv("results/breakout_optimizer.csv", index=False)
    with open("results/breakout_optimizer_params.json","w") as f:
        json.dump(all_params, f, indent=2, default=str)
    print("💾 results/breakout_optimizer.csv")
    print("💾 results/breakout_optimizer_params.json")


if __name__ == "__main__":
    main()
