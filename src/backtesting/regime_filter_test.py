"""Test monthly/weekly regime filters + VWAP mean reversion on M15 stoch_cross baseline."""
import sys, numpy as np, pandas as pd, warnings
sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets
warnings.filterwarnings('ignore')

MONTHS = 123.6
OBJ_M, OBJ_DD, OBJ_TPM, OBJ_WD = 2.0, -7.0, 7.0, -3.0

# ── Load data ──────────────────────────────────────────────────────────────
df = pd.read_parquet('data/dukascopy/XAUUSD_15min_mt5.parquet')
df.index = pd.to_datetime(df.index)
df.columns = [c.lower() for c in df.columns]
# Normalize to tz-naive UTC
if df.index.tz is not None:
    df.index = df.index.tz_convert('UTC').tz_localize(None)
print(f"Loaded {len(df):,} M15 bars  {df.index[0].date()} → {df.index[-1].date()}")

# ── Numba warm-up ──────────────────────────────────────────────────────────
cache15 = precompute(df, None)
dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
_bt(cache15['op'][:600], cache15['hi'][:600], cache15['lo'][:600],
    cache15['atr14'][:600], dummy, 0.005, 0.02, 1.5, 2.0, 3, 32,
    cache15['day_idx'][:600])
print("Numba warmed up")

# ── Helpers ────────────────────────────────────────────────────────────────
def ema(s, n): return s.ewm(n, adjust=False).mean()

def stoch_k(d, k=14):
    lk = d['low'].rolling(k).min()
    hk = d['high'].rolling(k).max()
    return (d['close'] - lk) / (hk - lk + 1e-12) * 100

# ── Base signals ───────────────────────────────────────────────────────────
sk14   = stoch_k(df, 14).fillna(50).values
sk_p   = np.roll(sk14, 1); sk_p[0] = 50
em200  = ema(df['close'], 200).values
bull_ema = df['close'].values > em200
wday_ok  = (df.index.dayofweek < 5)          # already numpy bool array

long_raw  = (sk14 > 20) & (sk_p <= 20) & bull_ema & wday_ok
short_raw = (sk14 < 80) & (sk_p >= 80) & (~bull_ema) & wday_ok

# ── Monthly SMA-10 filter ──────────────────────────────────────────────────
monthly = df.resample('ME').agg({'close': 'last'}).dropna()
monthly['sma10'] = monthly['close'].rolling(10).mean()
monthly['bull']  = (monthly['close'] > monthly['sma10'])
# forward-fill monthly bull to each M15 bar
monthly.index = pd.to_datetime(monthly.index).tz_localize(None)
m15_mf = monthly['bull'].reindex(df.index, method='ffill').fillna(False).values
print(f"Monthly SMA10 bull: {m15_mf.mean()*100:.1f}% of M15 bars")

# ── Weekly EMA-20 > EMA-50 filter ─────────────────────────────────────────
weekly = df.resample('W').agg({'close': 'last'}).dropna()
weekly['em20'] = ema(weekly['close'], 20)
weekly['em50'] = ema(weekly['close'], 50)
weekly['bull'] = weekly['em20'] > weekly['em50']
weekly.index = pd.to_datetime(weekly.index).tz_localize(None)
m15_wf = weekly['bull'].reindex(df.index, method='ffill').fillna(False).values
print(f"Weekly EMA20>50 bull: {m15_wf.mean()*100:.1f}% of M15 bars")

# ── Daily VWAP deviation signal ────────────────────────────────────────────
tp     = (df['high'] + df['low'] + df['close']) / 3
tpv    = tp * df['volume']
dg     = df.index.floor('D')
vwap   = tpv.groupby(dg).cumsum() / df['volume'].groupby(dg).cumsum()
dev    = (df['close'] - vwap)
vstd   = dev.rolling(20).std()
long_vwap  = (dev < -1.5 * vstd).values & bull_ema & wday_ok
short_vwap = (dev >  1.5 * vstd).values & (~bull_ema) & wday_ok

# ── Build signal arrays ────────────────────────────────────────────────────
W = 250  # warmup

def make_sig(long_cond, short_cond):
    sig = np.zeros(cache15['n'], dtype=np.int8)
    sig[W:] = np.where(long_cond[W:], 1, np.where(short_cond[W:], -1, 0))
    return sig

signals = {
    'Baseline_bidir':    make_sig(long_raw, short_raw),
    'Baseline_LO':       make_sig(long_raw, np.zeros(cache15['n'], dtype=bool)),
    'Monthly_bidir':     make_sig(long_raw & m15_mf, short_raw & ~m15_mf),
    'Monthly_LO':        make_sig(long_raw & m15_mf, np.zeros(cache15['n'], dtype=bool)),
    'Weekly_bidir':      make_sig(long_raw & m15_wf, short_raw & ~m15_wf),
    'Weekly_LO':         make_sig(long_raw & m15_wf, np.zeros(cache15['n'], dtype=bool)),
    'Both_LO':           make_sig(long_raw & m15_mf & m15_wf, np.zeros(cache15['n'], dtype=bool)),
    'VWAP_bidir':        make_sig(long_vwap, short_vwap),
    'VWAP_LO':           make_sig(long_vwap, np.zeros(cache15['n'], dtype=bool)),
    'VWAP_mf_LO':        make_sig(long_vwap & m15_mf, np.zeros(cache15['n'], dtype=bool)),
}

print(f"\n{'Signal':<20} {'Trades':>7} {'T/M':>6}")
for name, sig in signals.items():
    n = int((sig != 0).sum())
    print(f"  {name:<20} {n:>7} {n/MONTHS:>6.1f}")

# ── Sweep params ───────────────────────────────────────────────────────────
SLMs  = [1.0, 1.2, 1.5, 2.0, 2.5, 3.0]
TP_Rs = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
HOLDs = [12, 16, 24, 32, 48, 64, 96]
RPs   = [0.003, 0.005, 0.008, 0.010]

print(f"\n{'Signal':<22}{'slm':<6}{'tp':<6}{'hold':<6}{'rp':<7}{'M%':>7}{'DD%':>8}{'T/M':>6}{'WR%':>6}{'pass'}")
print('─' * 85)

all_passed = []

for sig_name, sig in signals.items():
    best_score = -9999; best_row = None; best_passed = None

    for slm in SLMs:
        for tp_r in TP_Rs:
            for hold in HOLDs:
                for rp in RPs:
                    bt  = _bt(cache15['op'], cache15['hi'], cache15['lo'],
                               cache15['atr14'], sig, rp, 0.015, slm, tp_r,
                               5, hold, cache15['day_idx'])
                    pnl = bt[1][:bt[2]]; eq = bt[0]
                    m   = mets(pnl, eq)
                    if m['n'] < 10:
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
        print(f"  {sig_name:<20} {sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
              f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}  {tag}")
    if best_passed and best_passed != best_row:
        sl, tp, hold, rp, m = best_passed
        print(f"  └─PASS {sig_name:<14} {sl:<6}{tp:<6}{hold:<6}{rp:<7.3f}"
              f"{m['m']:>7.2f}{m['dd']:>8.2f}{m['tpm']:>6.1f}{m['wr']:>6.1f}  ✅")

# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n{'='*85}")
print(f"PASSING COMBOS FOUND: {len(all_passed)}")
for item in all_passed:
    sig_name, sl, tp, hold, rp, m = item
    print(f"  {sig_name}: slm={sl} tp={tp} hold={hold} rp={rp} "
          f"→ M={m['m']:.2f}% DD={m['dd']:.2f}% T/M={m['tpm']:.1f} WR={m['wr']:.1f}%")
