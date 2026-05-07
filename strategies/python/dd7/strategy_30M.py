"""
ESTRATEGIA GANADORA — 30M (30 minutos)
=======================================
Señal  : rsirsi_bidir — Stoch(14) crossup desde sobrevendido
Filtro : 4H RSI > 50  AND  D1 RSI > 50  (alineación multi-TF)
         Sesión activa: 06:00–20:00 UTC (Londres + NY)
Params : slm=1.0 × ATR14 | tp=3.0 × ATR14 | hold=24 barras | rp=0.5%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.48%
  Max Drawdown    : -6.78%
  Trades/mes      : 14.5
  Win Rate        : 37.2%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.50%  (mediana: +2.30%)
    Desviación estándar      : 3.35%
    Mejor mes                : +14.89%  |  Peor mes: -4.16%
    Max DD mensual promedio  : -2.17%  |  Peor DD mes: -5.91%
    Trades/mes promedio      : 14.4
    Win Rate promedio        : 36.7%
    Peor día promedio        : -1.02%
    Meses positivos          : 94/125 (75%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +1.90%     -2.45%    13.6   33.2%    8    4
    2017      +2.50%     -2.16%    12.6   36.7%    7    5
    2018      +2.23%     -1.85%    11.4   38.6%    8    4
    2019      +2.42%     -2.13%    12.7   38.7%    9    3
    2020      +1.32%     -1.95%    13.2   34.3%    8    4
    2021      +1.21%     -2.20%    14.6   31.3%    7    5
    2022      +2.86%     -2.12%    15.9   36.9%   11    1
    2023      +4.01%     -1.73%    14.4   39.2%   10    2
    2024      +2.66%     -2.74%    17.4   38.2%   10    2
    2025      +4.18%     -2.38%    18.1   41.1%   12    0
    2026      +1.92%     -2.03%    13.6   33.7%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +3.14%   -1.99%      15  46.7%   -1.00% $      593,271  ✓
    2023-07    +3.79%   -1.00%      11  45.5%   -1.00% $      615,767  ✓
    2023-08    +7.28%   -1.49%      23  43.5%   -1.00% $      660,606  ✓
    2023-09   +10.29%   -1.49%      16  62.5%   -1.00% $      728,562  ✓
    2023-10   +10.20%   -1.89%      17  58.8%   -1.00% $      802,846  ✓
    2023-11    +2.90%   -1.49%      12  41.7%   -1.00% $      826,109  ✓
    2023-12    +2.14%   -1.83%      13  38.5%   -1.00% $      843,774  ✓
    2024-01    -0.87%   -4.41%      16  25.0%   -1.49% $      836,404  ✗
    2024-02    +2.48%   -1.49%      11  36.4%   -0.50% $      857,121  ✓
    2024-03    +1.96%   -3.45%      12  33.3%   -1.49% $      873,959  ✓
    2024-04    +0.77%   -2.73%      14  42.9%   -0.50% $      880,709  ✓
    2024-05    -4.16%   -5.91%      22  18.2%   -1.07% $      844,079  ✗
    2024-06    +3.88%   -1.16%      10  50.0%   -1.00% $      876,818  ✓
    2024-07    +6.99%   -2.22%      22  45.5%   -1.00% $      938,115  ✓
    2024-08    +5.34%   -3.12%      24  45.8%   -1.00% $      988,219  ✓
    2024-09    +4.51%   -1.99%      21  47.6%   -1.61% $    1,032,753  ✓
    2024-10    +1.74%   -1.99%      19  31.6%   -1.00% $    1,050,722  ✓
    2024-11    +3.59%   -3.04%      14  35.7%   -1.49% $    1,088,409  ✓
    2024-12    +5.71%   -1.37%      24  45.8%   -1.00% $    1,150,507  ✓
    2025-01    +4.58%   -2.96%      24  37.5%   -1.49% $    1,203,220  ✓
    2025-02    +5.13%   -1.99%      19  42.1%   -1.49% $    1,264,919  ✓
    2025-03    +6.13%   -1.00%      11  54.5%   -1.00% $    1,342,429  ✓
    2025-04    +0.44%   -1.99%      20  35.0%   -1.49% $    1,348,357  ✓
    2025-05    +6.67%   -1.49%      12  58.3%   -0.50% $    1,438,336  ✓
    2025-06    +6.62%   -1.99%      17  47.1%   -1.00% $    1,533,541  ✓
    2025-07    +1.92%   -3.93%      24  29.2%   -1.49% $    1,562,968  ✓
    2025-08    +4.90%   -2.56%      22  36.4%   -0.50% $    1,639,576  ✓
    2025-09    +3.48%   -3.95%      17  35.3%   -1.49% $    1,696,608  ✓
    2025-10    +1.48%   -1.73%      15  40.0%   -1.00% $    1,721,722  ✓
    2025-11    +3.43%   -2.96%      16  37.5%   -1.00% $    1,780,859  ✓
    2025-12    +5.43%   -1.99%      20  40.0%   -1.00% $    1,877,473  ✓
    2026-01    +0.96%   -3.23%      17  29.4%   -1.49% $    1,895,440  ✓
    2026-02    +6.74%   -1.99%      21  42.9%   -1.49% $    2,023,105  ✓
    2026-03    +0.42%   -1.78%      16  31.2%   -1.00% $    2,031,568  ✓
    2026-04    +1.80%   -1.66%      10  40.0%   -1.00% $    2,068,190  ✓
    2026-05    -0.30%   -1.49%       4  25.0%   -1.49% $    2,061,928  ✗

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
TIMEFRAME   = '30M'
RESAMPLE    = '30min'
SLM         = 1.0
TP_R        = 3.0
HOLD        = 24
RP          = 0.005
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

    sk   = stoch_k(df_tf, 14).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long  = (sk > 20) & (sk_p <= 20) & time_ok
    stoch_short = (sk < 80) & (sk_p >= 80) & time_ok

    h4 = resample_ohlcv(m15, '4h')
    h4_bull = (rsi_calc(h4['close'], 14) > 50)
    h4_bull.index = pd.to_datetime(h4_bull.index).tz_localize(None)

    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)

    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values

    long_sig  = stoch_long  & h4v & d1v
    short_sig = stoch_short & ~h4v & ~d1v

    sig = np.zeros(n, dtype=np.int8)
    warmup = 200
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
