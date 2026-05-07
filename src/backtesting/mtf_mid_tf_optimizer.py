"""
Mid-TF Optimizer: 1H, 2H, 3H, 4H — fix T/M problem via shorter stochastic periods
========================================================================
Root cause: stoch(14) generates only 2-4 T/M at 4H scale
Solution:   stoch(3/5/7) + D1+4H RSI alignment (same pattern that passed M15 and 30M)

1D is excluded here — handled by yfinance GVF V3 (already 11.73%/month ✅)
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

# ── build higher-TF reference signals (from M15 base) ────────────────────────
def build_ref_signals(m15):
    ref = {}
    # 4H RSI > 50
    h4 = resample_ohlcv(m15, '4h')
    h4_rsi = rsi_calc(h4['close'], 14)
    ref['h4_rsi'] = (h4_rsi > 50)
    ref['h4_rsi'].index = pd.to_datetime(ref['h4_rsi'].index).tz_localize(None)

    # D1 RSI > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_rsi = rsi_calc(d1['close'], 14)
    ref['d1_rsi'] = (d1_rsi > 50)
    ref['d1_rsi'].index = pd.to_datetime(ref['d1_rsi'].index).tz_localize(None)

    # D1 EMA50 > EMA200
    d1_em50  = ema(d1['close'], 50)
    d1_em200 = ema(d1['close'], 200)
    ref['d1_ema'] = (d1_em50 > d1_em200)
    ref['d1_ema'].index = pd.to_datetime(ref['d1_ema'].index).tz_localize(None)

    # W1 RSI > 50
    w1 = resample_ohlcv(m15, 'W')
    w1_rsi = rsi_calc(w1['close'], 14)
    ref['w1_rsi'] = (w1_rsi > 50)
    ref['w1_rsi'].index = pd.to_datetime(ref['w1_rsi'].index).tz_localize(None)

    return ref


# ── build signals for a target TF ────────────────────────────────────────────
def build_signals(df_tf, ref, tf_label, stoch_periods):
    n   = len(df_tf)
    idx = df_tf.index

    # Hour filter (London + NY)
    if tf_label == '1H':
        time_ok = (idx.dayofweek < 5) & (idx.hour >= 6) & (idx.hour < 20)
    elif tf_label in ('2H', '3H'):
        time_ok = (idx.dayofweek < 5) & (idx.hour >= 4) & (idx.hour < 21)
    else:
        time_ok = (idx.dayofweek < 5)

    # Map reference signals to this TF
    def get_ref(key):
        return ffill_to(ref[key], idx).values

    h4_bull = get_ref('h4_rsi')
    d1_bull = get_ref('d1_rsi')
    d1_ema  = get_ref('d1_ema')
    w1_bull = get_ref('w1_rsi')

    em200  = ema(df_tf['close'], 200).values
    price_bull = df_tf['close'].values > em200

    sigs = {}

    for k in stoch_periods:
        sk   = stoch_k(df_tf, k).fillna(50).values
        sk_p = np.roll(sk, 1); sk_p[0] = 50

        # Crossover signals
        cross_long  = (sk > 20) & (sk_p <= 20) & time_ok
        cross_short = (sk < 80) & (sk_p >= 80) & time_ok

        # Level signals (first bar entering oversold zone)
        level_long  = (sk < 30) & (sk_p >= 30) & time_ok  # entering oversold
        level_short = (sk > 70) & (sk_p <= 70) & time_ok  # entering overbought

        for sig_type, long_c, short_c in [
            ('cross', cross_long, cross_short),
            ('level', level_long, level_short),
        ]:
            # D1+4H RSI alignment (winner pattern for M15/30M)
            lo = long_c & h4_bull & d1_bull
            sigs[f'sk{k}_{sig_type}_h4d1_LO']    = (lo, np.zeros(n, dtype=bool))
            bidir = lo | (short_c & ~h4_bull & ~d1_bull)
            sigs[f'sk{k}_{sig_type}_h4d1_bidir']  = (lo, short_c & ~h4_bull & ~d1_bull)

            # D1+EMA alignment
            lo_ema = long_c & d1_ema & price_bull
            sigs[f'sk{k}_{sig_type}_d1ema_LO']    = (lo_ema, np.zeros(n, dtype=bool))

            # D1 only (more signals)
            lo_d1 = long_c & d1_bull
            sigs[f'sk{k}_{sig_type}_d1only_LO']   = (lo_d1, np.zeros(n, dtype=bool))

    return sigs


def make_sig_array(long_c, short_c, n, warmup=100):
    sig = np.zeros(n, dtype=np.int8)
    warmup = min(warmup, n // 4)
    sig[warmup:] = np.where(long_c[warmup:], 1, np.where(short_c[warmup:], -1, 0))
    return sig


# ── sweep ────────────────────────────────────────────────────────────────────
def sweep_tf(cache, sig_arrays):
    SLMs  = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0]
    TP_Rs = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    HOLDs = [2, 4, 6, 8, 12, 16, 24, 32, 48, 64]
    RPs   = [0.003, 0.005, 0.008, 0.010]

    all_passed   = []
    global_best  = {}   # key → (score, row)

    for sig_name, sig in sig_arrays.items():
        nt  = int((sig != 0).sum())
        tpm = nt / MONTHS

        best_score = -9999; best_row = None; best_passed = None

        for slm in SLMs:
            for tp_r in TP_Rs:
                for hold in HOLDs:
                    for rp in RPs:
                        bt  = _bt(cache['op'], cache['hi'], cache['lo'],
                                   cache['atr14'], sig, rp, 0.015, slm, tp_r,
                                   5, hold, cache['day_idx'])
                        pnl = bt[1][:bt[2]]; eq = bt[0]
                        m   = mets(pnl, eq)
                        if m['n'] < 5:
                            continue
                        if m['score'] > best_score:
                            best_score = m['score']
                            best_row   = (sig_name, slm, tp_r, hold, rp, m)
                        if m['passed'] and best_passed is None:
                            best_passed = (sig_name, slm, tp_r, hold, rp, m)
                            all_passed.append((sig_name, slm, tp_r, hold, rp, m))

        if best_row:
            sn, sl, tp, hold, rp, m = best_row
            tag = '✅' if m['passed'] else ''
            print(f"    {sn:<34} {nt:5d} T/M={nt/MONTHS:5.1f}  "
                  f"slm={sl:.1f} tp={tp:.1f} h={hold:<3} rp={rp:.3f}  "
                  f"M={m['m']:>5.2f}%  DD={m['dd']:>7.2f}%  "
                  f"WR={m['wr']:>5.1f}%  {tag}")
        if best_passed and best_passed is not best_row:
            sn, sl, tp, hold, rp, m = best_passed
            print(f"    └PASS {sn:<28} "
                  f"slm={sl:.1f} tp={tp:.1f} h={hold:<3} rp={rp:.3f}  "
                  f"M={m['m']:>5.2f}%  DD={m['dd']:>7.2f}%  ✅")

    return all_passed


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 100)
    print("MID-TF OPTIMIZER: 1H / 2H / 3H / 4H")
    print("Strategy: shorter stochastic (k=3,5,7,14) + D1+4H RSI alignment")
    print("=" * 100)

    m15 = load_m15()
    print(f"M15 data: {len(m15):,} bars  {m15.index[0].date()} → {m15.index[-1].date()}\n")

    print("Building reference signals…")
    ref = build_ref_signals(m15)
    print("  Done\n")

    TF_RULES = {
        '1H' : ('1h',  [3, 5, 7, 14]),
        '2H' : ('2h',  [3, 5, 7, 14]),
        '3H' : ('3h',  [3, 5, 7, 14]),
        '4H' : ('4h',  [3, 5, 7, 14]),
    }

    all_passed_global = []
    tf_best = {}

    # Warm up Numba once
    cache_m15 = precompute(m15, None)
    dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache_m15['op'][:600], cache_m15['hi'][:600], cache_m15['lo'][:600],
        cache_m15['atr14'][:600], dummy, 0.005, 0.02, 1.5, 2.0, 3, 32,
        cache_m15['day_idx'][:600])
    print("Numba warmed up\n")

    for tf_label, (rule, stoch_periods) in TF_RULES.items():
        print(f"{'─'*100}")
        print(f"TF: {tf_label}")

        df_tf  = resample_ohlcv(m15, rule)
        cache  = precompute(df_tf, None)
        print(f"  Bars: {len(df_tf):,}")

        raw_sigs = build_signals(df_tf, ref, tf_label, stoch_periods)

        # Print signal counts summary
        print("  Top signal counts:")
        sig_arrays = {}
        counts = []
        for name, (lc, sc) in raw_sigs.items():
            sig = make_sig_array(lc, sc, cache['n'])
            sig_arrays[name] = sig
            nt  = int((sig != 0).sum())
            counts.append((nt, name))
        counts.sort(reverse=True)
        for nt, name in counts[:6]:
            ok = '✓' if nt/MONTHS >= OBJ_TPM else '✗'
            print(f"    {name:<36} {nt:5d} = {nt/MONTHS:5.1f} T/M  {ok}")
        print(f"  ... {len(counts)} total signals")

        t0 = time.time()
        passed = sweep_tf(cache, sig_arrays)
        elapsed = time.time() - t0

        print(f"  Sweep: {elapsed:.1f}s  →  {len(passed)} passing combo(s)\n")
        all_passed_global.extend([(tf_label,) + p for p in passed])

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*100}")
    print(f"GLOBAL SUMMARY — PASSING COMBOS: {len(all_passed_global)}")
    print(f"{'='*100}")
    if all_passed_global:
        print(f"  {'TF':<5}{'Signal':<36}{'slm':<5}{'tp':<5}{'h':<5}{'rp':<7}"
              f"{'M%':>6}{'DD%':>8}{'T/M':>6}{'WR%':>6}")
        print('─' * 100)
        for item in all_passed_global:
            tf, sn, sl, tp, hold, rp, m = item
            print(f"  {tf:<5}{sn:<36}{sl:<5}{tp:<5}{hold:<5}{rp:<7.3f}"
                  f"{m['m']:>6.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}  ✅")

    tfs_passing = set(item[0] for item in all_passed_global)
    print(f"\nProgress on mid-TFs: {len(tfs_passing)}/4")
    for tf in ['1H', '2H', '3H', '4H']:
        status = '✅' if tf in tfs_passing else '❌'
        print(f"  {status} {tf}")

    print("\nNote: 1D is handled separately via yfinance GVF V3 (11.73%/month ✅)")


if __name__ == '__main__':
    main()
