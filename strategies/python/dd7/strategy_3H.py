"""
ESTRATEGIA GANADORA — 3H (3 horas)
====================================
Señal  : sk3_level_w1d1_LO — Stoch(3) entrando zona sobrevendida (long only)
Filtro : W1 RSI > 50  AND  D1 RSI > 50  (alineación semanal + diaria)
         *** IMPORTANTE: se usa W1 (semanal) en lugar de 4H porque las barras
         de 3H no alinean limpiamente con el grid de 4H, causando ruido ***
Params : slm=0.3 × ATR14 | tp=4.0 × ATR14 | hold=2 barras | rp=0.5%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.42%
  Max Drawdown    : -6.04%
  Trades/mes      : 7.5
  Win Rate        : 46.1%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.44%  (mediana: +2.00%)
    Desviación estándar      : 2.95%
    Mejor mes                : +14.72%  |  Peor mes: -3.01%
    Max DD mensual promedio  : -1.09%  |  Peor DD mes: -3.48%
    Trades/mes promedio      : 7.4
    Win Rate promedio        : 37.0%
    Peor día promedio        : -0.44%
    Meses positivos          : 84/125 (67%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +2.50%     -0.66%     6.0   33.9%    7    5
    2017      +0.44%     -1.53%     6.2   30.1%    6    6
    2018      +1.28%     -0.62%     4.0   19.0%    5    7
    2019      +2.15%     -1.52%     9.9   37.7%    9    3
    2020      +3.12%     -1.25%     9.1   56.5%   11    1
    2021      +1.86%     -0.69%     3.8   33.1%    5    7
    2022      +2.44%     -0.83%     5.8   21.9%    6    6
    2023      +2.67%     -1.07%     8.2   36.8%    8    4
    2024      +3.47%     -1.43%     9.9   48.6%   11    1
    2025      +4.22%     -1.48%    11.6   48.4%   12    0
    2026      +3.00%     -0.70%     6.6   45.8%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $      590,753  ✗
    2023-07    +5.17%   -1.49%       9  55.6%   -1.00% $      621,277  ✓
    2023-08    +0.00%    0.00%       0   0.0%    0.00% $      621,277  ✗
    2023-09    -1.00%   -1.00%       2   0.0%   -0.50% $      615,079  ✗
    2023-10    +6.22%   -0.50%       8  62.5%   -0.50% $      653,359  ✓
    2023-11    +1.27%   -3.48%      15  33.3%   -0.50% $      661,635  ✓
    2023-12    +3.39%   -1.00%      12  58.3%   -0.50% $      684,072  ✓
    2024-01    +1.09%   -1.49%       9  44.4%   -1.00% $      691,513  ✓
    2024-02    +5.02%   -1.49%      12  50.0%   -0.50% $      726,198  ✓
    2024-03   +11.26%   -1.00%      14  64.3%   -1.00% $      807,939  ✓
    2024-04    +5.46%   -1.49%      17  35.3%   -0.50% $      852,054  ✓
    2024-05    -3.01%   -3.01%       8  12.5%   -0.50% $      826,443  ✗
    2024-06    +2.00%    0.00%       1 100.0%    0.00% $      842,972  ✓
    2024-07    +4.14%   -1.99%      15  46.7%   -1.00% $      877,907  ✓
    2024-08    +3.78%   -1.99%      10  40.0%   -0.50% $      911,080  ✓
    2024-09    +6.26%   -1.49%      13  46.2%   -0.50% $      968,087  ✓
    2024-10    +3.03%   -2.26%      16  43.8%   -0.50% $      997,395  ✓
    2024-11    +1.49%   -0.50%       2  50.0%    0.00% $    1,012,256  ✓
    2024-12    +1.07%   -0.50%       2  50.0%   -0.50% $    1,023,051  ✓
    2025-01    +3.59%   -2.89%      14  35.7%   -1.00% $    1,059,804  ✓
    2025-02    +4.11%   -1.13%      17  41.2%   -0.50% $    1,103,325  ✓
    2025-03    +4.00%   -1.49%      12  41.7%   -0.50% $    1,147,466  ✓
    2025-04    +0.35%   -1.99%      13  30.8%   -1.00% $    1,151,476  ✓
    2025-05    +0.61%   -2.56%       9  33.3%   -0.50% $    1,158,452  ✓
    2025-06    +2.08%   -1.49%      12  41.7%   -1.00% $    1,182,591  ✓
    2025-07    +2.41%   -0.71%       7  57.1%   -0.50% $    1,211,084  ✓
    2025-08    +4.54%   -0.50%       6  66.7%   -0.50% $    1,266,076  ✓
    2025-09   +14.72%   -1.04%      16  68.8%   -0.50% $    1,452,466  ✓
    2025-10    +8.33%   -0.50%       8  87.5%   -0.50% $    1,573,482  ✓
    2025-11    +3.38%   -1.49%       7  42.9%   -0.50% $    1,626,729  ✓
    2025-12    +2.50%   -2.02%      18  33.3%   -1.00% $    1,667,355  ✓
    2026-01    +5.68%   -1.00%      11  54.5%   -0.50% $    1,762,125  ✓
    2026-02    +4.02%   -1.00%       8  50.0%   -0.50% $    1,833,020  ✓
    2026-03    +0.75%   -1.00%       9  44.4%   -0.50% $    1,846,725  ✓
    2026-04    +4.55%   -0.50%       5  80.0%   -0.28% $    1,930,767  ✓
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    1,930,767  ✗

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
SLM         = 0.3    # MUY ajustado — crítico para controlar DD en 3H
TP_R        = 4.0
HOLD        = 2
RP          = 0.005
MONTHS      = 123.6

def rsi_calc(s, n=14):
    d  = s.diff()
    up = d.clip(lower=0).ewm(n, adjust=False).mean()
    dn = (-d).clip(lower=0).ewm(n, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))

def stoch_k(d, k=3):
    lk = d['low'].rolling(k).min()
    hk = d['high'].rolling(k).max()
    return (d['close'] - lk) / (hk - lk + 1e-12) * 100

def resample_ohlcv(df, rule):
    return df.resample(rule).agg(
        {'open': 'first', 'high': 'max', 'low': 'min',
         'close': 'last', 'volume': 'sum'}
    ).dropna()

def ffill_to(series, target_index):
    s = series.copy()
    if hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s.reindex(target_index, method='ffill').fillna(False)

def load_data(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

def build_signal(df_tf, m15):
    idx  = df_tf.index
    n    = len(df_tf)

    time_ok = (idx.dayofweek < 5) & (idx.hour >= 3) & (idx.hour < 21)

    # Stoch(3) NIVEL: entrando sobrevendido (long only)
    sk   = stoch_k(df_tf, k=3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    level_long = (sk < 30) & (sk_p >= 30) & time_ok

    # Filtro W1: RSI semanal > 50 (usa W1 porque 3H no alinea con 4H)
    w1 = resample_ohlcv(m15, 'W')
    w1_bull = (rsi_calc(w1['close'], 14) > 50)
    w1_bull.index = pd.to_datetime(w1_bull.index).tz_localize(None)

    # Filtro D1: RSI diario > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)

    w1v = ffill_to(w1_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values

    long_sig = level_long & w1v & d1v

    sig = np.zeros(n, dtype=np.int8)
    warmup = 100
    sig[warmup:] = np.where(long_sig[warmup:], 1, 0)
    return sig

def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA GANADORA  {TIMEFRAME}  —  XAUUSD")
    print(f"{'='*70}")

    m15 = load_data()
    df  = resample_ohlcv(m15, RESAMPLE)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    print(f"  Datos: {len(df):,} barras  {df.index[0].date()} → {df.index[-1].date()}")

    cache = precompute(df, None)

    dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache['op'][:600], cache['hi'][:600], cache['lo'][:600],
        cache['atr14'][:600], dummy, 0.005, 0.015, 0.5, 2.0, 5, 2,
        cache['day_idx'][:600])

    sig = build_signal(df, m15)
    n_signals = int((sig != 0).sum())
    print(f"  Señales generadas: {n_signals:,}  ({n_signals/MONTHS:.1f} T/mes raw)")

    bt = _bt(cache['op'], cache['hi'], cache['lo'], cache['atr14'],
             sig, RP, 0.015, SLM, TP_R, 5, HOLD, cache['day_idx'])
    m = mets(bt[1][:bt[2]], bt[0])

    print(f"\n  Parámetros usados:")
    print(f"    Stoch(3) nivel + W1+D1 RSI>50 | SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} barras | RP={RP*100:.1f}%")
    print(f"\n  Resultados (10 años, {MONTHS} meses):")
    print(f"    Retorno mensual  : {m['m']:+.2f}%  {'✅' if m['m'] >= 2.0 else '❌'}")
    print(f"    Max Drawdown     : {m['dd']:+.2f}%  {'✅' if m['dd'] >= -7.0 else '❌'}")
    print(f"    Trades/mes       : {m['tpm']:.1f}     {'✅' if m['tpm'] >= 7.0 else '❌'}")
    print(f"    Peor día         : {m['wd']:+.2f}%  {'✅' if m['wd'] >= -3.0 else '❌'}")
    print(f"    Win Rate         : {m['wr']:.1f}%")
    print(f"    Total trades     : {m['n']:,}")
    print(f"    {'PASA OBJETIVOS ✅' if m['passed'] else 'NO PASA ❌'}")
    print(f"{'='*70}\n")
    return m

if __name__ == '__main__':
    run()
