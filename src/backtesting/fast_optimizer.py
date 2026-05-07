#!/usr/bin/env python3
"""
Fast XAUUSD Optimizer — MA Cross + ATR SL/TP + Filters
=======================================================
Estrategia:
  • Señal: cruce de EMA(fast) / EMA(slow)
  • Filtro macro: EMA(200) — long_only=True → no shorts en tendencia alcista
  • Exits: ATR-based SL + TP1 parcial (50%) + TP2
  • Filtros: sesión, RSI extremo, ADR diario

Optimización:
  • Numba JIT en el backtest loop
  • Precalcula EMA(200), ATR, RSI, CMF por timeframe UNA VEZ
  • Grid search sobre (fast, slow, sl_mult, tp1, tp2, filtros)

Objetivos:
  monthly ≥ 2%, DD ≤ 7%, trades/mes ≥ 7, peor_día ≥ -3%
"""

import itertools, json, random, time, warnings
from pathlib import Path

import numba
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

MONTHS    = 10.3 * 12   # 123.6
OBJ_M     = 2.0
OBJ_DD    = -7.0
OBJ_TPM   = 7.0
OBJ_WD    = -3.0
INITIAL   = 100_000.0

# ─────────────────────────────────────────────────────────────────────────────
# VECTORIZED HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def ema_v(s, n):
    return s.ewm(span=n, adjust=False).mean().values

def atr14_v(df):
    hi, lo, cl = df["high"].values, df["low"].values, df["close"].values
    tr = np.maximum(hi - lo, np.maximum(np.abs(hi - np.roll(cl,1)),
                                         np.abs(lo - np.roll(cl,1))))
    tr[0] = hi[0] - lo[0]
    a = pd.Series(tr).ewm(span=14, adjust=False).mean().values
    return a

def rsi14_v(cl):
    d  = np.diff(cl, prepend=cl[0])
    up = np.where(d > 0, d, 0.0)
    dn = np.where(d < 0, -d, 0.0)
    au = pd.Series(up).ewm(span=14, adjust=False).mean().values
    ad = pd.Series(dn).ewm(span=14, adjust=False).mean().values
    rs = np.where(ad > 0, au / ad, 100.0)
    return 100.0 - 100.0 / (1.0 + rs)

def precompute_tf(df_m15, rule):
    """Resample + compute slow-changing indicators once per TF."""
    if rule is None:
        df = df_m15.copy()
    else:
        agg = {"open":"first","high":"max","low":"min","close":"last","volume":"sum"}
        df  = df_m15.resample(rule).agg(agg).dropna(subset=["close"])

    cl = df["close"].values

    # Cumulative daily high/low for ADR and intraday range
    date_col      = df.index.normalize()
    day_hi_cum    = df.groupby(date_col)["high"].cummax().values
    day_lo_cum    = df.groupby(date_col)["low"].cummin().values
    day_range_arr = day_hi_cum - day_lo_cum

    # 14-day ADR
    daily_hl   = df.groupby(date_col).apply(lambda g: g["high"].max() - g["low"].min())
    daily_hl.index = pd.to_datetime(daily_hl.index)
    adr_roll   = daily_hl.rolling(14).mean()
    bar_dates  = date_col
    adr_arr    = bar_dates.map(adr_roll.to_dict()).values.astype(float)

    cache = {
        "df":         df,
        "cl":         cl,
        "op":         df["open"].values,
        "hi":         df["high"].values,
        "lo":         df["low"].values,
        "vol":        df["volume"].values,
        "ema200":     ema_v(df["close"], 200),
        "atr14":      atr14_v(df),
        "rsi14":      rsi14_v(cl),
        "day_range":  day_range_arr,
        "adr":        adr_arr,
        "hour":       df.index.hour,
        "weekday":    df.index.dayofweek,
        "dates":      np.array([d.date() for d in df.index]),
        "n":          len(df),
    }

    # Day index integer for Numba
    days_uniq = pd.factorize(date_col)[0]
    cache["day_idx"] = days_uniq.astype(np.int32)

    # CMF (needs volume) — optional
    denom = (df["high"] - df["low"]).replace(0, np.nan)
    mf_mul = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / denom
    cmf_s  = (mf_mul * df["volume"]).rolling(20).sum() / df["volume"].rolling(20).sum().replace(0, np.nan)
    cache["cmf"] = cmf_s.values

    return cache


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL GENERATION (fast numpy)
# ─────────────────────────────────────────────────────────────────────────────

