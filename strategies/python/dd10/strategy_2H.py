"""
ESTRATEGIA ESTRATEGIA DD10% — 2H (DD objetivo: -10.0%)
============================================================
Señal  : Stoch(3) CRUCE saliendo de zona + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.7 × ATR14 | tp=3.0 × ATR14 | hold=2 barras | rp=0.7%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.37%
  Max Drawdown    : -7.69%
  Trades/mes      : 15.6
  Win Rate        : 51.6%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -10.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.08%  (mediana: +2.12%)
    Desviación estándar      : 3.05%
    Mejor mes                : +11.02%  |  Peor mes: -4.32%
    Max DD mensual promedio  : -1.71%  |  Peor DD mes: -4.32%
    Trades/mes promedio      : 11.8
    Win Rate promedio        : 51.6%
    Peor día promedio        : -0.86%
    Meses positivos          : 91/125 (73%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +1.56%     -2.07%    12.9   46.8%    7    5
    2017      +1.52%     -1.68%    11.0   48.0%    8    4
    2018      +2.77%     -1.79%    10.8   53.9%    9    3
    2019      +1.30%     -1.99%    12.0   48.7%    8    4
    2020      +1.53%     -1.70%    11.3   49.0%   10    2
    2021      +1.54%     -1.73%    12.6   50.0%    8    4
    2022      +1.81%     -1.91%    11.8   50.9%    6    6
    2023      +3.70%     -1.47%    12.6   57.6%   12    0
    2024      +2.68%     -1.74%    12.2   51.8%   10    2
    2025      +2.25%     -1.35%    11.8   56.9%   10    2
    2026      +2.34%     -0.94%     8.4   56.7%    3    2

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +4.85%   -1.40%      13  69.2%   -0.70% $      483,303  ✓
    2023-07    +0.80%   -0.87%       7  42.9%   -0.70% $      487,154  ✓
    2023-08    +7.84%   -2.09%      15  53.3%   -1.40% $      525,335  ✓
    2023-09   +11.02%   -0.87%      19  73.7%   -0.30% $      583,241  ✓
    2023-10    +4.98%   -1.40%      13  76.9%   -0.70% $      612,273  ✓
    2023-11    +0.15%   -1.40%       8  50.0%   -1.40% $      613,218  ✓
    2023-12    +1.23%   -1.47%      16  56.2%   -0.98% $      620,782  ✓
    2024-01    +4.12%   -1.22%      11  63.6%   -0.70% $      646,333  ✓
    2024-02    -0.39%   -3.38%       9  33.3%   -0.70% $      643,835  ✗
    2024-03    -2.66%   -2.91%       7  28.6%   -1.40% $      626,690  ✗
    2024-04    +3.27%   -0.85%      10  50.0%   -0.70% $      647,170  ✓
    2024-05    +1.77%   -1.76%      11  54.5%   -1.40% $      658,633  ✓
    2024-06    +2.98%   -0.87%      10  60.0%   -0.70% $      678,290  ✓
    2024-07    +0.95%   -2.14%      11  54.5%   -0.70% $      684,715  ✓
    2024-08    +8.75%   -1.40%      19  73.7%   -0.70% $      744,658  ✓
    2024-09    +3.29%   -1.45%      13  61.5%   -1.45% $      769,134  ✓
    2024-10    +0.06%   -2.51%      16  31.2%   -1.40% $      769,619  ✓
    2024-11    +4.55%   -0.73%      12  58.3%   -0.73% $      804,627  ✓
    2024-12    +5.51%   -1.65%      17  52.9%   -0.70% $      848,955  ✓
    2025-01    -1.76%   -2.79%      12  41.7%   -0.70% $      834,047  ✗
    2025-02    +2.12%   -0.76%      13  53.8%   -0.70% $      851,748  ✓
    2025-03    +0.98%   -0.74%       8  62.5%   -0.70% $      860,101  ✓
    2025-04    +0.92%   -1.40%      11  54.5%   -0.70% $      867,972  ✓
    2025-05    +4.26%   -0.93%      12  58.3%   -0.93% $      904,943  ✓
    2025-06    +5.92%   -1.40%      16  62.5%   -1.40% $      958,551  ✓
    2025-07    -0.98%   -1.69%      12  33.3%   -1.40% $      949,153  ✗
    2025-08    +0.66%   -2.47%      15  46.7%   -0.97% $      955,387  ✓
    2025-09    +6.43%   -1.09%      10  80.0%   -0.39% $    1,016,836  ✓
    2025-10    +3.77%   -0.70%      11  72.7%   -0.70% $    1,055,128  ✓
    2025-11    +4.69%   -0.90%      13  53.8%   -0.90% $    1,104,568  ✓
    2025-12    +0.01%   -1.37%       8  62.5%   -0.70% $    1,104,650  ✓
    2026-01    -0.15%   -0.81%       6  50.0%   -0.55% $    1,102,953  ✗
    2026-02    +4.03%   -0.41%       8  87.5%   -0.41% $    1,147,436  ✓
    2026-03    +2.24%   -1.87%      13  46.2%   -0.70% $    1,173,143  ✓
    2026-04    +5.93%   -0.70%      12  66.7%   -0.70% $    1,242,662  ✓
    2026-05    -0.36%   -0.93%       3  33.3%   -0.12% $    1,238,249  ✗

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
SLM         = 0.7
TP_R        = 3.0
HOLD        = 2
RP          = 0.007
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
