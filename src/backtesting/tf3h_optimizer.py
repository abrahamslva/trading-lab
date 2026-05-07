"""
3H Targeted Optimizer
=====================
Problem: 3H DD stays at -10 to -16% with D1+4H alignment because
         3H bars don't cleanly align with 4H reference frame.

Solutions tried here:
1. W1+D1 RSI alignment (weekly trend + daily RSI)
2. Tighter slm [0.3, 0.4, 0.5] to cap individual losses
3. W1 EMA alignment
4. Combined W1+D1+4H triple filter (very selective)
5. EMA crossover signal (5>13 on 3H) with W1+D1 alignment
"""

import sys, time
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

MONTHS  = 123.6
OBJ_M, OBJ_DD, OBJ_TPM, OBJ_WD = 2.0, -7.0, 7.0, -3.0

# ── helpers ──────────────────────────────────────────────────────────────────
def ema(s, n): return s.ewm(n, adjust=False).mean()

def rsi_calc(s, n=14):
    d  = s.diff()
    up = d.clip(lower=0).ewm(n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(n, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))

def stoch_k(d, k=14):
    lk = d['low'].rolling(k).min()
    hk = d['high'].rolling(k).max()
    return (d['close'] - lk) / (hk - lk + 1e-12) * 100

def resample_ohlcv(df, rule):
    return df.resample(rule).agg(
        {'open': 'first', 'high': 'max', 'low': 'min',
         'close': 'last', 'volume': 'sum'}
    ).dropna()

def ffill_to(series, target_index):
    s = series.copy()
    if hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s.reindex(target_index, method='ffill').fillna(False)

