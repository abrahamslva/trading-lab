"""
ESTRATEGIA ESTRATEGIA DD10% — 3H (DD objetivo: -10.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando sobrevendido + W1/D1 RSI — SOLO LARGO
Params : slm=0.4 × ATR14 | tp=4.0 × ATR14 | hold=2 barras | rp=1.0%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +5.04%
  Max Drawdown    : -9.67%
  Trades/mes      : 10.0
  Win Rate        : 48.4%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -10.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +3.73%  (mediana: +2.82%)
    Desviación estándar      : 5.14%
    Mejor mes                : +24.55%  |  Peor mes: -6.11%
    Max DD mensual promedio  : -2.04%  |  Peor DD mes: -6.54%
    Trades/mes promedio      : 7.3
    Win Rate promedio        : 38.5%
    Peor día promedio        : -0.86%
    Meses positivos          : 80/125 (64%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +3.81%     -1.24%     6.0   35.9%    7    5
    2017      +0.65%     -2.72%     6.1   32.1%    6    6
    2018      +2.76%     -1.23%     4.0   20.7%    4    8
    2019      +2.52%     -2.61%     9.7   41.1%    7    5
    2020      +4.39%     -2.46%     9.0   57.4%   11    1
    2021      +2.70%     -1.32%     3.8   33.1%    5    7
    2022      +3.62%     -1.59%     5.6   22.6%    6    6
    2023      +4.74%     -1.95%     8.2   38.6%    7    5
    2024      +5.36%     -2.67%     9.8   50.2%   11    1
    2025      +6.22%     -2.86%    11.4   50.4%   12    0
    2026      +4.91%     -1.39%     6.6   45.8%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $    1,330,150  ✗
    2023-07   +11.08%   -1.59%       9  66.7%   -1.00% $    1,477,524  ✓
    2023-08    +0.00%    0.00%       0   0.0%    0.00% $    1,477,524  ✗
    2023-09    -1.99%   -1.99%       2   0.0%   -1.00% $    1,448,121  ✗
    2023-10   +11.79%   -1.00%       8  62.5%   -1.00% $    1,618,881  ✓
    2023-11    -2.55%   -6.54%      15  26.7%   -1.00% $    1,577,606  ✗
    2023-12   +12.94%   -1.00%      12  75.0%   -1.00% $    1,781,762  ✓
    2024-01    +2.01%   -2.97%       9  44.4%   -1.99% $    1,817,586  ✓
    2024-02    +3.78%   -2.97%      12  41.7%   -1.00% $    1,886,222  ✓
    2024-03   +20.26%   -1.99%      13  61.5%   -1.99% $    2,268,366  ✓
    2024-04    +9.68%   -2.97%      17  41.2%   -1.00% $    2,487,847  ✓
    2024-05    -6.11%   -6.11%       8  12.5%   -1.00% $    2,335,746  ✗
    2024-06    +4.00%    0.00%       1 100.0%    0.00% $    2,429,176  ✓
    2024-07    +7.47%   -3.94%      15  53.3%   -1.99% $    2,610,731  ✓
    2024-08    +8.40%   -2.97%      10  50.0%   -1.00% $    2,830,026  ✓
    2024-09    +9.99%   -1.99%      13  53.8%   -1.00% $    3,112,655  ✓
    2024-10    +2.20%   -4.18%      16  43.8%   -1.00% $    3,181,111  ✓
    2024-11    +1.30%   -1.00%       2  50.0%    0.00% $    3,222,532  ✓
    2024-12    +1.34%   -1.00%       2  50.0%   -1.00% $    3,265,640  ✓
    2025-01    +3.76%   -5.50%      13  30.8%   -1.99% $    3,388,408  ✓
    2025-02    +6.10%   -2.19%      17  41.2%   -1.00% $    3,594,978  ✓
    2025-03    +4.25%   -2.73%      11  54.5%   -1.00% $    3,747,665  ✓
    2025-04    +0.59%   -3.94%      13  38.5%   -1.99% $    3,769,958  ✓
    2025-05    +0.33%   -5.26%       9  33.3%   -1.00% $    3,782,523  ✓
    2025-06    +5.76%   -2.97%      12  50.0%   -1.00% $    4,000,297  ✓
    2025-07    +4.09%   -1.31%       7  57.1%   -1.00% $    4,164,039  ✓
    2025-08    +7.35%   -1.00%       6  66.7%   -1.00% $    4,469,958  ✓
    2025-09   +24.55%   -2.30%      16  68.8%   -1.00% $    5,567,337  ✓
    2025-10   +13.40%   -1.00%       8  87.5%   -1.00% $    6,313,539  ✓
    2025-11    +1.11%   -2.97%       7  42.9%   -1.00% $    6,383,772  ✓
    2025-12    +3.39%   -3.10%      18  33.3%   -1.99% $    6,600,326  ✓
    2026-01    +9.60%   -1.99%      11  54.5%   -1.00% $    7,233,856  ✓
    2026-02    +6.51%   -1.99%       8  50.0%   -1.00% $    7,704,747  ✓
    2026-03    +0.80%   -1.99%       9  44.4%   -1.00% $    7,766,708  ✓
    2026-04    +7.64%   -1.00%       5  80.0%   -0.68% $    8,359,781  ✓
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    8,359,781  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = '3H'
RESAMPLE    = '3h'
SLM         = 0.4
TP_R        = 4.0
HOLD        = 2
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
    time_ok = idx.dayofweek < 5
    sk   = stoch_k(df, 3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long = (sk < 30) & (sk_p >= 30) & time_ok
    w1 = resample_ohlcv(m15, 'W')
    w1_bull = rsi_calc(w1['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    w1v = ffill_to(w1_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    sig[25:] = np.where(stoch_long[25:] & w1v[25:] & d1v[25:], 1, 0)
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
