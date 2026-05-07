"""
ESTRATEGIA ESTRATEGIA DD5% — 4H (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando sobrevendido + D1 RSI — SOLO LARGO
Params : slm=0.3 × ATR14 | tp=2.5 × ATR14 | hold=2 barras | rp=0.5%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.05%
  Max Drawdown    : -4.85%
  Trades/mes      : 9.4
  Win Rate        : 46.1%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.04%  (mediana: +1.95%)
    Desviación estándar      : 2.36%
    Mejor mes                : +8.90%  |  Peor mes: -2.93%
    Max DD mensual promedio  : -1.24%  |  Peor DD mes: -3.67%
    Trades/mes promedio      : 9.2
    Win Rate promedio        : 43.8%
    Peor día promedio        : -0.49%
    Meses positivos          : 92/125 (74%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +1.95%     -1.09%     8.2   38.1%    8    4
    2017      +1.63%     -1.67%    10.2   47.3%    9    3
    2018      +0.97%     -1.26%     7.6   32.4%    7    5
    2019      +1.71%     -1.23%     9.9   45.3%    9    3
    2020      +2.29%     -1.12%    10.1   53.2%   11    1
    2021      +1.07%     -1.24%     7.5   34.5%    7    5
    2022      +1.77%     -1.26%     7.9   31.1%    7    5
    2023      +2.66%     -1.21%     9.4   47.8%   10    2
    2024      +2.06%     -1.34%     9.6   54.2%    9    3
    2025      +3.34%     -1.42%    12.8   48.3%   11    1
    2026      +4.36%     -0.30%     6.6   57.9%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $      430,329  ✗
    2023-07    +1.07%   -2.48%      11  36.4%   -1.00% $      434,947  ✓
    2023-08    +2.52%    0.00%       2 100.0%    0.00% $      445,888  ✓
    2023-09    -1.75%   -1.99%       7  14.3%   -0.50% $      438,086  ✗
    2023-10    +6.90%   -0.50%      10  60.0%   -0.50% $      468,329  ✓
    2023-11    +6.05%   -1.00%      12  58.3%   -0.50% $      496,686  ✓
    2023-12    +4.96%   -1.00%      14  57.1%   -1.00% $      521,325  ✓
    2024-01    +2.47%   -1.00%       5  60.0%    0.00% $      534,196  ✓
    2024-02    +3.16%   -1.49%       9  66.7%   -0.50% $      551,056  ✓
    2024-03    -2.93%   -3.67%      11  18.2%   -0.50% $      534,927  ✗
    2024-04    +5.47%   -1.99%      20  45.0%   -0.50% $      564,190  ✓
    2024-05    -0.38%   -1.49%       8  25.0%   -1.00% $      562,047  ✗
    2024-06    +1.25%    0.00%       1 100.0%    0.00% $      569,072  ✓
    2024-07    +3.65%   -1.49%      13  46.2%   -0.50% $      589,835  ✓
    2024-08    +3.91%   -1.49%      12  50.0%   -1.00% $      612,923  ✓
    2024-09    +5.09%   -1.00%      15  53.3%   -0.50% $      644,128  ✓
    2024-10    +3.26%   -1.49%      17  52.9%   -0.50% $      665,138  ✓
    2024-11    -0.30%   -1.00%       3  33.3%   -0.50% $      663,158  ✗
    2024-12    +0.10%    0.00%       1 100.0%    0.00% $      663,830  ✓
    2025-01    -0.82%   -2.51%      13  23.1%   -1.00% $      658,418  ✗
    2025-02    +0.49%   -1.99%      15  33.3%   -0.50% $      661,633  ✓
    2025-03    +6.49%   -1.00%      14  64.3%   -0.50% $      704,544  ✓
    2025-04    +1.47%   -1.32%      15  40.0%   -1.00% $      714,891  ✓
    2025-05    +0.22%   -1.66%      10  40.0%   -0.50% $      716,478  ✓
    2025-06    +6.39%   -1.00%      12  58.3%   -0.50% $      762,226  ✓
    2025-07    +2.62%   -1.00%      11  54.5%   -0.50% $      782,218  ✓
    2025-08    +0.22%   -2.48%      10  30.0%   -0.50% $      783,924  ✓
    2025-09    +4.90%   -1.00%      11  54.5%   -0.50% $      822,369  ✓
    2025-10    +7.86%   -1.00%      11  72.7%   -0.50% $      887,004  ✓
    2025-11    +6.18%   -1.00%      11  63.6%   -0.50% $      941,840  ✓
    2025-12    +4.03%   -1.02%      20  45.0%   -0.50% $      979,803  ✓
    2026-01    +8.90%   -0.51%      13  76.9%   -0.50% $    1,067,034  ✓
    2026-02    +7.82%    0.00%      10 100.0%    0.00% $    1,150,433  ✓
    2026-03    +4.36%   -0.50%       8  62.5%   -0.50% $    1,200,643  ✓
    2026-04    +0.74%   -0.50%       2  50.0%   -0.50% $    1,209,572  ✓
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    1,209,572  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = '4H'
RESAMPLE    = '4h'
SLM         = 0.3
TP_R        = 2.5
HOLD        = 2
RP          = 0.005
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
    stoch_long = (sk < 30) & (sk_p >= 30) & time_ok
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    sig[20:] = np.where(stoch_long[20:] & d1v[20:], 1, 0)
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
