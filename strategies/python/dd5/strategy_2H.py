"""
ESTRATEGIA ESTRATEGIA DD5% — 2H (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(3) CRUCE saliendo de zona + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.2 × ATR14 | tp=3.0 × ATR14 | hold=2 barras | rp=0.3%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.34%
  Max Drawdown    : -4.71%
  Trades/mes      : 16.1
  Win Rate        : 39.5%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +1.78%  (mediana: +1.60%)
    Desviación estándar      : 1.96%
    Mejor mes                : +9.18%  |  Peor mes: -2.39%
    Max DD mensual promedio  : -1.11%  |  Peor DD mes: -3.26%
    Trades/mes promedio      : 12.0
    Win Rate promedio        : 39.6%
    Peor día promedio        : -0.45%
    Meses positivos          : 104/125 (83%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +1.44%     -1.35%    13.2   33.9%    8    4
    2017      +1.22%     -1.27%    11.2   34.2%   10    2
    2018      +2.36%     -0.94%    11.0   42.1%   11    1
    2019      +1.85%     -1.05%    12.2   41.0%   11    1
    2020      +1.34%     -1.13%    11.8   37.3%    8    4
    2021      +1.92%     -1.03%    12.7   42.3%   10    2
    2022      +1.30%     -1.13%    11.9   37.6%    9    3
    2023      +2.11%     -1.18%    12.8   38.6%   10    2
    2024      +2.59%     -1.00%    12.4   45.5%   12    0
    2025      +1.64%     -1.15%    12.0   37.9%   10    2
    2026      +1.76%     -0.83%     8.4   51.9%    5    0

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +1.32%   -0.90%      13  38.5%   -0.30% $      442,603  ✓
    2023-07    -0.90%   -1.49%       7  14.3%   -0.60% $      438,608  ✗
    2023-08    +2.71%   -0.90%      15  40.0%   -0.60% $      450,484  ✓
    2023-09    +8.90%   -0.60%      19  68.4%   -0.30% $      490,592  ✓
    2023-10    +1.55%   -1.19%      13  38.5%   -0.30% $      498,187  ✓
    2023-11    -1.17%   -1.37%       9  22.2%   -0.60% $      492,383  ✗
    2023-12    +0.01%   -2.18%      16  31.2%   -0.60% $      492,450  ✓
    2024-01    +3.35%   -0.60%      11  54.5%   -0.30% $      508,936  ✓
    2024-02    +0.89%   -1.79%       9  33.3%   -0.60% $      513,461  ✓
    2024-03    +0.08%   -1.19%       7  42.9%   -0.60% $      513,856  ✓
    2024-04    +2.50%   -0.60%      11  45.5%   -0.30% $      526,727  ✓
    2024-05    +0.64%   -0.90%      11  36.4%   -0.60% $      530,096  ✓
    2024-06    +1.49%   -0.90%      11  36.4%   -0.60% $      538,003  ✓
    2024-07    +2.81%   -0.90%      11  54.5%   -0.30% $      553,122  ✓
    2024-08    +9.18%   -0.60%      19  68.4%   -0.30% $      603,886  ✓
    2024-09    +2.35%   -0.98%      13  46.2%   -0.68% $      618,079  ✓
    2024-10    +1.18%   -1.49%      16  31.2%   -0.60% $      625,383  ✓
    2024-11    +3.57%   -0.60%      12  58.3%   -0.30% $      647,721  ✓
    2024-12    +3.01%   -1.50%      18  38.9%   -0.60% $      667,226  ✓
    2025-01    -0.06%   -1.49%      12  25.0%   -0.30% $      666,826  ✗
    2025-02    +1.75%   -0.90%      13  38.5%   -0.30% $      678,478  ✓
    2025-03    +0.23%   -0.66%       8  25.0%   -0.30% $      680,053  ✓
    2025-04    +1.81%   -0.60%      11  45.5%   -0.30% $      692,344  ✓
    2025-05    +3.33%   -1.19%      13  46.2%   -0.60% $      715,377  ✓
    2025-06    +3.29%   -1.19%      16  50.0%   -0.60% $      738,889  ✓
    2025-07    -2.38%   -2.38%      12   8.3%   -0.60% $      721,302  ✗
    2025-08    +0.28%   -1.79%      15  26.7%   -0.60% $      723,317  ✓
    2025-09    +3.02%   -0.60%      10  50.0%   -0.30% $      745,178  ✓
    2025-10    +4.47%   -0.30%      11  63.6%   -0.30% $      778,504  ✓
    2025-11    +3.02%   -1.19%      14  42.9%   -0.60% $      801,990  ✓
    2025-12    +0.89%   -1.49%       9  33.3%   -0.30% $      809,121  ✓
    2026-01    +0.72%   -0.57%       6  50.0%   -0.30% $      814,981  ✓
    2026-02    +2.87%   -0.60%       8  62.5%   -0.30% $      838,358  ✓
    2026-03    +2.10%   -1.79%      13  38.5%   -0.30% $      855,947  ✓
    2026-04    +1.60%   -0.90%      12  41.7%   -0.60% $      869,634  ✓
    2026-05    +1.50%   -0.30%       3  66.7%    0.00% $      882,701  ✓

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = '2H'
RESAMPLE    = '2h'
SLM         = 0.2
TP_R        = 3.0
HOLD        = 2
RP          = 0.003
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
    time_ok = idx.dayofweek < 5
    sk   = stoch_k(df, 3).fillna(50).values
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
    sig[40:] = np.where(
        stoch_long[40:] & h4v[40:] & d1v[40:], 1,
        np.where(stoch_short[40:] & ~h4v[40:] & ~d1v[40:], -1, 0)
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
