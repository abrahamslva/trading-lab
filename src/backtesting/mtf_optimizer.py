"""
Multi-TimeFrame (MTF) Trend Alignment Optimizer
================================================
Strategy: Only take M15 long entries when ALL of:
  - Daily   : EMA50 > EMA200  (macro bull trend)
  - 4H      : EMA20 > EMA50   (intermediate trend)
  - 1H      : RSI14 > 50      (medium momentum)
  - M15     : Stoch(%K) crosses up from <20 oversold  (entry trigger)

Classic "buy the dip in an established uptrend" — expected WR: 55-70%
Short side: All inverted when macro is bearish.
"""

import sys, time
import numpy as np
import pandas as pd
import numba
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

MONTHS  = 123.6
INITIAL = 100_000.0
OBJ_M, OBJ_DD, OBJ_TPM, OBJ_WD = 2.0, -7.0, 7.0, -3.0

# ─── helpers ────────────────────────────────────────────────────────────────
def ema(s, n): return s.ewm(n, adjust=False).mean()
def sma(s, n): return s.rolling(n).mean()

def rsi(s, n=14):
    d  = s.diff()
    up = d.clip(lower=0).ewm(n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(n, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))

def stoch_k(d, k=14):
    lk = d['low'].rolling(k).min()
    hk = d['high'].rolling(k).max()
    return (d['close'] - lk) / (hk - lk + 1e-12) * 100

