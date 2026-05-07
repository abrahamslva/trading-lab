"""
ESTRATEGIA ESTRATEGIA DD5% — 3H (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando sobrevendido + W1/D1 RSI — SOLO LARGO
Params : slm=0.15 × ATR14 | tp=4.0 × ATR14 | hold=2 barras | rp=0.4%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +3.55%
  Max Drawdown    : -3.94%
  Trades/mes      : 10.2
  Win Rate        : 40.0%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.59%  (mediana: +1.72%)
    Desviación estándar      : 3.00%
    Mejor mes                : +10.98%  |  Peor mes: -2.05%
    Max DD mensual promedio  : -0.99%  |  Peor DD mes: -3.16%
    Trades/mes promedio      : 7.5
    Win Rate promedio        : 32.1%
    Peor día promedio        : -0.38%
    Meses positivos          : 84/125 (67%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +2.57%     -0.63%     6.2   23.6%    7    5
    2017      +1.02%     -1.23%     6.2   28.3%    6    6
    2018      +1.13%     -0.50%     4.0   16.0%    5    7
    2019      +2.87%     -1.30%    10.0   35.1%   10    2
    2020      +3.80%     -1.18%     9.2   51.4%   11    1
    2021      +1.81%     -0.66%     3.8   26.2%    6    6
    2022      +2.26%     -0.74%     5.8   20.2%    5    7
    2023      +2.64%     -1.13%     8.2   28.0%    8    4
    2024      +3.83%     -1.20%    10.1   47.5%   11    1
    2025      +4.01%     -1.41%    11.7   42.6%   11    1
    2026      +2.45%     -0.72%     6.8   37.0%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $      763,474  ✗
    2023-07    +2.39%   -1.98%       9  33.3%   -0.80% $      781,684  ✓
    2023-08    +0.00%    0.00%       0   0.0%    0.00% $      781,684  ✗
    2023-09    -0.80%   -0.80%       2   0.0%   -0.40% $      775,443  ✗
    2023-10    +2.22%   -1.20%       8  37.5%   -0.40% $      792,627  ✓
    2023-11    +0.83%   -2.94%      15  26.7%   -0.40% $      799,166  ✓
    2023-12    +3.09%   -1.98%      12  41.7%   -0.40% $      823,857  ✓
    2024-01    +2.51%   -1.20%       9  44.4%   -0.80% $      844,551  ✓
    2024-02    +5.88%   -1.20%      12  50.0%   -0.40% $      894,186  ✓
    2024-03   +10.98%   -0.80%      14  64.3%   -0.40% $      992,385  ✓
    2024-04    +5.10%   -1.98%      17  35.3%   -0.40% $    1,043,030  ✓
    2024-05    -2.05%   -2.05%       8  12.5%   -0.40% $    1,021,605  ✗
    2024-06    +1.60%    0.00%       1 100.0%    0.00% $    1,037,950  ✓
    2024-07    +6.65%   -1.59%      15  46.7%   -0.80% $    1,107,003  ✓
    2024-08    +3.66%   -1.59%      10  40.0%   -0.40% $    1,147,528  ✓
    2024-09    +4.42%   -1.20%      14  35.7%   -0.40% $    1,198,301  ✓
    2024-10    +4.85%   -2.03%      17  41.2%   -0.40% $    1,256,370  ✓
    2024-11    +1.19%   -0.40%       2  50.0%    0.00% $    1,271,366  ✓
    2024-12    +1.19%   -0.40%       2  50.0%   -0.40% $    1,286,541  ✓
    2025-01    +3.92%   -2.38%      14  35.7%   -0.80% $    1,337,029  ✓
    2025-02    +4.63%   -1.01%      17  41.2%   -0.40% $    1,398,888  ✓
    2025-03    +3.85%   -1.59%      13  38.5%   -0.80% $    1,452,799  ✓
    2025-04    -0.47%   -2.38%      13  23.1%   -0.80% $    1,446,012  ✗
    2025-05    +1.45%   -1.98%       9  33.3%   -0.40% $    1,466,950  ✓
    2025-06    +5.26%   -1.20%      12  41.7%   -0.80% $    1,544,184  ✓
    2025-07    +1.51%   -0.80%       7  42.9%   -0.40% $    1,567,506  ✓
    2025-08    +5.70%   -0.40%       6  66.7%   -0.40% $    1,656,925  ✓
    2025-09    +9.93%   -0.80%      16  56.2%   -0.40% $    1,821,534  ✓
    2025-10    +7.73%   -0.80%       8  75.0%   -0.40% $    1,962,255  ✓
    2025-11    +1.18%   -1.59%       7  28.6%   -0.40% $    1,985,361  ✓
    2025-12    +3.46%   -1.98%      18  27.8%   -0.80% $    2,054,078  ✓
    2026-01    +5.26%   -1.20%      12  41.7%   -0.80% $    2,162,224  ✓
    2026-02    +4.01%   -0.80%       8  50.0%   -0.40% $    2,248,831  ✓
    2026-03    +0.24%   -1.20%       9  33.3%   -0.40% $    2,254,327  ✓
    2026-04    +2.76%   -0.40%       5  60.0%   -0.40% $    2,316,469  ✓
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    2,316,469  ✗

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
SLM         = 0.15
TP_R        = 4.0
HOLD        = 2
RP          = 0.004
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
