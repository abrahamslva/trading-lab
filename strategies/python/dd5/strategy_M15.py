"""
ESTRATEGIA ESTRATEGIA DD5% — M15 (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(14) cruzando sobrevendido + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.3 × ATR14 | tp=5.0 × ATR14 | hold=12 barras | rp=0.2%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +4.92%
  Max Drawdown    : -4.52%
  Trades/mes      : 33.3
  Win Rate        : 29.9%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +4.92%  (mediana: +4.80%)
    Desviación estándar      : 3.62%
    Mejor mes                : +18.27%  |  Peor mes: -2.60%
    Max DD mensual promedio  : -1.57%  |  Peor DD mes: -4.13%
    Trades/mes promedio      : 32.9
    Win Rate promedio        : 30.1%
    Peor día promedio        : -0.74%
    Meses positivos          : 117/125 (94%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +4.54%     -1.66%    31.8   29.9%   12    0
    2017      +3.50%     -1.52%    27.9   28.0%   12    0
    2018      +3.34%     -1.85%    28.6   26.8%    9    3
    2019      +5.33%     -1.33%    29.2   33.8%   11    1
    2020      +4.67%     -1.24%    28.3   31.4%   11    1
    2021      +4.83%     -1.32%    31.4   30.8%   11    1
    2022      +6.41%     -1.40%    32.3   34.3%   12    0
    2023      +4.95%     -1.47%    31.1   31.1%   11    1
    2024      +4.26%     -1.83%    39.4   25.9%   12    0
    2025      +7.01%     -2.04%    48.2   29.8%   11    1
    2026      +5.82%     -1.55%    35.6   29.0%    5    0

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +5.25%   -1.59%      26  34.6%   -0.60% $    6,089,386  ✓
    2023-07    +5.63%   -1.00%      21  38.1%   -0.60% $    6,431,985  ✓
    2023-08    +1.89%   -2.38%      42  21.4%   -0.60% $    6,553,839  ✓
    2023-09    +6.06%   -1.19%      31  35.5%   -0.60% $    6,951,095  ✓
    2023-10    +8.25%   -1.59%      38  34.2%   -0.80% $    7,524,794  ✓
    2023-11    +1.92%   -2.05%      31  22.6%   -0.80% $    7,668,928  ✓
    2023-12    +2.59%   -1.39%      29  24.1%   -0.60% $    7,867,852  ✓
    2024-01    +4.17%   -1.19%      31  29.0%   -0.40% $    8,195,970  ✓
    2024-02    +0.57%   -1.79%      27  18.5%   -1.00% $    8,242,883  ✓
    2024-03    +4.73%   -0.80%      25  36.0%   -0.40% $    8,632,663  ✓
    2024-04    +4.87%   -1.39%      40  27.5%   -1.00% $    9,053,004  ✓
    2024-05    +0.46%   -3.15%      37  18.9%   -1.00% $    9,094,494  ✓
    2024-06    +0.77%   -2.38%      32  18.8%   -1.00% $    9,164,333  ✓
    2024-07    +8.54%   -1.59%      51  31.4%   -1.00% $    9,946,779  ✓
    2024-08    +7.69%   -1.00%      51  29.4%   -0.80% $   10,711,441  ✓
    2024-09    +5.05%   -1.39%      53  24.5%   -1.00% $   11,252,458  ✓
    2024-10   +12.20%   -1.79%      47  38.3%   -1.00% $   12,624,833  ✓
    2024-11    +1.98%   -3.15%      32  21.9%   -1.00% $   12,874,750  ✓
    2024-12    +0.15%   -2.39%      47  17.0%   -1.00% $   12,894,393  ✓
    2025-01    +9.18%   -1.98%      62  29.0%   -1.00% $   14,077,856  ✓
    2025-02   +10.39%   -1.79%      44  38.6%   -1.00% $   15,540,342  ✓
    2025-03   +10.82%   -1.19%      40  40.0%   -0.60% $   17,221,545  ✓
    2025-04    +4.65%   -2.18%      48  25.0%   -1.00% $   18,022,600  ✓
    2025-05    -2.60%   -4.13%      40  12.5%   -1.00% $   17,553,980  ✗
    2025-06    +4.80%   -2.18%      44  27.3%   -0.60% $   18,396,183  ✓
    2025-07    +2.35%   -2.18%      52  21.2%   -1.00% $   18,827,952  ✓
    2025-08   +18.27%   -2.37%      52  46.2%   -1.00% $   22,267,106  ✓
    2025-09    +2.20%   -2.35%      47  23.4%   -0.80% $   22,757,788  ✓
    2025-10   +10.20%   -1.19%      47  34.0%   -1.00% $   25,079,497  ✓
    2025-11    +5.38%   -1.39%      41  29.3%   -1.00% $   26,427,532  ✓
    2025-12    +8.45%   -1.59%      61  31.1%   -1.00% $   28,659,367  ✓
    2026-01   +16.99%   -1.39%      47  44.7%   -0.80% $   33,528,144  ✓
    2026-02    +6.11%   -1.39%      48  27.1%   -0.60% $   35,575,935  ✓
    2026-03    +3.41%   -2.37%      37  24.3%   -1.00% $   36,787,802  ✓
    2026-04    +1.60%   -1.98%      39  20.5%   -1.00% $   37,377,641  ✓
    2026-05    +0.99%   -0.60%       7  28.6%    0.00% $   37,749,165  ✓

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = 'M15'
RESAMPLE    = None
SLM         = 0.3
TP_R        = 5.0
HOLD        = 12
RP          = 0.002
MONTHS      = 123.6
DD_TARGET   = -5.0   # objetivo de drawdown máximo

def ema(s, n):   return s.ewm(n, adjust=False).mean()
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
        {'open':'first','high':'max','low':'min','close':'last','volume':'sum'}
    ).dropna()
def ffill_to(series, target_index):
    s = series.copy()
    if hasattr(s.index,'tz') and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s.reindex(target_index, method='ffill').fillna(False)

def load_data(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

def build_signal(df, m15):
    idx  = df.index
    hour_ok = (idx.hour >= 6) & (idx.hour < 20)
    time_ok = (idx.dayofweek < 5) & hour_ok
    sk   = stoch_k(df, 14).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long  = (sk > 20) & (sk_p <= 20) & time_ok
    stoch_short = (sk < 80) & (sk_p >= 80) & time_ok
    h4 = resample_ohlcv(m15, '4h')
    h4_bull = rsi_calc(h4['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    sig[300:] = np.where(
        stoch_long[300:] & h4v[300:] & d1v[300:], 1,
        np.where(stoch_short[300:] & ~h4v[300:] & ~d1v[300:], -1, 0)
    )
    return sig

def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA DD5%  {TIMEFRAME}  —  XAUUSD  (DD objetivo: {DD_TARGET}%)")
    print(f"{'='*70}")
    m15 = load_data()
    if RESAMPLE is None:
        df = m15.copy()
    else:
        df = resample_ohlcv(m15, RESAMPLE)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
    print(f"  Datos: {len(df):,} barras  {df.index[0].date()} → {df.index[-1].date()}")
    cache = precompute(df, RESAMPLE)
    dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache['op'][:600], cache['hi'][:600], cache['lo'][:600],
        cache['atr14'][:600], dummy, 0.005, 0.015, 0.5, 2.0, 5, 2,
        cache['day_idx'][:600])
    sig = build_signal(df, m15)
    bt = _bt(cache['op'], cache['hi'], cache['lo'], cache['atr14'],
             sig, RP, 0.015, SLM, TP_R, 5, HOLD, cache['day_idx'])
    m = mets(bt[1][:bt[2]], bt[0])
    print(f"  Parámetros: SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} | RP={RP*100:.2f}%")
    print(f"  Retorno mensual  : {m['m']:+.2f}%  {'✅' if m['m'] >= 2.0 else '❌'}")
    print(f"  Max Drawdown     : {m['dd']:+.2f}%  {'✅' if m['dd'] >= DD_TARGET else '❌'} (objetivo ≥{DD_TARGET}%)")
    print(f"  Trades/mes       : {m['tpm']:.1f}     {'✅' if m['tpm'] >= 7.0 else '❌'}")
    print(f"  Peor día         : {m['wd']:+.2f}")
    print(f"  Win Rate         : {m['wr']:.1f}%")
    print(f"{'='*70}\n")
    return m

if __name__ == '__main__':
    run()
