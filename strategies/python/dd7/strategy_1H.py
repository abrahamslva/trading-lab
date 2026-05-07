"""
ESTRATEGIA GANADORA — 1H (1 hora)
==================================
Señal  : sk3_level_h4d1_bidir — Stoch(3) entrando zona sobrevendida
Filtro : 4H RSI > 50  AND  D1 RSI > 50  (alineación multi-TF)
         Sesión activa: 06:00–20:00 UTC (Londres + NY)
Params : slm=0.5 × ATR14 | tp=5.0 × ATR14 | hold=2 barras | rp=0.5%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +4.67%
  Max Drawdown    : -6.45%
  Trades/mes      : 19.9
  Win Rate        : 51.7%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +4.70%  (mediana: +4.27%)
    Desviación estándar      : 4.17%
    Mejor mes                : +18.14%  |  Peor mes: -2.94%
    Max DD mensual promedio  : -1.77%  |  Peor DD mes: -3.91%
    Trades/mes promedio      : 19.0
    Win Rate promedio        : 50.9%
    Peor día promedio        : -0.80%
    Meses positivos          : 111/125 (89%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +5.75%     -1.68%    18.4   54.1%   11    1
    2017      +2.52%     -2.01%    16.3   46.3%    9    3
    2018      +3.35%     -2.19%    18.0   46.2%    8    4
    2019      +3.03%     -1.80%    17.3   47.6%   10    2
    2020      +5.75%     -1.29%    18.2   57.0%   12    0
    2021      +3.73%     -1.44%    16.7   52.2%   12    0
    2022      +5.73%     -1.28%    17.9   54.6%   12    0
    2023      +4.12%     -1.92%    17.8   47.3%   11    1
    2024      +5.10%     -2.12%    21.9   46.3%   12    0
    2025      +7.73%     -1.93%    27.3   57.3%   10    2
    2026      +5.09%     -1.77%    20.6   51.0%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +3.63%   -1.38%      15  53.3%   -1.00% $    3,829,958  ✓
    2023-07   +11.35%   -0.50%      15  66.7%   -0.50% $    4,264,630  ✓
    2023-08    +3.45%   -1.49%      20  50.0%   -1.00% $    4,411,840  ✓
    2023-09    +6.42%   -2.15%      21  38.1%   -1.00% $    4,695,048  ✓
    2023-10    +3.86%   -2.25%      22  45.5%   -1.00% $    4,876,188  ✓
    2023-11    +1.25%   -2.66%      13  30.8%   -1.00% $    4,937,197  ✓
    2023-12    +3.41%   -3.85%      21  38.1%   -1.49% $    5,105,543  ✓
    2024-01    +2.44%   -2.70%      20  40.0%   -1.07% $    5,230,188  ✓
    2024-02    +5.63%   -1.49%      21  47.6%   -0.87% $    5,524,870  ✓
    2024-03    +3.85%   -2.48%      12  41.7%   -0.50% $    5,737,643  ✓
    2024-04    +5.67%   -1.44%      23  52.2%   -0.50% $    6,062,694  ✓
    2024-05    +7.26%   -2.83%      23  47.8%   -1.49% $    6,502,695  ✓
    2024-06    +9.86%   -1.00%      18  55.6%   -1.00% $    7,143,779  ✓
    2024-07    +8.37%   -1.49%      26  50.0%   -1.00% $    7,741,584  ✓
    2024-08    +4.95%   -1.56%      25  52.0%   -1.00% $    8,124,624  ✓
    2024-09    +5.64%   -2.55%      31  45.2%   -1.00% $    8,583,096  ✓
    2024-10    +0.72%   -2.44%      20  40.0%   -1.00% $    8,644,595  ✓
    2024-11    +1.72%   -2.87%      17  35.3%   -1.00% $    8,793,205  ✓
    2024-12    +5.15%   -2.54%      27  48.1%   -0.82% $    9,246,220  ✓
    2025-01    +2.09%   -2.76%      34  50.0%   -1.11% $    9,439,042  ✓
    2025-02    +4.48%   -1.99%      27  55.6%   -1.00% $    9,861,897  ✓
    2025-03   +18.14%   -1.00%      25  76.0%   -1.00% $   11,650,934  ✓
    2025-04    +5.81%   -1.99%      22  59.1%   -1.49% $   12,328,083  ✓
    2025-05    -0.43%   -2.37%      21  38.1%   -1.49% $   12,274,639  ✗
    2025-06    -0.19%   -3.66%      22  45.5%   -1.00% $   12,251,324  ✗
    2025-07   +12.11%   -1.83%      30  66.7%   -0.84% $   13,735,196  ✓
    2025-08   +17.05%   -1.65%      32  65.6%   -1.00% $   16,076,803  ✓
    2025-09    +9.76%   -1.00%      36  63.9%   -0.50% $   17,646,511  ✓
    2025-10    +6.71%   -1.99%      22  54.5%   -1.49% $   18,830,269  ✓
    2025-11   +10.08%   -1.33%      25  56.0%   -1.00% $   20,728,660  ✓
    2025-12    +7.13%   -1.56%      32  56.2%   -1.00% $   22,207,169  ✓
    2026-01   +17.43%   -1.00%      30  70.0%   -1.00% $   26,077,891  ✓
    2026-02    +1.73%   -1.99%      24  50.0%   -1.49% $   26,529,262  ✓
    2026-03    +3.56%   -2.96%      19  47.4%   -1.00% $   27,474,193  ✓
    2026-04    +3.60%   -1.90%      24  54.2%   -0.50% $   28,463,609  ✓
    2026-05    -0.88%   -1.02%       6  33.3%   -0.50% $   28,213,842  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

TIMEFRAME   = '1H'
RESAMPLE    = '1h'
SLM         = 0.5
TP_R        = 5.0
HOLD        = 2
RP          = 0.005
MONTHS      = 123.6

def ema(s, n):   return s.ewm(n, adjust=False).mean()

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

    hour_ok = (idx.hour >= 6) & (idx.hour < 20)
    time_ok = (idx.dayofweek < 5) & hour_ok

    # Stoch(3): señal de NIVEL (precio entrando zona <30 desde arriba)
    sk   = stoch_k(df_tf, k=3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    level_long  = (sk < 30) & (sk_p >= 30) & time_ok   # entrando sobrevendido
    level_short = (sk > 70) & (sk_p <= 70) & time_ok   # entrando sobrecomprado

    h4 = resample_ohlcv(m15, '4h')
    h4_bull = (rsi_calc(h4['close'], 14) > 50)
    h4_bull.index = pd.to_datetime(h4_bull.index).tz_localize(None)

    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)

    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values

    long_sig  = level_long  & h4v & d1v
    short_sig = level_short & ~h4v & ~d1v

    sig = np.zeros(n, dtype=np.int8)
    warmup = 100
    sig[warmup:] = np.where(
        long_sig[warmup:], 1,
        np.where(short_sig[warmup:], -1, 0)
    )
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
    print(f"    Stoch(3) nivel | SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} barras | RP={RP*100:.1f}%")
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
