"""
ESTRATEGIA ESTRATEGIA DD10% — 30M (DD objetivo: -10.0%)
============================================================
Señal  : Stoch(14) cruzando sobrevendido + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=1.2 × ATR14 | tp=3.0 × ATR14 | hold=24 barras | rp=1.0%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +3.57%
  Max Drawdown    : -16.52%
  Trades/mes      : 13.2
  Win Rate        : 37.6%
  Estado          : MEJOR ENCONTRADO (DD=-16.52%) ⚠️

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -10.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +3.70%  (mediana: +2.82%)
    Desviación estándar      : 5.74%
    Mejor mes                : +22.56%  |  Peor mes: -7.07%
    Max DD mensual promedio  : -4.03%  |  Peor DD mes: -8.86%
    Trades/mes promedio      : 13.0
    Win Rate promedio        : 37.2%
    Peor día promedio        : -1.69%
    Meses positivos          : 90/125 (72%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +2.08%     -4.52%    12.1   32.5%    6    6
    2017      +3.85%     -3.98%    11.8   36.6%    7    5
    2018      +2.05%     -3.96%    10.4   36.6%    8    4
    2019      +5.61%     -3.51%    11.8   42.7%   10    2
    2020      +2.76%     -3.71%    12.0   36.5%    8    4
    2021      +0.45%     -4.48%    13.2   30.9%    6    6
    2022      +5.12%     -3.67%    14.7   37.9%   11    1
    2023      +6.90%     -3.53%    13.4   42.3%   11    1
    2024      +1.87%     -5.04%    15.2   34.2%    8    4
    2025      +6.36%     -4.07%    15.9   41.5%   12    0
    2026      +3.65%     -3.53%    12.4   37.1%    3    2

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06   +10.22%   -1.99%      14  57.1%   -1.00% $    1,551,833  ✓
    2023-07    +4.21%   -1.99%      10  40.0%   -1.99% $    1,617,165  ✓
    2023-08    +6.11%   -6.43%      19  42.1%   -1.99% $    1,715,948  ✓
    2023-09   +15.21%   -4.90%      16  56.2%   -1.99% $    1,976,901  ✓
    2023-10   +18.85%   -2.98%      16  62.5%   -1.00% $    2,349,488  ✓
    2023-11    +6.69%   -2.97%      11  45.5%   -1.00% $    2,506,658  ✓
    2023-12    +1.92%   -4.01%      13  46.2%   -1.00% $    2,554,888  ✓
    2024-01    -2.62%   -6.79%      13  23.1%   -1.99% $    2,487,846  ✗
    2024-02    +1.74%   -1.99%      10  40.0%   -1.00% $    2,531,044  ✓
    2024-03    +2.26%   -4.69%      11  36.4%   -1.56% $    2,588,136  ✓
    2024-04    -0.64%   -5.52%      13  38.5%   -1.00% $    2,571,463  ✗
    2024-05    -5.83%   -8.76%      19  21.1%   -2.11% $    2,421,569  ✗
    2024-06    +1.86%   -3.02%       9  33.3%   -1.00% $    2,466,669  ✓
    2024-07    +2.01%   -8.15%      18  33.3%   -1.99% $    2,516,365  ✓
    2024-08   +11.08%   -4.90%      21  52.4%   -1.99% $    2,795,271  ✓
    2024-09   +11.88%   -4.30%      19  52.6%   -2.36% $    3,127,451  ✓
    2024-10    +2.99%   -2.97%      18  33.3%   -1.99% $    3,221,081  ✓
    2024-11    -2.78%   -5.98%      12  16.7%   -1.99% $    3,131,666  ✗
    2024-12    +0.49%   -3.38%      20  30.0%   -1.99% $    3,147,134  ✓
    2025-01    +6.38%   -5.85%      19  36.8%   -1.99% $    3,347,886  ✓
    2025-02    +5.52%   -4.43%      18  38.9%   -1.99% $    3,532,818  ✓
    2025-03    +9.99%   -1.99%      10  50.0%   -1.99% $    3,885,851  ✓
    2025-04    +2.46%   -2.97%      18  38.9%   -1.99% $    3,981,613  ✓
    2025-05    +4.62%   -2.97%      11  54.5%   -1.00% $    4,165,455  ✓
    2025-06   +12.13%   -2.97%      16  50.0%   -1.00% $    4,670,879  ✓
    2025-07    +0.95%   -6.79%      20  30.0%   -1.99% $    4,715,238  ✓
    2025-08    +3.89%   -5.05%      21  33.3%   -1.99% $    4,898,820  ✓
    2025-09    +6.97%   -7.73%      13  38.5%   -1.99% $    5,240,336  ✓
    2025-10    +7.11%   -1.99%      13  46.2%   -1.99% $    5,613,164  ✓
    2025-11    +6.75%   -3.08%      15  40.0%   -1.99% $    5,992,062  ✓
    2025-12    +9.57%   -2.97%      17  41.2%   -1.99% $    6,565,607  ✓
    2026-01    +2.00%   -5.34%      16  31.2%   -1.99% $    6,697,006  ✓
    2026-02   +12.07%   -2.97%      18  44.4%   -1.99% $    7,505,407  ✓
    2026-03    -0.77%   -4.90%      15  26.7%   -1.99% $    7,447,871  ✗
    2026-04    +4.98%   -2.44%      10  50.0%   -1.99% $    7,818,707  ✓
    2026-05    -0.02%   -1.99%       3  33.3%   -1.99% $    7,817,371  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = '30M'
RESAMPLE    = '30min'
SLM         = 1.2
TP_R        = 3.0
HOLD        = 24
RP          = 0.01
MONTHS      = 123.6
DD_TARGET   = -10.0   # objetivo de drawdown máximo

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
    sig[150:] = np.where(
        stoch_long[150:] & h4v[150:] & d1v[150:], 1,
        np.where(stoch_short[150:] & ~h4v[150:] & ~d1v[150:], -1, 0)
    )
    return sig

def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA DD10%  {TIMEFRAME}  —  XAUUSD  (DD objetivo: {DD_TARGET}%)")
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
