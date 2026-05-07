"""
MTF All-Timeframes Optimizer
============================
Apply Multi-TimeFrame trend alignment to all 7 TFs.
Key insight from M15: D1_RSI>50 + 4H_RSI>50 + stoch_cross achieves WR≈50%

For each TF, use 2 higher reference timeframes for trend alignment:
  M15 : 4H RSI + D1 RSI  → SOLVED ✅
  30M : 4H RSI + D1 RSI
  1H  : D1 RSI + W1 RSI
  2H  : D1 RSI + W1 RSI
  3H  : D1 RSI + W1 RSI
  4H  : D1 RSI + W1 RSI
  1D  : W1 RSI + Monthly RSI
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

# ── load M15 base data ───────────────────────────────────────────────────────
def load_m15(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

# ── pre-build reference TF signals (compute once from M15) ───────────────────
def build_ref_signals(m15):
    """Build higher-TF RSI bull signals, mapped to M15 timestamps."""
    ref = {}
    for rule, label in [('4h','h4'), ('D','d1'), ('W','w1'), ('ME','mn1')]:
        tf = resample_ohlcv(m15, rule)
        r  = rsi_calc(tf['close'], 14)
        bull = r > 50
        bull.index = pd.to_datetime(bull.index).tz_localize(None)
        ref[label] = bull
    # D1 EMA50 > EMA200
    d1 = resample_ohlcv(m15, 'D')
    em50  = ema(d1['close'], 50)
    em200 = ema(d1['close'], 200)
    d1_ema_bull = (em50 > em200)
    d1_ema_bull.index = pd.to_datetime(d1_ema_bull.index).tz_localize(None)
    ref['d1_ema'] = d1_ema_bull
    return ref

# ── build signals for a specific TF ─────────────────────────────────────────
def build_tf_signals(df_tf, ref, tf_label):
    """
    df_tf : OHLCV resampled to the target TF (or M15 if tf_label=='M15')
    ref   : dict of higher-TF RSI bool series (from M15 base)
    """
    n   = len(df_tf)
    idx = df_tf.index

    # ── M15-specific session filter ───────────────────────────────────────────
    if tf_label in ('M15', '30M'):
        hour_ok = (idx.hour >= 6) & (idx.hour < 20)  # London + NY
    elif tf_label in ('1H', '2H', '3H'):
        hour_ok = (idx.hour >= 6) & (idx.hour < 21)
    else:
        hour_ok = np.ones(n, dtype=bool)  # no hour filter for 4H+

    wday_ok  = (idx.dayofweek < 5)
    time_ok  = wday_ok & hour_ok

    # ── Entry triggers (on target TF) ────────────────────────────────────────
    sk   = stoch_k(df_tf, 14).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    rsi14 = rsi_calc(df_tf['close'], 14).fillna(50).values

    stoch_long  = (sk > 20)  & (sk_p <= 20) & time_ok
    stoch_short = (sk < 80)  & (sk_p >= 80) & time_ok

    em200_tf = ema(df_tf['close'], 200).values
    price_bull = df_tf['close'].values > em200_tf
    price_bear = df_tf['close'].values < em200_tf

    # ── Map reference signals to this TF ─────────────────────────────────────
    def get_ref(key):
        return ffill_to(ref[key], idx).values

    # RSI reference TFs by target TF
    if tf_label in ('M15', '30M'):
        ref1_bull = get_ref('h4')   # 4H RSI > 50
        ref2_bull = get_ref('d1')   # D1 RSI > 50
        ref3_bull = get_ref('d1_ema')  # D1 EMA50 > EMA200
    elif tf_label in ('1H', '2H', '3H'):
        ref1_bull = get_ref('d1')   # D1 RSI > 50
        ref2_bull = get_ref('w1')   # W1 RSI > 50
        ref3_bull = get_ref('d1_ema')
    elif tf_label == '4H':
        ref1_bull = get_ref('d1')
        ref2_bull = get_ref('w1')
        ref3_bull = get_ref('d1_ema')
    else:  # 1D
        ref1_bull = get_ref('w1')
        ref2_bull = get_ref('mn1')
        ref3_bull = get_ref('d1_ema')  # repurposed as "ema bull"

    sigs = {}

    # Sig A: ref1 + ref2 + stoch
    long_a  = stoch_long & ref1_bull & ref2_bull
    short_a = stoch_short & ~ref1_bull & ~ref2_bull
    sigs['rsirsi_LO']    = (long_a,  np.zeros(n, dtype=bool))
    sigs['rsirsi_bidir'] = (long_a,  short_a)

    # Sig B: ref3(EMA) + ref1 + stoch
    long_b  = stoch_long & ref3_bull & ref1_bull
    sigs['ema_rsi_LO'] = (long_b, np.zeros(n, dtype=bool))

    # Sig C: ref3 only + price > em200 + stoch
    long_c  = stoch_long & ref3_bull & price_bull
    sigs['ema_price_LO'] = (long_c, np.zeros(n, dtype=bool))

    # Sig D: all three + stoch
    long_d  = stoch_long & ref1_bull & ref2_bull & ref3_bull
    sigs['3align_LO'] = (long_d, np.zeros(n, dtype=bool))

    # Sig E: ref1+ref2 + price > em200 + stoch (most conservative)
    long_e  = stoch_long & ref1_bull & ref2_bull & price_bull
    sigs['rsirsi_em200_LO'] = (long_e, np.zeros(n, dtype=bool))

    return sigs

# ── Numba backtest sweep ─────────────────────────────────────────────────────
def sweep_tf(cache, sig_arrays, tf_label):
    SLMs  = [0.8, 1.0, 1.2, 1.5, 2.0, 2.5]
    TP_Rs = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    HOLDs = [4, 6, 8, 12, 16, 24, 32, 48, 64, 96]
    RPs   = [0.003, 0.005, 0.008, 0.010]

    all_passed = []
    best_overall = None; best_overall_score = -9999

    for sig_name, sig in sig_arrays.items():
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
                        if m['score'] > best_overall_score:
                            best_overall_score = m['score']
                            best_overall = (sig_name, slm, tp_r, hold, rp, m)
                        if m['passed'] and best_passed is None:
                            best_passed = (sig_name, slm, tp_r, hold, rp, m)
                            all_passed.append((tf_label, sig_name, slm, tp_r, hold, rp, m))

        if best_row:
            sn, sl, tp, hold, rp, m = best_row
            tag = '✅' if m['passed'] else ''
            print(f"    {sn:<22} slm={sl:<5} tp={tp:<5} h={hold:<4} rp={rp:.3f}"
                  f"  M={m['m']:>6.2f}%  DD={m['dd']:>7.2f}%"
                  f"  T/M={m['tpm']:>5.1f}  WR={m['wr']:>5.1f}%  {tag}")
        if best_passed and best_passed != best_row:
            sn, sl, tp, hold, rp, m = best_passed
            print(f"    └PASS {sn:<17} slm={sl:<5} tp={tp:<5} h={hold:<4} rp={rp:.3f}"
                  f"  M={m['m']:>6.2f}%  DD={m['dd']:>7.2f}%"
                  f"  T/M={m['tpm']:>5.1f}  WR={m['wr']:>5.1f}%  ✅")

    return all_passed, best_overall

# ── main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 90)
    print("MTF ALL-TF OPTIMIZER  (D1+4H RSI alignment pattern)")
    print("=" * 90)

    m15 = load_m15()
    print(f"M15 data: {len(m15):,} bars  {m15.index[0].date()} → {m15.index[-1].date()}\n")

    print("Building reference signals (4H / D1 / W1 / Monthly RSI)…")
    ref = build_ref_signals(m15)
    print("  Done\n")

    # Timeframes to test
    TF_RULES = {
        'M15': None,   # use m15 directly
        '30M': '30min',
        '1H' : '1h',
        '2H' : '2h',
        '3H' : '3h',
        '4H' : '4h',
        '1D' : 'D',
    }

    all_passed_global = []
    tf_best = {}

    for tf_label, rule in TF_RULES.items():
        print(f"{'─'*90}")
        print(f"TF: {tf_label}")

        # Resample
        if rule is None:
            df_tf = m15.copy()
        else:
            df_tf = resample_ohlcv(m15, rule)

        tf_months = len(df_tf) / {'M15': 4*24*21, '30M': 2*24*21,
                                   '1H': 24*21, '2H': 12*21,
                                   '3H': 8*21, '4H': 6*21,
                                   '1D': 21}[tf_label]
        # Just use the known constant
        months = MONTHS

        print(f"  Bars: {len(df_tf):,}   (≈{months:.0f} months)")

        # Precompute Numba cache
        cache = precompute(df_tf, None)

        # Warm up Numba on first TF
        if tf_label == 'M15':
            dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
            _bt(cache['op'][:600], cache['hi'][:600], cache['lo'][:600],
                cache['atr14'][:600], dummy, 0.005, 0.02, 1.5, 2.0, 3, 32,
                cache['day_idx'][:600])
            print("  Numba warmed up")

        # Build signals
        raw_sigs = build_tf_signals(df_tf, ref, tf_label)

        # Convert to signal arrays
        W = min(250, len(df_tf) // 4)
        sig_arrays = {}
        for name, (lc, sc) in raw_sigs.items():
            sig = np.zeros(cache['n'], dtype=np.int8)
            sig[W:] = np.where(lc[W:], 1, np.where(sc[W:], -1, 0))
            nt = int((sig != 0).sum())
            tpm = nt / months
            sig_arrays[name] = sig

        # Print signal counts
        print("  Signal counts:")
        for name, sig in sig_arrays.items():
            nt = int((sig != 0).sum()); tpm = nt/months
            ok = '✓' if tpm >= OBJ_TPM else '✗'
            print(f"    {name:<28} {nt:5d} = {tpm:5.1f} T/M {ok}")

        t0 = time.time()
        passed, best = sweep_tf(cache, sig_arrays, tf_label)
        print(f"  Sweep: {time.time()-t0:.1f}s  →  {len(passed)} passing combo(s)")

        all_passed_global.extend(passed)
        if best:
            tf_best[tf_label] = best

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"GLOBAL SUMMARY — PASSING COMBOS: {len(all_passed_global)}")
    print(f"{'='*90}")
    print(f"  {'TF':<6}{'Signal':<24}{'slm':<6}{'tp':<6}{'hold':<6}{'rp':<7}"
          f"{'M%':>7}{'DD%':>8}{'T/M':>6}{'WR%':>6}")
    print('─' * 90)
    for item in all_passed_global:
        tf, sn, sl, tp, hold, rp, m = item
        print(f"  {tf:<6}{sn:<24}{sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
              f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}  ✅")

    print(f"\nBest combo per TF (by score, regardless of pass):")
    print(f"  {'TF':<6}{'Signal':<24}{'slm':<6}{'tp':<6}{'hold':<6}{'rp':<7}"
          f"{'M%':>7}{'DD%':>8}{'T/M':>6}{'WR%':>6}")
    print('─' * 90)
    for tf_label in TF_RULES:
        if tf_label in tf_best:
            sn, sl, tp, hold, rp, m = tf_best[tf_label]
            tag = ' ✅' if m['passed'] else ''
            print(f"  {tf_label:<6}{sn:<24}{sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
                  f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}{tag}")

    # Progress
    tfs_passing = set(item[0] for item in all_passed_global)
    print(f"\nProgress: {len(tfs_passing)}/7 TFs passing")
    for tf in TF_RULES:
        status = '✅' if tf in tfs_passing else '❌'
        print(f"  {status} {tf}")

if __name__ == '__main__':
    main()