def atr14(d):
    tr = pd.concat([
        d['high'] - d['low'],
        (d['high'] - d['close'].shift()).abs(),
        (d['low']  - d['close'].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(14, adjust=False).mean()


# ─── load & prepare data ─────────────────────────────────────────────────────
def load_data(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df


def build_mtf_signals(df):
    """Build multi-timeframe trend alignment signals, mapped back to M15."""
    n = len(df)

    # ── 1D resample ──────────────────────────────────────────────────────────
    d1 = df.resample('D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    d1_em50  = ema(d1['close'], 50)
    d1_em200 = ema(d1['close'], 200)
    d1_bull  = (d1_em50 > d1_em200)
    d1_rsi   = rsi(d1['close'], 14)
    d1_rsi_bull = d1_rsi > 50

    # ── 4H resample ──────────────────────────────────────────────────────────
    h4 = df.resample('4h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    h4_em20 = ema(h4['close'], 20)
    h4_em50 = ema(h4['close'], 50)
    h4_bull = (h4_em20 > h4_em50)
    h4_rsi  = rsi(h4['close'], 14)
    h4_rsi_bull = h4_rsi > 50

    # ── 1H resample ──────────────────────────────────────────────────────────
    h1 = df.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    h1_rsi  = rsi(h1['close'], 14)
    h1_em20 = ema(h1['close'], 20)
    h1_em50 = ema(h1['close'], 50)
    h1_bull     = h1_em20 > h1_em50
    h1_rsi_bull = h1_rsi > 50

    # ── Map higher-TF signals to M15 (forward-fill) ───────────────────────────
    def ffill_to_m15(series):
        s = series.copy()
        s.index = pd.to_datetime(s.index).tz_localize(None) if s.index.tz else s.index
        return s.reindex(df.index, method='ffill').fillna(False).values

    m15_d1_bull     = ffill_to_m15(d1_bull)
    m15_d1_rsi_bull = ffill_to_m15(d1_rsi_bull)
    m15_h4_bull     = ffill_to_m15(h4_bull)
    m15_h4_rsi_bull = ffill_to_m15(h4_rsi_bull)
    m15_h1_bull     = ffill_to_m15(h1_bull)
    m15_h1_rsi_bull = ffill_to_m15(h1_rsi_bull)

    # ── M15 entry triggers ────────────────────────────────────────────────────
    sk   = stoch_k(df, 14).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50

    rsi14 = rsi(df['close'], 14).fillna(50).values
    rsi_p = np.roll(rsi14, 1); rsi_p[0] = 50

    em200_m15 = ema(df['close'], 200).values
    em50_m15  = ema(df['close'], 50).values

    wday_ok = (df.index.dayofweek < 5)
    # Session filter: London + NY (6:00-20:00 UTC)
    hour_ok = (df.index.hour >= 6) & (df.index.hour < 20)
    time_ok = wday_ok & hour_ok

    # Stochastic oversold cross-up
    stoch_long  = (sk > 20)  & (sk_p <= 20)
    stoch_short = (sk < 80)  & (sk_p >= 80)

    # RSI cross-40 (less restrictive entry)
    rsi_long  = (rsi14 > 40) & (rsi_p <= 40)
    rsi_short = (rsi14 < 60) & (rsi_p >= 60)

    # Price above M15 EMA200
    price_bull = df['close'].values > em200_m15
    price_bear = df['close'].values < em200_m15

    # ── Build composite signals ────────────────────────────────────────────────
    signals = {}

    # 1. Full MTF: D1+4H+1H alignment + stoch entry
    full_long  = stoch_long  & m15_d1_bull & m15_h4_bull & m15_h1_bull & time_ok
    full_short = stoch_short & ~m15_d1_bull & ~m15_h4_bull & ~m15_h1_bull & time_ok
    signals['MTF_full_bidir'] = (full_long, full_short)

    # 2. D1+4H alignment only (less restrictive)
    d1h4_long  = stoch_long  & m15_d1_bull & m15_h4_bull & time_ok
    d1h4_short = stoch_short & ~m15_d1_bull & ~m15_h4_bull & time_ok
    signals['MTF_d1h4_bidir'] = (d1h4_long, d1h4_short)

    # 3. Long-only: D1 bull + 4H bull + stoch oversold
    lo_long = stoch_long & m15_d1_bull & m15_h4_bull & time_ok
    signals['MTF_d1h4_LO'] = (lo_long, np.zeros(n, dtype=bool))

    # 4. D1 bull + 4H RSI > 50 + M15 stoch
    lo_h4rsi = stoch_long & m15_d1_bull & m15_h4_rsi_bull & time_ok
    signals['MTF_d1_h4rsi_LO'] = (lo_h4rsi, np.zeros(n, dtype=bool))

    # 5. D1 + 1H alignment + stoch (skip 4H)
    d1h1_long = stoch_long & m15_d1_bull & m15_h1_bull & time_ok
    signals['MTF_d1h1_LO'] = (d1h1_long, np.zeros(n, dtype=bool))

    # 6. RSI entry instead of stoch
    rsi_mtf_long = rsi_long & m15_d1_bull & m15_h4_bull & time_ok
    signals['MTF_rsi_d1h4_LO'] = (rsi_mtf_long, np.zeros(n, dtype=bool))

    # 7. D1 only filter + M15 EMA200 + stoch
    d1_ema_long  = stoch_long  & m15_d1_bull & price_bull & time_ok
    d1_ema_short = stoch_short & ~m15_d1_bull & price_bear & time_ok
    signals['MTF_d1_ema_bidir'] = (d1_ema_long, d1_ema_short)

    # 8. 4H bull + M15 price > ema200 + stoch (no D1 required)
    h4_ema_long = stoch_long & m15_h4_bull & price_bull & time_ok
    signals['MTF_h4_ema_LO'] = (h4_ema_long, np.zeros(n, dtype=bool))

    # 9. D1 RSI > 50 + 4H RSI > 50 + stoch
    rsi_rsi_long = stoch_long & m15_d1_rsi_bull & m15_h4_rsi_bull & time_ok
    signals['MTF_rsirsi_LO'] = (rsi_rsi_long, np.zeros(n, dtype=bool))

    # 10. Three RSI alignment
    three_rsi = stoch_long & m15_d1_rsi_bull & m15_h4_rsi_bull & m15_h1_rsi_bull & time_ok
    signals['MTF_3rsi_LO'] = (three_rsi, np.zeros(n, dtype=bool))

    return signals


def make_sig_array(long_c, short_c, n, warmup=250):
    sig = np.zeros(n, dtype=np.int8)
    sig[warmup:] = np.where(long_c[warmup:], 1,
                   np.where(short_c[warmup:], -1, 0))
    return sig


# ─── sweep ───────────────────────────────────────────────────────────────────
def sweep(cache, signals, sig_arrays):
    SLMs  = [0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
    TP_Rs = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    HOLDs = [8, 12, 16, 24, 32, 48, 64, 96]
    RPs   = [0.003, 0.005, 0.008, 0.010, 0.012]

    print(f"\n{'Signal':<24}{'slm':<6}{'tp':<6}{'hold':<6}{'rp':<7}"
          f"{'M%':>7}{'DD%':>8}{'T/M':>6}{'WR%':>6}{'WD%':>7}  pass")
    print('─' * 90)

    all_passed = []

    for sig_name, sig in sig_arrays.items():
        nt = int((sig != 0).sum())
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
                            best_row   = (slm, tp_r, hold, rp, m)
                        if m['passed'] and best_passed is None:
                            best_passed = (slm, tp_r, hold, rp, m)
                            all_passed.append((sig_name, slm, tp_r, hold, rp, m))

        if best_row:
            sl, tp, hold, rp, m = best_row
            tag = '✅' if m['passed'] else ''
            print(f"  {sig_name:<22} {sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
                  f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}"
                  f"{m['wr']:>6.1f}{m['wd']:>7.2f}  {tag}")
        else:
            print(f"  {sig_name:<22} no trades (T/M={tpm:.1f})")

        if best_passed and id(best_passed) != id(best_row):
            sl, tp, hold, rp, m = best_passed
            print(f"  └─PASS {sig_name:<16} {sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
                  f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}"
                  f"{m['wr']:>6.1f}{m['wd']:>7.2f}  ✅")

    return all_passed


# ─── main ────────────────────────────────────────────────────────────────────
def main():
    print("Loading M15 data…")
    df = load_data()
    print(f"  {len(df):,} bars  {df.index[0].date()} → {df.index[-1].date()}")

    print("Precomputing cache & warming Numba…")
    cache = precompute(df, None)
    dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache['op'][:600], cache['hi'][:600], cache['lo'][:600],
        cache['atr14'][:600], dummy, 0.005, 0.02, 1.5, 2.0, 3, 32,
        cache['day_idx'][:600])
    print("  Numba ready")

    print("Building MTF signals (resample 4H/1H/D)…")
    t0 = time.time()
    raw_signals = build_mtf_signals(df)
    print(f"  Done in {time.time()-t0:.2f}s")

    print("\nSignal trade counts:")
    sig_arrays = {}
    for name, (lc, sc) in raw_signals.items():
        sig = make_sig_array(lc, sc, cache['n'])
        sig_arrays[name] = sig
        nt = int((sig != 0).sum())
        print(f"  {name:<28} {nt:5d} signals = {nt/MONTHS:5.1f} T/M")

    t1 = time.time()
    passed = sweep(cache, raw_signals, sig_arrays)
    print(f"\nSweep time: {time.time()-t1:.1f}s")

    print(f"\n{'='*90}")
    print(f"PASSING COMBOS: {len(passed)}")
    for item in passed:
        sn, sl, tp, hold, rp, m = item
        print(f"  {sn}: slm={sl} tp={tp} hold={hold} rp={rp}"
              f" → M={m['m']:.2f}% DD={m['dd']:.2f}% T/M={m['tpm']:.1f}"
              f" WR={m['wr']:.1f}% WD={m['wd']:.2f}%")

    # ── Top-5 by score across all signals ─────────────────────────────────────
    print("\nTop combos across all signals (by score, any):")
    all_results = []
    for sig_name, sig in sig_arrays.items():
        for slm in [0.8,1.0,1.2,1.5,2.0]:
            for tp_r in [2.0,2.5,3.0,4.0,5.0]:
                for hold in [12,16,24,32,48]:
                    for rp in [0.005,0.008,0.010]:
                        bt  = _bt(cache['op'], cache['hi'], cache['lo'],
                                   cache['atr14'], sig, rp, 0.015, slm, tp_r,
                                   5, hold, cache['day_idx'])
                        pnl = bt[1][:bt[2]]; eq = bt[0]
                        m   = mets(pnl, eq)
                        if m['n'] >= 5:
                            all_results.append((m['score'], sig_name, slm, tp_r, hold, rp, m))

    all_results.sort(reverse=True)
    print(f"{'Signal':<24}{'slm':<6}{'tp':<6}{'hold':<6}{'rp':<7}"
          f"{'M%':>7}{'DD%':>8}{'T/M':>6}{'WR%':>6}")
    for score, sn, sl, tp, hold, rp, m in all_results[:20]:
        tag = ' ✅' if m['passed'] else ''
        print(f"  {sn:<22} {sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
              f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}{tag}")


if __name__ == '__main__':
    main()
