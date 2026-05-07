"""
ESTRATEGIA ESTRATEGIA DD10% — 4H (DD objetivo: -10.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando sobrevendido + D1 RSI — SOLO LARGO
Params : slm=0.7 × ATR14 | tp=2.5 × ATR14 | hold=2 barras | rp=1.5%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +3.19%
  Max Drawdown    : -12.88%
  Trades/mes      : 8.6
  Win Rate        : 54.5%
  Estado          : MEJOR ENCONTRADO (DD=-12.88%) ⚠️

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -10.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +3.33%  (mediana: +2.04%)
    Desviación estándar      : 5.40%
    Mejor mes                : +19.67%  |  Peor mes: -6.72%
    Max DD mensual promedio  : -2.76%  |  Peor DD mes: -8.66%
    Trades/mes promedio      : 8.4
    Win Rate promedio        : 50.0%
    Peor día promedio        : -1.19%
    Meses positivos          : 79/125 (63%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +4.48%     -2.81%     7.9   46.9%    9    3
    2017      +3.49%     -3.31%     9.6   58.5%    7    5
    2018      +1.36%     -2.76%     6.5   36.8%    5    7
    2019      +1.89%     -2.72%     9.0   51.8%    8    4
    2020      +4.82%     -2.55%     9.4   59.7%   10    2
    2021      +2.24%     -2.87%     6.8   41.3%    8    4
    2022      +2.81%     -2.80%     7.3   36.5%    6    6
    2023      +3.58%     -2.72%     8.4   51.6%    8    4
    2024      +3.08%     -2.38%     8.5   62.7%    8    4
    2025      +4.39%     -3.44%    11.2   53.8%    7    5
    2026      +6.12%     -0.90%     6.2   51.7%    3    2

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $    1,323,545  ✗
    2023-07    +3.61%   -4.95%       9  55.6%   -1.50% $    1,371,272  ✓
    2023-08    +8.85%    0.00%       2 100.0%    0.00% $    1,492,633  ✓
    2023-09    -3.65%   -5.25%       5  20.0%   -1.50% $    1,438,174  ✗
    2023-10   +10.13%   -1.50%      10  60.0%   -1.50% $    1,583,824  ✓
    2023-11    +3.94%   -3.12%      11  54.5%   -1.50% $    1,646,236  ✓
    2023-12    +1.44%   -1.99%      12  58.3%   -1.50% $    1,669,864  ✓
    2024-01    +5.97%   -1.00%       5  60.0%   -0.76% $    1,769,502  ✓
    2024-02   +13.53%   -1.03%       8  87.5%   -1.03% $    2,008,871  ✓
    2024-03    -6.72%   -7.64%      11  36.4%   -1.50% $    1,873,886  ✗
    2024-04   +14.68%   -1.78%      18  61.1%   -1.50% $    2,148,890  ✓
    2024-05    -4.74%   -4.74%       7  28.6%   -1.50% $    2,047,042  ✗
    2024-06    +2.70%    0.00%       1 100.0%    0.00% $    2,102,301  ✓
    2024-07    +1.02%   -4.07%      12  41.7%   -1.50% $    2,123,712  ✓
    2024-08    +8.87%   -1.98%      11  72.7%   -1.50% $    2,312,103  ✓
    2024-09    +3.00%   -2.98%      12  50.0%   -1.50% $    2,381,566  ✓
    2024-10    -0.05%   -1.82%      14  64.3%   -1.50% $    2,380,361  ✗
    2024-11    -1.41%   -1.50%       2  50.0%   -1.50% $    2,346,832  ✗
    2024-12    +0.13%    0.00%       1 100.0%    0.00% $    2,349,889  ✓
    2025-01    -3.85%   -5.87%      10  30.0%   -1.50% $    2,259,438  ✗
    2025-02    -3.34%   -4.70%      14  42.9%   -1.50% $    2,183,908  ✗
    2025-03   +12.64%   -1.50%      14  78.6%   -1.50% $    2,459,875  ✓
    2025-04    -3.39%   -3.94%      11  36.4%   -1.50% $    2,376,596  ✗
    2025-05    +2.04%   -1.50%      10  60.0%   -1.50% $    2,425,139  ✓
    2025-06   +19.67%   -1.50%      11  72.7%   -1.50% $    2,902,250  ✓
    2025-07    +3.60%   -2.98%      11  63.6%   -1.50% $    3,006,606  ✓
    2025-08    -1.63%   -5.19%       8  25.0%   -1.50% $    2,957,489  ✗
    2025-09   +14.41%   -1.50%      10  70.0%   -1.50% $    3,383,726  ✓
    2025-10   +11.90%   -2.98%      11  72.7%   -1.50% $    3,786,435  ✓
    2025-11    +2.08%   -4.56%      10  60.0%   -1.50% $    3,865,359  ✓
    2025-12    -1.43%   -5.01%      15  33.3%   -1.50% $    3,809,986  ✗
    2026-01   +13.64%   -1.50%      12  83.3%   -1.50% $    4,329,660  ✓
    2026-02   +12.05%    0.00%      10 100.0%    0.00% $    4,851,581  ✓
    2026-03    +6.42%   -1.50%       8  75.0%   -1.50% $    5,163,081  ✓
    2026-04    -1.50%   -1.50%       1   0.0%   -1.50% $    5,085,634  ✗
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    5,085,634  ✗

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
SLM         = 0.7
TP_R        = 2.5
HOLD        = 2
RP          = 0.015
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
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    sig[20:] = np.where(stoch_long[20:] & d1v[20:], 1, 0)
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