# ── load data ────────────────────────────────────────────────────────────────
def load_m15(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

def make_sig_array(long_c, short_c, n, warmup=100):
    sig = np.zeros(n, dtype=np.int8)
    w = min(warmup, n // 4)
    sig[w:] = np.where(long_c[w:], 1, np.where(short_c[w:], -1, 0))
    return sig

# ── sweep parameter grid ─────────────────────────────────────────────────────
def sweep(cache, sig_arrays):
    # Tighter slm and focused tp/hold for 3H
    SLMs  = [0.3, 0.4, 0.5, 0.6, 0.8]
    TP_Rs = [2.0, 2.5, 3.0, 4.0, 5.0]
    HOLDs = [2, 3, 4, 6, 8, 10, 12, 16]
    RPs   = [0.003, 0.005, 0.008, 0.010]

    results = []
    for name, sig in sig_arrays.items():
        best = None
        alts = []
        for slm in SLMs:
            for tp in TP_Rs:
                for h in HOLDs:
                    for rp in RPs:
                        try:
                            bt = _bt(cache['op'], cache['hi'], cache['lo'],
                                     cache['atr14'], sig, rp, 0.015, slm, tp, 5, h,
                                     cache['day_idx'])
                            m = mets(bt[1][:bt[2]], bt[0])
                            if m['tpm'] < 3:
                                continue
                            if best is None or m['score'] > best['score']:
                                best = {**m, 'slm': slm, 'tp': tp, 'h': h, 'rp': rp}
                            if m['passed']:
                                alts.append({**m, 'slm': slm, 'tp': tp, 'h': h, 'rp': rp})
                        except Exception:
                            pass
        results.append((name, best, alts))
    return results

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 100)
    print("3H TARGETED OPTIMIZER")
    print("Focus: W1+D1 alignment, tighter slm [0.3-0.8], EMA crossover signals")
    print("=" * 100)

    m15 = load_m15()
    print(f"M15 data: {len(m15):,} bars  {m15.index[0].date()} → {m15.index[-1].date()}\n")

    # Build reference signals
    print("Building reference signals…")
    # 4H RSI
    h4 = resample_ohlcv(m15, '4h')
    h4_rsi_bool = (rsi_calc(h4['close'], 14) > 50)
    h4_rsi_bool.index = pd.to_datetime(h4_rsi_bool.index).tz_localize(None)

    # D1 RSI
    d1 = resample_ohlcv(m15, 'D')
    d1_rsi_bool = (rsi_calc(d1['close'], 14) > 50)
    d1_rsi_bool.index = pd.to_datetime(d1_rsi_bool.index).tz_localize(None)

    # D1 EMA50 > EMA200
    d1_ema_bool = (ema(d1['close'], 50) > ema(d1['close'], 200))
    d1_ema_bool.index = pd.to_datetime(d1_ema_bool.index).tz_localize(None)

    # W1 RSI
    w1 = resample_ohlcv(m15, 'W')
    w1_rsi_bool = (rsi_calc(w1['close'], 14) > 50)
    w1_rsi_bool.index = pd.to_datetime(w1_rsi_bool.index).tz_localize(None)

    # W1 EMA10 > EMA20 (weekly trend)
    w1_ema_bool = (ema(w1['close'], 10) > ema(w1['close'], 20))
    w1_ema_bool.index = pd.to_datetime(w1_ema_bool.index).tz_localize(None)

    # 2H RSI (mid-ref between 1H and 4H)
    h2 = resample_ohlcv(m15, '2h')
    h2_rsi_bool = (rsi_calc(h2['close'], 14) > 50)
    h2_rsi_bool.index = pd.to_datetime(h2_rsi_bool.index).tz_localize(None)

    print("  Done\n")

    # Resample to 3H
    df3h = resample_ohlcv(m15, '3h')
    df3h.index = pd.to_datetime(df3h.index).tz_localize(None)
    n = len(df3h)
    idx = df3h.index

    bars_per_month = n / MONTHS
    print(f"3H bars: {n:,}  ({bars_per_month:.0f} bars/month)")

    # Precompute Numba cache
    cache = precompute(df3h, None)

    # Warm up JIT
    dummy_sig = np.zeros(n, dtype=np.int8)
    dummy_sig[50] = 1
    _bt(cache['op'], cache['hi'], cache['lo'], cache['atr14'],
        dummy_sig, 0.005, 0.015, 0.5, 2.0, 5, 2, cache['day_idx'])
    print("Numba warmed up\n")

    # Time filter
    time_ok = (idx.dayofweek < 5) & (idx.hour >= 3) & (idx.hour < 21)

    # Reference signals aligned to 3H
    h4_bull = ffill_to(h4_rsi_bool, idx).values
    d1_bull = ffill_to(d1_rsi_bool, idx).values
    d1_ema  = ffill_to(d1_ema_bool, idx).values
    w1_bull = ffill_to(w1_rsi_bool, idx).values
    w1_ema  = ffill_to(w1_ema_bool, idx).values
    h2_bull = ffill_to(h2_rsi_bool, idx).values

    em50_3h  = ema(df3h['close'], 50).values
    em200_3h = ema(df3h['close'], 200).values
    price_bull_3h = df3h['close'].values > em200_3h

    sig_arrays = {}

    # ── Signal family 1: Stoch crossover/level with W1+D1 alignment ──────────
    for k in [3, 5, 7]:
        sk   = stoch_k(df3h, k).fillna(50).values
        sk_p = np.roll(sk, 1); sk_p[0] = 50

        cross_lo  = (sk > 20) & (sk_p <= 20) & time_ok
        cross_sh  = (sk < 80) & (sk_p >= 80) & time_ok
        level_lo  = (sk < 30) & (sk_p >= 30) & time_ok
        level_sh  = (sk > 70) & (sk_p <= 70) & time_ok

        for sig_type, lo_base, sh_base in [
            ('cross', cross_lo, cross_sh),
            ('level', level_lo, level_sh),
        ]:
            # W1+D1 alignment (both weekly RSI and daily RSI bullish)
            lo_w1d1 = lo_base & w1_bull & d1_bull
            sig_arrays[f'sk{k}_{sig_type}_w1d1_LO'] = make_sig_array(
                lo_w1d1, np.zeros(n, bool), n)
            sig_arrays[f'sk{k}_{sig_type}_w1d1_bidir'] = make_sig_array(
                lo_w1d1, sh_base & ~w1_bull & ~d1_bull, n)

            # W1 only alignment (more signals, looser)
            lo_w1 = lo_base & w1_bull
            sig_arrays[f'sk{k}_{sig_type}_w1only_LO'] = make_sig_array(
                lo_w1, np.zeros(n, bool), n)
            sig_arrays[f'sk{k}_{sig_type}_w1only_bidir'] = make_sig_array(
                lo_w1, sh_base & ~w1_bull, n)

            # W1+D1 EMA alignment
            lo_w1ema = lo_base & w1_ema & d1_ema & price_bull_3h
            sig_arrays[f'sk{k}_{sig_type}_w1ema_LO'] = make_sig_array(
                lo_w1ema, np.zeros(n, bool), n)

            # W1+D1+4H triple filter (very selective, high WR)
            lo_triple = lo_base & w1_bull & d1_bull & h4_bull
            sig_arrays[f'sk{k}_{sig_type}_triple_LO'] = make_sig_array(
                lo_triple, np.zeros(n, bool), n)
            sig_arrays[f'sk{k}_{sig_type}_triple_bidir'] = make_sig_array(
                lo_triple, sh_base & ~w1_bull & ~d1_bull & ~h4_bull, n)

    # ── Signal family 2: EMA crossover on 3H + higher-TF alignment ───────────
    ema5  = ema(df3h['close'], 5).values
    ema13 = ema(df3h['close'], 13).values
    ema5_p  = np.roll(ema5, 1); ema5_p[0] = ema13[0]
    ema13_p = np.roll(ema13, 1); ema13_p[0] = ema13[0]

    ema_cross_lo = (ema5 > ema13) & (ema5_p <= ema13_p) & time_ok
    ema_cross_sh = (ema5 < ema13) & (ema5_p >= ema13_p) & time_ok

    # EMA cross + W1+D1
    lo_ema_w1d1 = ema_cross_lo & w1_bull & d1_bull
    sig_arrays['ema5x13_w1d1_LO']    = make_sig_array(lo_ema_w1d1, np.zeros(n, bool), n)
    sig_arrays['ema5x13_w1d1_bidir'] = make_sig_array(
        lo_ema_w1d1, ema_cross_sh & ~w1_bull & ~d1_bull, n)

    # EMA cross + W1 only
    lo_ema_w1 = ema_cross_lo & w1_bull
    sig_arrays['ema5x13_w1only_LO']    = make_sig_array(lo_ema_w1, np.zeros(n, bool), n)
    sig_arrays['ema5x13_w1only_bidir'] = make_sig_array(
        lo_ema_w1, ema_cross_sh & ~w1_bull, n)

    # EMA cross + triple
    lo_ema_triple = ema_cross_lo & w1_bull & d1_bull & h4_bull
    sig_arrays['ema5x13_triple_LO']    = make_sig_array(lo_ema_triple, np.zeros(n, bool), n)
    sig_arrays['ema5x13_triple_bidir'] = make_sig_array(
        lo_ema_triple, ema_cross_sh & ~w1_bull & ~d1_bull & ~h4_bull, n)

    # ── Signal family 3: RSI oversold rebound on 3H + W1+D1 ─────────────────
    rsi3h = rsi_calc(df3h['close'], 7).fillna(50).values
    rsi3h_p = np.roll(rsi3h, 1); rsi3h_p[0] = 50

    rsi_rebound_lo = (rsi3h > 30) & (rsi3h_p <= 30) & time_ok
    rsi_rebound_sh = (rsi3h < 70) & (rsi3h_p >= 70) & time_ok

    sig_arrays['rsi7_rebound_w1d1_LO']    = make_sig_array(
        rsi_rebound_lo & w1_bull & d1_bull, np.zeros(n, bool), n)
    sig_arrays['rsi7_rebound_w1d1_bidir'] = make_sig_array(
        rsi_rebound_lo & w1_bull & d1_bull,
        rsi_rebound_sh & ~w1_bull & ~d1_bull, n)
    sig_arrays['rsi7_rebound_w1only_LO']  = make_sig_array(
        rsi_rebound_lo & w1_bull, np.zeros(n, bool), n)

    # Print signal counts
    print(f"\n  3H signal counts ({len(sig_arrays)} total):")
    count_list = []
    for name, sig in sig_arrays.items():
        cnt = int((sig != 0).sum())
        tpm = cnt / MONTHS
        count_list.append((name, cnt, tpm))
    count_list.sort(key=lambda x: -x[1])
    for name, cnt, tpm in count_list[:10]:
        flag = '✓' if tpm >= OBJ_TPM else '✗'
        print(f"    {name:<45} {cnt:5d} = {tpm:5.1f} T/M  {flag}")
    print(f"  ... {len(sig_arrays)} total signals")

    # ── Sweep ─────────────────────────────────────────────────────────────────
    print()
    t0 = time.time()
    results = sweep(cache, sig_arrays)
    elapsed = time.time() - t0

    passing = []
    print(f"\n  Results (best combo per signal, then best passing alt):")
    for name, best, alts in results:
        if best is None:
            continue
        cnt = int((sig_arrays[name] != 0).sum())
        tpm_raw = cnt / MONTHS
        flag = '✅' if best['passed'] else ''
        print(f"    {name:<45} {cnt:4d} T/M={tpm_raw:5.1f}"
              f"  slm={best['slm']} tp={best['tp']} h={best['h']:<3d}"
              f"  rp={best['rp']}  M={best['m']:5.2f}%"
              f"  DD={best['dd']:7.2f}%  WR={best['wr']:5.1f}%  {flag}")
        # Show best passing alt if different from best
        if alts:
            a = alts[0]
            if (a['slm'] != best['slm'] or a['tp'] != best['tp'] or
                    a['h'] != best['h'] or a['rp'] != best['rp']):
                print(f"    └PASS {name:<40}"
                      f"  slm={a['slm']} tp={a['tp']} h={a['h']:<3d}"
                      f"  rp={a['rp']}  M={a['m']:5.2f}%  DD={a['dd']:7.2f}%  ✅")
            passing.append((name, a))
        elif best['passed']:
            passing.append((name, best))

    print(f"\n  Sweep: {elapsed:.1f}s  →  {len(passing)} passing combo(s)")

    if passing:
        print("\n" + "=" * 100)
        print("✅ 3H PASSING COMBOS")
        print("=" * 100)
        print(f"  {'Signal':<45} {'slm':>5} {'tp':>5} {'h':>5} {'rp':>7}   {'M%':>6} {'DD%':>8} {'T/M':>6} {'WR%':>6}")
        print("─" * 100)
        seen = set()
        for name, m in passing:
            key = (name, m['slm'], m['tp'], m['h'], m['rp'])
            if key in seen: continue
            seen.add(key)
            print(f"  {name:<45} {m['slm']:>5} {m['tp']:>5} {m['h']:>5} {m['rp']:>7}"
                  f"  {m['m']:>6.2f} {m['dd']:>8.2f} {m['tpm']:>6.1f} {m['wr']:>6.1f}  ✅")
    else:
        print("\n❌ No passing combos found for 3H with W1+D1 alignment.")
        print("   Next: Try EMA crossover or mean-reversion channel approach.")

if __name__ == '__main__':
    main()
