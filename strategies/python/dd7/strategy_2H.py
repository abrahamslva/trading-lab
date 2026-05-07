"""
ESTRATEGIA GANADORA — 2H (2 horas)
====================================
Señal  : sk3_cross_h4d1_bidir — Stoch(3) cruzando hacia arriba desde sobrevendido
Filtro : 4H RSI > 50  AND  D1 RSI > 50  (alineación multi-TF)
         Sesión activa: 04:00–21:00 UTC
Params : slm=0.5 × ATR14 | tp=3.0 × ATR14 | hold=2 barras | rp=0.5%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.02%
  Max Drawdown    : -5.77%
  Trades/mes      : 12.0
  Win Rate        : 48.8%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.03%  (mediana: +1.97%)
    Desviación estándar      : 2.64%
    Mejor mes                : +9.63%  |  Peor mes: -3.74%
    Max DD mensual promedio  : -1.45%  |  Peor DD mes: -4.53%
    Trades/mes promedio      : 11.9
    Win Rate promedio        : 48.4%
    Peor día promedio        : -0.66%
    Meses positivos          : 94/125 (75%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +1.84%     -1.75%    13.0   44.2%    8    4
    2017      +1.47%     -1.62%    11.0   45.3%    9    3
    2018      +2.63%     -1.49%    10.9   50.6%    8    4
    2019      +1.37%     -1.64%    12.0   45.8%   10    2
    2020      +1.35%     -1.50%    11.7   46.7%    9    3
    2021      +1.63%     -1.45%    12.6   48.0%    9    3
    2022      +1.66%     -1.58%    11.9   45.5%    6    6
    2023      +3.24%     -1.13%    12.7   54.4%   11    1
    2024      +2.73%     -1.47%    12.4   49.4%   10    2
    2025      +2.41%     -1.12%    11.9   52.8%   10    2
    2026      +1.98%     -0.76%     8.4   52.6%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +4.87%   -1.00%      13  69.2%   -0.50% $      488,431  ✓
    2023-07    +0.81%   -0.56%       7  42.9%   -0.50% $      492,393  ✓
    2023-08    +5.62%   -1.49%      15  46.7%   -1.00% $      520,088  ✓
    2023-09    +9.63%   -0.67%      19  73.7%   -0.17% $      570,199  ✓
    2023-10    +2.92%   -1.00%      13  69.2%   -0.50% $      586,870  ✓
    2023-11    +0.56%   -1.00%       8  50.0%   -1.00% $      590,146  ✓
    2023-12    -0.14%   -1.61%      16  43.8%   -1.00% $      589,342  ✗
    2024-01    +4.10%   -1.00%      11  63.6%   -0.50% $      613,521  ✓
    2024-02    -0.10%   -2.53%       9  33.3%   -1.00% $      612,907  ✗
    2024-03    -1.96%   -2.21%       7  28.6%   -1.00% $      600,907  ✗
    2024-04    +3.18%   -1.00%      11  45.5%   -0.50% $      620,015  ✓
    2024-05    +1.99%   -1.36%      11  54.5%   -1.00% $      632,358  ✓
    2024-06    +1.71%   -1.00%      11  45.5%   -0.86% $      643,184  ✓
    2024-07    +1.16%   -1.55%      11  54.5%   -0.50% $      650,677  ✓
    2024-08    +9.42%   -1.00%      19  68.4%   -0.50% $      711,948  ✓
    2024-09    +2.85%   -1.54%      13  53.8%   -1.05% $      732,263  ✓
    2024-10    +1.43%   -1.92%      16  31.2%   -1.00% $      742,721  ✓
    2024-11    +2.85%   -1.00%      12  58.3%   -0.50% $      763,919  ✓
    2024-12    +6.08%   -1.49%      18  55.6%   -0.50% $      810,345  ✓
    2025-01    -1.36%   -2.00%      12  33.3%   -0.50% $      799,339  ✗
    2025-02    +2.12%   -0.56%      13  46.2%   -0.50% $      816,294  ✓
    2025-03    +1.19%   -0.54%       8  62.5%   -0.50% $      826,028  ✓
    2025-04    +1.97%   -1.00%      11  54.5%   -0.50% $      842,275  ✓
    2025-05    +2.96%   -1.57%      13  46.2%   -1.00% $      867,230  ✓
    2025-06    +6.20%   -1.00%      16  62.5%   -1.00% $      921,012  ✓
    2025-07    -0.64%   -1.76%      12  33.3%   -1.00% $      915,072  ✗
    2025-08    +1.33%   -1.76%      15  40.0%   -0.77% $      927,213  ✓
    2025-09    +6.67%   -0.69%      10  80.0%   -0.19% $      989,021  ✓
    2025-10    +4.45%   -0.50%      11  72.7%   -0.50% $    1,033,060  ✓
    2025-11    +2.70%   -1.11%      13  46.2%   -0.70% $    1,060,950  ✓
    2025-12    +1.30%   -0.97%       9  55.6%   -0.50% $    1,074,733  ✓
    2026-01    +0.10%   -0.56%       6  50.0%   -0.50% $    1,075,834  ✓
    2026-02    +3.05%   -0.50%       8  75.0%   -0.50% $    1,108,678  ✓
    2026-03    +2.67%   -1.28%      13  46.2%   -0.50% $    1,138,250  ✓
    2026-04    +4.22%   -0.71%      12  58.3%   -0.50% $    1,186,290  ✓
    2026-05    -0.15%   -0.73%       3  33.3%    0.00% $    1,184,458  ✗

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
SLM         = 0.5
TP_R        = 3.0
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

    time_ok = (idx.dayofweek < 5) & (idx.hour >= 4) & (idx.hour < 21)

    # Stoch(3) CRUCE: cruza hacia arriba a través de 20 (saliendo de sobrevendido)
    sk   = stoch_k(df_tf, k=3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    cross_long  = (sk > 20) & (sk_p <= 20) & time_ok
    cross_short = (sk < 80) & (sk_p >= 80) & time_ok

    h4 = resample_ohlcv(m15, '4h')
    h4_bull = (rsi_calc(h4['close'], 14) > 50)
    h4_bull.index = pd.to_datetime(h4_bull.index).tz_localize(None)

    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)

    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values

    long_sig  = cross_long  & h4v & d1v
    short_sig = cross_short & ~h4v & ~d1v

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
    print(f"    Stoch(3) cruce | SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} barras | RP={RP*100:.1f}%")
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
