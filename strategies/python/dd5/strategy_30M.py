"""
ESTRATEGIA ESTRATEGIA DD5% — 30M (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(14) cruzando sobrevendido + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.5 × ATR14 | tp=3.0 × ATR14 | hold=24 barras | rp=0.4%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +3.08%
  Max Drawdown    : -7.37%
  Trades/mes      : 16.3
  Win Rate        : 36.9%
  Estado          : MEJOR ENCONTRADO (DD=-7.37%) ⚠️

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +3.11%  (mediana: +2.80%)
    Desviación estándar      : 3.49%
    Mejor mes                : +13.08%  |  Peor mes: -4.34%
    Max DD mensual promedio  : -1.85%  |  Peor DD mes: -4.34%
    Trades/mes promedio      : 16.1
    Win Rate promedio        : 36.6%
    Peor día promedio        : -0.96%
    Meses positivos          : 95/125 (76%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +3.71%     -1.66%    15.2   39.6%   10    2
    2017      +2.43%     -1.95%    14.3   34.7%    9    3
    2018      +1.30%     -1.56%    12.4   32.2%    7    5
    2019      +3.09%     -1.62%    14.8   36.7%   10    2
    2020      +3.56%     -1.85%    15.4   38.2%   11    1
    2021      +3.13%     -1.82%    16.0   36.8%   10    2
    2022      +4.55%     -1.85%    17.3   43.1%   10    2
    2023      +3.04%     -1.69%    16.0   35.1%    6    6
    2024      +3.03%     -2.44%    19.8   34.8%   10    2
    2025      +3.11%     -2.12%    20.4   34.7%    9    3
    2026      +3.51%     -1.59%    15.4   35.6%    3    2

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +5.82%   -0.80%      15  53.3%   -0.40% $    1,465,704  ✓
    2023-07    -0.83%   -2.39%      14  21.4%   -1.20% $    1,453,585  ✗
    2023-08    +7.37%   -1.59%      26  42.3%   -0.80% $    1,560,689  ✓
    2023-09    +7.39%   -1.20%      18  50.0%   -0.80% $    1,676,003  ✓
    2023-10    +7.82%   -0.80%      17  52.9%   -0.80% $    1,807,067  ✓
    2023-11    -1.61%   -1.99%      12  16.7%   -0.80% $    1,777,987  ✗
    2023-12    -0.04%   -3.54%      16  25.0%   -1.20% $    1,777,308  ✗
    2024-01    +3.20%   -1.99%      16  37.5%   -1.59% $    1,834,168  ✓
    2024-02    -1.62%   -3.16%      16  18.8%   -1.59% $    1,804,480  ✗
    2024-03    +0.77%   -2.77%      14  28.6%   -1.59% $    1,818,308  ✓
    2024-04    +1.16%   -3.54%      17  29.4%   -1.59% $    1,839,425  ✓
    2024-05    -3.19%   -4.32%      24  16.7%   -1.20% $    1,780,701  ✗
    2024-06    +4.04%   -1.20%      10  50.0%   -0.80% $    1,852,637  ✓
    2024-07    +6.52%   -1.60%      24  41.7%   -0.80% $    1,973,450  ✓
    2024-08    +6.76%   -1.59%      26  42.3%   -1.20% $    2,106,848  ✓
    2024-09    +9.97%   -1.59%      24  50.0%   -0.40% $    2,316,922  ✓
    2024-10    +2.78%   -1.59%      21  33.3%   -1.20% $    2,381,254  ✓
    2024-11    +4.44%   -2.77%      17  41.2%   -1.59% $    2,486,925  ✓
    2024-12    +1.54%   -3.16%      28  28.6%   -1.59% $    2,525,187  ✓
    2025-01    +9.52%   -1.59%      29  44.8%   -1.20% $    2,765,602  ✓
    2025-02    +8.24%   -1.59%      20  50.0%   -0.80% $    2,993,561  ✓
    2025-03    +5.08%   -1.98%      12  50.0%   -1.20% $    3,145,730  ✓
    2025-04    +0.34%   -1.98%      23  26.1%   -1.59% $    3,156,554  ✓
    2025-05    +0.77%   -2.78%      14  28.6%   -0.80% $    3,180,744  ✓
    2025-06    +6.12%   -1.59%      17  47.1%   -1.20% $    3,375,257  ✓
    2025-07    +4.42%   -1.59%      25  36.0%   -1.20% $    3,524,365  ✓
    2025-08    +3.44%   -1.59%      24  33.3%   -0.80% $    3,645,704  ✓
    2025-09    -0.85%   -3.94%      22  22.7%   -1.59% $    3,614,871  ✗
    2025-10    +1.57%   -1.20%      16  31.2%   -0.80% $    3,671,538  ✓
    2025-11    -0.84%   -2.77%      18  22.2%   -1.20% $    3,640,834  ✗
    2025-12    -0.46%   -2.78%      25  24.0%   -0.80% $    3,624,193  ✗
    2026-01    +7.82%   -0.80%      17  52.9%   -0.40% $    3,907,605  ✓
    2026-02    +4.01%   -1.59%      22  36.4%   -1.20% $    4,064,298  ✓
    2026-03    +6.96%   -1.59%      19  47.4%   -1.20% $    4,347,139  ✓
    2026-04    -0.83%   -2.39%      14  21.4%   -1.20% $    4,311,196  ✗
    2026-05    -0.41%   -1.59%       5  20.0%   -1.59% $    4,293,541  ✗

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
SLM         = 0.5
TP_R        = 3.0
HOLD        = 24
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