def make_signals(cache, p):
    """Fully vectorized signal generation — no Python loops."""
    n       = cache["n"]
    cl      = cache["cl"]
    em200   = cache["ema200"]
    rs      = cache["rsi14"]
    drng    = cache["day_range"]
    adr_v   = cache["adr"]
    hrs     = cache["hour"]
    wds     = cache["weekday"]

    ef = ema_v(pd.Series(cl), p["fast"])
    es = ema_v(pd.Series(cl), p["slow"])

    wu = max(210, p["slow"] + 5)

    # Boolean cross masks
    cup = (ef > es) & (np.roll(ef, 1) <= np.roll(es, 1))
    cdn = (ef < es) & (np.roll(ef, 1) >= np.roll(es, 1))
    cup[:wu] = False; cdn[:wu] = False
    cup[-1]  = False; cdn[-1]  = False

    # Filters (boolean masks)
    valid = np.ones(n, dtype=bool)
    if p.get("avoid_m"): valid &= (wds != 0)
    if p.get("avoid_f"): valid &= (wds != 4)
    if p.get("use_sess"):
        sh, se = p.get("sh", 7), p.get("se", 18)
        valid &= (hrs >= sh) & (hrs < se)

    # ADR cap
    with np.errstate(invalid="ignore", divide="ignore"):
        adr_ratio = np.where(adr_v > 0, drng / adr_v, 0)
    valid &= adr_ratio <= p.get("adr_cap", 0.80)

    # RSI extreme
    if p.get("rsi_f"):
        cup &= (rs <= 75)
        cdn &= (rs >= 25)

    # Macro / long-only filter
    if p.get("lo_only"):
        bull = cl > em200
        cdn &= ~bull   # no shorts when price > EMA200

    cup &= valid; cdn &= valid

    sig = np.zeros(n, dtype=np.int8)
    sig[cup] = 1
    sig[cdn] = -1
    return sig


# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST (pure numpy, fast)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST (Numba JIT — ~50x faster than Python loop)
# ─────────────────────────────────────────────────────────────────────────────

