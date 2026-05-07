"""
ESTRATEGIA GANADORA — M15 (15 minutos)
=======================================
Señal  : rsirsi_bidir — Stoch(14) crossup desde sobrevendido
Filtro : 4H RSI > 50  AND  D1 RSI > 50  (alineación multi-TF)
         Sesión activa: 06:00–20:00 UTC (Londres + NY)
Params : slm=0.8 × ATR14 | tp=5.0 × ATR14 | hold=12 barras | rp=0.3%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +4.05%
  Max Drawdown    : -6.67%
  Trades/mes      : 30.9
  Win Rate        : 37.1%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +4.05%  (mediana: +3.94%)
    Desviación estándar      : 3.70%
    Mejor mes                : +13.86%  |  Peor mes: -2.33%
    Max DD mensual promedio  : -2.00%  |  Peor DD mes: -4.48%
    Trades/mes promedio      : 30.6
    Win Rate promedio        : 37.2%
    Peor día promedio        : -1.05%
    Meses positivos          : 109/125 (87%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +6.26%     -1.60%    28.8   41.9%   12    0
    2017      +3.10%     -1.85%    26.1   35.3%   11    1
    2018      +2.13%     -2.11%    26.6   33.7%    8    4
    2019      +3.07%     -2.07%    27.2   37.9%   11    1
    2020      +4.56%     -1.53%    26.0   42.2%   12    0
    2021      +3.62%     -1.99%    29.7   35.0%   10    2
    2022      +6.69%     -1.76%    30.2   40.7%   11    1
    2023      +4.54%     -1.76%    28.7   36.5%   11    1
    2024      +2.21%     -2.73%    36.6   31.5%    8    4
    2025      +5.16%     -2.57%    44.8   39.6%   12    0
    2026      +2.11%     -2.14%    34.0   32.0%    3    2

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +3.20%   -1.19%      23  34.8%   -0.90% $    3,892,361  ✓
    2023-07    +2.68%   -1.19%      19  36.8%   -0.90% $    3,996,484  ✓
    2023-08    +5.81%   -2.08%      39  33.3%   -0.90% $    4,228,678  ✓
    2023-09    +9.32%   -1.19%      29  44.8%   -0.90% $    4,622,819  ✓
    2023-10    +7.82%   -1.51%      33  42.4%   -1.19% $    4,984,373  ✓
    2023-11    +3.02%   -2.56%      28  32.1%   -1.19% $    5,134,984  ✓
    2023-12    -0.20%   -3.69%      28  25.0%   -1.19% $    5,124,523  ✗
    2024-01    +4.95%   -1.79%      30  40.0%   -1.49% $    5,377,935  ✓
    2024-02    -1.16%   -4.04%      27  22.2%   -1.55% $    5,315,708  ✗
    2024-03    +5.70%   -1.79%      24  41.7%   -1.19% $    5,618,742  ✓
    2024-04    +1.06%   -2.78%      35  28.6%   -1.19% $    5,678,043  ✓
    2024-05    -2.11%   -2.70%      35  25.7%   -1.49% $    5,558,077  ✗
    2024-06    +1.91%   -4.12%      29  24.1%   -1.49% $    5,664,427  ✓
    2024-07    +1.29%   -3.40%      50  32.0%   -1.49% $    5,737,463  ✓
    2024-08    +3.94%   -2.28%      48  37.5%   -1.05% $    5,963,364  ✓
    2024-09    +6.32%   -1.79%      47  42.6%   -1.49% $    6,340,447  ✓
    2024-10    -0.49%   -2.18%      42  26.2%   -1.49% $    6,309,322  ✗
    2024-11    -2.33%   -4.41%      29  20.7%   -1.49% $    6,162,390  ✗
    2024-12    +7.38%   -1.52%      43  37.2%   -1.49% $    6,616,948  ✓
    2025-01    +3.32%   -2.08%      56  28.6%   -1.49% $    6,836,308  ✓
    2025-02    +8.65%   -2.46%      40  52.5%   -1.49% $    7,427,500  ✓
    2025-03   +13.86%   -0.90%      38  60.5%   -0.90% $    8,456,695  ✓
    2025-04    +0.72%   -3.22%      46  37.0%   -1.49% $    8,517,758  ✓
    2025-05    +0.60%   -3.20%      38  36.8%   -1.49% $    8,568,649  ✓
    2025-06    +4.17%   -2.07%      39  38.5%   -0.90% $    8,926,059  ✓
    2025-07    +4.07%   -2.81%      45  33.3%   -1.19% $    9,289,087  ✓
    2025-08    +8.97%   -2.43%      46  39.1%   -1.19% $   10,122,230  ✓
    2025-09    +0.55%   -4.48%      45  28.9%   -1.49% $   10,178,198  ✓
    2025-10    +8.25%   -1.62%      47  46.8%   -0.99% $   11,017,467  ✓
    2025-11    +1.92%   -2.54%      41  31.7%   -0.90% $   11,229,145  ✓
    2025-12    +6.78%   -3.02%      56  41.1%   -1.49% $   11,990,137  ✓
    2026-01    +9.32%   -1.33%      45  51.1%   -1.19% $   13,108,065  ✓
    2026-02    -0.86%   -2.33%      44  27.3%   -1.49% $   12,994,753  ✗
    2026-03    +2.55%   -2.96%      36  33.3%   -1.49% $   13,325,567  ✓
    2026-04    +0.83%   -2.27%      38  34.2%   -1.12% $   13,435,680  ✓
    2026-05    -1.27%   -1.79%       7  14.3%   -1.49% $   13,265,284  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
import numpy as np
import pandas as pd
import warnings

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

# ── Parámetros confirmados ────────────────────────────────────────────────────
TIMEFRAME   = 'M15'
RESAMPLE    = None          # M15 es el TF base del parquet
SLM         = 0.8           # multiplicador stop-loss (× ATR14)
TP_R        = 5.0           # take-profit ratio (× ATR14)
HOLD        = 12            # máximo de barras a mantener la posición
RP          = 0.003         # riesgo por operación (0.3% del equity)
MONTHS      = 123.6

# ── Helpers ───────────────────────────────────────────────────────────────────
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
        {'open': 'first', 'high': 'max', 'low': 'min',
         'close': 'last', 'volume': 'sum'}
    ).dropna()

def ffill_to(series, target_index):
    s = series.copy()
    if hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s.reindex(target_index, method='ffill').fillna(False)

# ── Carga de datos ────────────────────────────────────────────────────────────
def load_data(path='data/dukascopy/XAUUSD_15min_mt5.parquet'):
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

# ── Construcción de señal ─────────────────────────────────────────────────────
def build_signal(df, m15):
    idx  = df.index
    n    = len(df)

    # Filtro temporal: sesión Londres + NY
    hour_ok = (idx.hour >= 6) & (idx.hour < 20)
    time_ok = (idx.dayofweek < 5) & hour_ok

    # Señal base: stoch(14) cruzando hacia arriba desde sobrevendido
    sk   = stoch_k(df, 14).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long  = (sk > 20) & (sk_p <= 20) & time_ok
    stoch_short = (sk < 80) & (sk_p >= 80) & time_ok

    # Referencia: 4H RSI > 50
    h4 = resample_ohlcv(m15, '4h')
    h4_bull = (rsi_calc(h4['close'], 14) > 50)
    h4_bull.index = pd.to_datetime(h4_bull.index).tz_localize(None)

    # Referencia: D1 RSI > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)

    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values

    # Señal larga: stoch cruzando + ambos filtros alcistas
    long_sig  = stoch_long  & h4v & d1v
    # Señal corta: stoch cruzando + ambos filtros bajistas
    short_sig = stoch_short & ~h4v & ~d1v

    sig = np.zeros(n, dtype=np.int8)
    warmup = 300
    sig[warmup:] = np.where(
        long_sig[warmup:], 1,
        np.where(short_sig[warmup:], -1, 0)
    )
    return sig

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA GANADORA  {TIMEFRAME}  —  XAUUSD")
    print(f"{'='*70}")

    m15 = load_data()
    df  = m15.copy()  # M15 es el TF objetivo
    print(f"  Datos: {len(df):,} barras  {df.index[0].date()} → {df.index[-1].date()}")

    cache = precompute(df, RESAMPLE)

    # Warmup Numba
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
    print(f"    SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} barras | RP={RP*100:.1f}%")
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