@numba.njit(cache=True)
def _bt_numba(op, hi, lo, at, sig,
              risk_pct, daily_limit, sl_m, tp1_r, tp2_r, max_td,
              day_idx):
    """
    day_idx: integer array mapping bar → day number (0-based)
    Returns (equity_array, pnl_per_trade array, n_trades)
    """
    n       = len(op)
    eq_arr  = np.empty(n); eq_arr[0] = 100_000.0
    capital = 100_000.0

    MAX_DAYS   = day_idx[-1] + 2
    day_pnl    = np.zeros(MAX_DAYS)
    day_cnt    = np.zeros(MAX_DAYS, dtype=numba.int32)

    pos      = 0
    entry_p  = 0.0; sl_p = 0.0; tp1_p = 0.0; tp2_p = 0.0
    risk_usd = 0.0; tp1_done = False

    pnl_buf  = np.zeros(10000)
    nt       = 0

    for i in range(1, n):
        d = day_idx[i]

        if pos != 0:
            bop = op[i]; bhi = hi[i]; blo = lo[i]

            if pos == 1:
                if bop <= sl_p:
                    pnl = -risk_usd
                    capital += pnl; day_pnl[d] += pnl
                    if nt < 10000: pnl_buf[nt] = pnl; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if blo <= sl_p:
                    pnl = 0.0 if tp1_done else -risk_usd
                    capital += pnl; day_pnl[d] += pnl
                    if nt < 10000: pnl_buf[nt] = pnl; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if not tp1_done and bhi >= tp1_p:
                    pnl1 = risk_usd * tp1_r * 0.5
                    capital += pnl1; day_pnl[d] += pnl1
                    sl_p = entry_p; tp1_done = True
                    if bhi >= tp2_p:
                        pnl2 = risk_usd * tp2_r * 0.5
                        capital += pnl2; day_pnl[d] += pnl2
                        if nt < 10000: pnl_buf[nt] = pnl1 + pnl2; nt += 1
                        pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if tp1_done and bhi >= tp2_p:
                    pnl2 = risk_usd * tp2_r * 0.5
                    capital += pnl2; day_pnl[d] += pnl2
                    if nt < 10000: pnl_buf[nt] = pnl2; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue
            else:  # SHORT
                if bop >= sl_p:
                    pnl = -risk_usd
                    capital += pnl; day_pnl[d] += pnl
                    if nt < 10000: pnl_buf[nt] = pnl; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if bhi >= sl_p:
                    pnl = 0.0 if tp1_done else -risk_usd
                    capital += pnl; day_pnl[d] += pnl
                    if nt < 10000: pnl_buf[nt] = pnl; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if not tp1_done and blo <= tp1_p:
                    pnl1 = risk_usd * tp1_r * 0.5
                    capital += pnl1; day_pnl[d] += pnl1
                    sl_p = entry_p; tp1_done = True
                    if blo <= tp2_p:
                        pnl2 = risk_usd * tp2_r * 0.5
                        capital += pnl2; day_pnl[d] += pnl2
                        if nt < 10000: pnl_buf[nt] = pnl1 + pnl2; nt += 1
                        pos = 0; tp1_done = False; eq_arr[i] = capital; continue
                if tp1_done and blo <= tp2_p:
                    pnl2 = risk_usd * tp2_r * 0.5
                    capital += pnl2; day_pnl[d] += pnl2
                    if nt < 10000: pnl_buf[nt] = pnl2; nt += 1
                    pos = 0; tp1_done = False; eq_arr[i] = capital; continue

        if pos == 0 and sig[i-1] != 0:
            if day_pnl[d] / capital <= -daily_limit: eq_arr[i] = capital; continue
            if day_cnt[d] >= max_td:                 eq_arr[i] = capital; continue
            at_i = at[i]
            if at_i <= 0.0:                          eq_arr[i] = capital; continue

            entry_p  = op[i]
            sl_dist  = sl_m * at_i
            risk_usd = risk_pct * capital

            if sig[i-1] == 1:
                sl_p  = entry_p - sl_dist
                tp1_p = entry_p + sl_dist * tp1_r
                tp2_p = entry_p + sl_dist * tp2_r
                pos   = 1
            else:
                sl_p  = entry_p + sl_dist
                tp1_p = entry_p - sl_dist * tp1_r
                tp2_p = entry_p - sl_dist * tp2_r
                pos   = -1

            tp1_done = False
            day_cnt[d] += 1

        eq_arr[i] = capital

    return eq_arr, pnl_buf[:nt], nt


def run_bt(cache, sig, p):
    eq_arr, pnl_arr, nt = _bt_numba(
        cache["op"], cache["hi"], cache["lo"], cache["atr14"],
        sig.astype(np.int8),
        p["rp"], p["dl"], p["slm"], p["tp1"], p["tp2"],
        int(p.get("mtd", 5)),
        cache["day_idx"],
    )
    return pnl_arr[:nt], eq_arr


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

def metrics(pnl_arr, eq_arr):
    n_trades = len(pnl_arr)
    if n_trades == 0:
        return {"m": 0, "dd": 0, "tpm": 0, "wd": 0, "wr": 0, "sh": 0,
                "pass": False, "score": -999, "n": 0}

    final   = eq_arr[-1]
    monthly = ((final / INITIAL) ** (1 / MONTHS) - 1) * 100
    tpm     = n_trades / MONTHS

    run_max = np.maximum.accumulate(eq_arr)
    dd_arr  = (eq_arr - run_max) / run_max * 100
    max_dd  = float(dd_arr.min())

    wins = int(np.sum(pnl_arr > 0))
    wr   = wins / n_trades * 100

    dret      = np.diff(eq_arr) / eq_arr[:-1]
    worst_day = float(dret.min()) * 100
    sharpe    = float(dret.mean() / (dret.std() + 1e-12) * np.sqrt(252))

    passed = (monthly >= OBJ_M and max_dd >= OBJ_DD
              and tpm >= OBJ_TPM and worst_day >= OBJ_WD)

    score = (monthly * 1.5
             + max(0, max_dd - OBJ_DD) * 0.4
             + min(tpm, 60) * 0.05
             + sharpe * 0.5
             + (15 if passed else 0))

    return {"m": round(monthly, 3), "dd": round(max_dd, 2),
            "tpm": round(tpm, 1), "wd": round(worst_day, 2),
            "wr": round(wr, 1), "sh": round(sharpe, 3),
            "pass": bool(passed), "score": round(score, 3), "n": n_trades}


# ─────────────────────────────────────────────────────────────────────────────
# PER-TF GRID SEARCH
# ─────────────────────────────────────────────────────────────────────────────

TF_PARAMS = {
    "15min": dict(fast=[5,8,10,12,15], slow=[20,26,30,40,50],
                  slm=[1.0,1.5,2.0], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0],
                  lo_only=[True,False], use_sess=[True], avoid_m=[True,False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[3,5],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "30min": dict(fast=[8,10,12,15,20], slow=[20,26,30,40,50],
                  slm=[1.0,1.5,2.0], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0],
                  lo_only=[True,False], use_sess=[True,False], avoid_m=[True,False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[3,5],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "1h":    dict(fast=[5,8,10,12,15,20], slow=[15,20,26,30,40,50],
                  slm=[1.0,1.5,2.0], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0],
                  lo_only=[True,False], use_sess=[True,False], avoid_m=[False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[3,5],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "2h":    dict(fast=[5,8,10,12,15,20], slow=[15,20,26,30,40,50],
                  slm=[1.0,1.5,2.0,2.5], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0,5.0],
                  lo_only=[True,False], use_sess=[False], avoid_m=[False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[2,3],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "3h":    dict(fast=[5,8,10,12,15,20], slow=[15,20,26,30,40,50],
                  slm=[1.0,1.5,2.0,2.5], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0,5.0],
                  lo_only=[True,False], use_sess=[False], avoid_m=[False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[2,3],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "4h":    dict(fast=[5,8,10,12,15,20], slow=[15,20,26,30,40,50],
                  slm=[1.5,2.0,2.5], tp1=[1.0,1.5], tp2=[2.0,3.0,4.0,5.0],
                  lo_only=[True,False], use_sess=[False], avoid_m=[False],
                  avoid_f=[False], rsi_f=[False,True], mtd=[2,3],
                  sh=[7], se=[18], adr_cap=[0.80]),
    "1D":    dict(fast=[5,8,10,12,15,20], slow=[20,26,30,40,50],
                  slm=[1.5,2.0,2.5], tp1=[1.0,1.5], tp2=[2.0,3.0,5.0,7.0],
                  lo_only=[True,False], use_sess=[False], avoid_m=[False],
                  avoid_f=[False], rsi_f=[False], mtd=[1,2],
                  sh=[0], se=[24], adr_cap=[0.90]),
}

RESAMPLE = {"15min":None,"30min":"30min","1h":"1h","2h":"2h","3h":"3h","4h":"4h","1D":"1D"}


def build_combos(tf, max_n=3000):
    pp = TF_PARAMS[tf]
    keys   = list(pp.keys())
    combos = []
    for vals in itertools.product(*[pp[k] for k in keys]):
        d = dict(zip(keys, vals))
        if d["fast"] >= d["slow"]: continue
        if d["tp1"] >= d["tp2"]:   continue
        combos.append(d)
    random.shuffle(combos)
    return combos[:max_n]


def optimize_tf(cache, tf, max_n=3000):
    combos = build_combos(tf, max_n)
    best_score = -999; best_p = {}; best_m = {}
    passed = 0

    for idx, p in enumerate(combos):
        # Pack into compact param dict
        bt_p = {"rp": 0.005, "dl": 0.015, "slm": p["slm"],
                "tp1": p["tp1"], "tp2": p["tp2"], "mtd": p["mtd"]}
        sig_p = {"fast": p["fast"], "slow": p["slow"],
                 "use_sess": p["use_sess"], "sh": p["sh"], "se": p["se"],
                 "avoid_m": p["avoid_m"], "avoid_f": p["avoid_f"],
                 "adr_cap": p["adr_cap"], "lo_only": p["lo_only"],
                 "rsi_f": p["rsi_f"]}
        try:
            sig       = make_signals(cache, sig_p)
            pnl, eq   = run_bt(cache, sig, bt_p)
            m         = metrics(pnl, eq)
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
    data_path = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
    print(f"Loading {data_path} …")
    df_m15 = pd.read_parquet(data_path)
    df_m15.index = pd.to_datetime(df_m15.index)
    df_m15.columns = [c.lower() for c in df_m15.columns]
    if "volume" not in df_m15.columns:
        df_m15["volume"] = 1.0
    print(f"  {len(df_m15):,} M15 bars | {df_m15.index[0].date()} → {df_m15.index[-1].date()}\n")

    TIMEFRAMES = ["15min", "30min", "1h", "2h", "3h", "4h", "1D"]

    hdr = (f"{'TF':<8} {'Mon%':>7} {'DD%':>7} {'Shr':>6} {'Trd/M':>6} "
           f"{'WR':>6} {'WDay':>7} {'N':>6} {'OK':>3}  params")
    print("=" * 100)
    print(f"{'FAST OPTIMIZER — XAUUSD 2016-2026':^100}")
    print(f"{'Objetivos: ≥2%/mes | DD≤7% | ≥7T/mes | peor_día≥-3%':^100}")
    print("=" * 100)
    print(hdr)
    print("-" * 100)

    all_results = []
    all_params  = {}

    for tf in TIMEFRAMES:
        rule = RESAMPLE[tf]
        t0   = time.time()
        print(f"  ⏳ {tf} — precomputing …", end="", flush=True)
        cache = precompute_tf(df_m15, rule)
        print(f" {len(cache['df']):,} bars → grid search …", end="", flush=True)

        bp, bm, passed_ct = optimize_tf(cache, tf, max_n=3000)
        elapsed = time.time() - t0

        ok = "✅" if bm.get("pass") else "✗ "
        pp = (f"f={bp.get('fast','?')}/s={bp.get('slow','?')} "
              f"sl={bp.get('slm','?')} tp1={bp.get('tp1','?')} tp2={bp.get('tp2','?')} "
              f"lo={bp.get('lo_only','?')} sess={bp.get('use_sess','?')} "
              f"rsi={bp.get('rsi_f','?')} mtd={bp.get('mtd','?')}")

        print(f"\r{tf:<8} {bm.get('m',0):>7.2f} {bm.get('dd',0):>7.2f} "
              f"{bm.get('sh',0):>6.3f} {bm.get('tpm',0):>6.1f} "
              f"{bm.get('wr',0):>6.1f} {bm.get('wd',0):>7.2f} "
              f"{bm.get('n',0):>6} {ok}  {pp}  [{elapsed:.0f}s, {passed_ct} passed]")

        all_results.append({"TF": tf, **bm, "params": bp})
        all_params[tf] = bp

    print("=" * 100)
    passed_total = sum(1 for r in all_results if r.get("pass"))
    print(f"\n✅ {passed_total}/{len(TIMEFRAMES)} timeframes pasan todos los objetivos\n")

    # Save
    Path("results").mkdir(exist_ok=True)
    rows = [{
        "Timeframe": r["TF"], "Monthly%": r["m"], "MaxDD%": r["dd"],
        "Sharpe": r["sh"], "Trades/Mes": r["tpm"], "WR%": r["wr"],
        "WorstDay%": r["wd"], "NTrades": r["n"],
        "Passed": "YES" if r["pass"] else "NO",
        **r["params"]
    } for r in all_results]
    df_out = pd.DataFrame(rows)
    csv_p = "results/fast_optimizer_results.csv"
    df_out.to_csv(csv_p, index=False)
    print(f"💾 {csv_p}")

    json_p = "results/fast_optimizer_params.json"
    with open(json_p, "w") as f:
        json.dump(all_params, f, indent=2, default=str)
    print(f"💾 {json_p}")


if __name__ == "__main__":
    main()
