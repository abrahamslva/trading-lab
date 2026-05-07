"""
ESTRATEGIA GANADORA — 4H (4 horas)
====================================
Señal  : sk3_level_d1only_LO — Stoch(3) entrando zona sobrevendida (long only)
Filtro : D1 RSI > 50  (solo tendencia diaria alcista)
         Nota: no se usa filtro 4H porque sería auto-referencial en este TF
Params : slm=0.5 × ATR14 | tp=2.5 × ATR14 | hold=2 barras | rp=0.8%

Resultado en 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +2.60%
  Max Drawdown    : -6.43%
  Trades/mes      : 9.2
  Win Rate        : 52.1%
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +2.63%  (mediana: +1.81%)
    Desviación estándar      : 3.52%
    Mejor mes                : +13.44%  |  Peor mes: -3.36%
    Max DD mensual promedio  : -1.72%  |  Peor DD mes: -5.46%
    Trades/mes promedio      : 9.1
    Win Rate promedio        : 48.1%
    Peor día promedio        : -0.75%
    Meses positivos          : 90/125 (72%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +2.55%     -1.89%     8.2   40.9%    8    4
    2017      +2.37%     -2.28%    10.2   53.9%   10    2
    2018      +1.34%     -1.74%     7.4   36.2%    7    5
    2019      +2.22%     -1.54%     9.8   50.2%   10    2
    2020      +3.61%     -1.59%    10.0   59.2%   11    1
    2021      +1.51%     -1.72%     7.3   38.3%    8    4
    2022      +2.18%     -1.88%     7.9   33.0%    7    5
    2023      +2.53%     -1.67%     9.2   49.8%    7    5
    2024      +2.58%     -1.62%     9.3   62.0%    8    4
    2025      +4.35%     -1.82%    12.6   52.8%   10    2
    2026      +5.30%     -0.48%     6.6   59.4%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $      682,909  ✗
    2023-07    +1.18%   -3.51%      11  45.5%   -0.80% $      690,976  ✓
    2023-08    +5.74%    0.00%       2 100.0%    0.00% $      730,665  ✓
    2023-09    -0.62%   -2.38%       7  28.6%   -0.80% $      726,157  ✗
    2023-10    +7.40%   -0.98%      10  60.0%   -0.80% $      779,888  ✓
    2023-11    +5.53%   -1.59%      12  58.3%   -0.80% $      823,040  ✓
    2023-12    +2.41%   -1.64%      14  57.1%   -1.59% $      842,834  ✓
    2024-01    +3.63%   -0.75%       5  60.0%   -0.57% $      873,417  ✓
    2024-02    +7.43%   -1.59%       9  77.8%   -0.80% $      938,282  ✓
    2024-03    -3.33%   -4.04%      11  36.4%   -0.80% $      907,055  ✗
    2024-04    +8.70%   -2.29%      19  52.6%   -0.80% $      986,008  ✓
    2024-05    -3.36%   -3.36%       8  25.0%   -1.59% $      952,898  ✗
    2024-06    +2.00%    0.00%       1 100.0%    0.00% $      971,956  ✓
    2024-07    +3.32%   -1.82%      13  46.2%   -0.80% $    1,004,220  ✓
    2024-08    +7.51%   -1.59%      11  63.6%   -0.80% $    1,079,644  ✓
    2024-09    +5.84%   -0.80%      15  60.0%   -0.80% $    1,142,659  ✓
    2024-10    -0.85%   -2.38%      16  56.2%   -0.80% $    1,132,931  ✗
    2024-11    -0.06%   -0.80%       3  66.7%   -0.80% $    1,132,278  ✗
    2024-12    +0.10%    0.00%       1 100.0%    0.00% $    1,133,379  ✓
    2025-01    -2.64%   -3.97%      13  23.1%   -1.59% $    1,103,461  ✗
    2025-02    -0.17%   -1.67%      15  40.0%   -0.80% $    1,101,575  ✗
    2025-03    +8.58%   -0.80%      14  71.4%   -0.80% $    1,196,108  ✓
    2025-04    +1.00%   -1.41%      14  42.9%   -0.80% $    1,208,025  ✓
    2025-05    +0.97%   -1.61%      10  50.0%   -0.80% $    1,219,685  ✓
    2025-06   +12.75%   -0.80%      12  75.0%   -0.80% $    1,375,223  ✓
    2025-07    +1.74%   -1.59%      11  54.5%   -0.80% $    1,399,102  ✓
    2025-08    +0.32%   -3.94%      10  30.0%   -0.80% $    1,403,562  ✓
    2025-09    +8.00%   -1.10%      10  60.0%   -0.80% $    1,515,884  ✓
    2025-10   +10.76%   -1.59%      11  72.7%   -0.80% $    1,678,979  ✓
    2025-11    +3.21%   -1.75%      11  63.6%   -0.80% $    1,732,791  ✓
    2025-12    +7.70%   -1.59%      20  50.0%   -0.80% $    1,866,202  ✓
    2026-01   +13.44%   -0.80%      13  84.6%   -0.80% $    2,116,936  ✓
    2026-02    +8.05%    0.00%      10 100.0%    0.00% $    2,287,259  ✓
    2026-03    +4.60%   -0.80%       8  62.5%   -0.80% $    2,392,391  ✓
    2026-04    +0.41%   -0.80%       2  50.0%   -0.80% $    2,402,119  ✓
    2026-05    +0.00%    0.00%       0   0.0%    0.00% $    2,402,119  ✗

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
SLM         = 0.5
TP_R        = 2.5
HOLD        = 2
RP          = 0.008
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

    time_ok = (idx.dayofweek < 5)

    # Stoch(3) NIVEL: entrando sobrevendido (long only)
    sk   = stoch_k(df_tf, k=3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    level_long = (sk < 30) & (sk_p >= 30) & time_ok

    d1 = resample_ohlcv(m15, 'D')
    d1_bull = (rsi_calc(d1['close'], 14) > 50)
    d1_bull.index = pd.to_datetime(d1_bull.index).tz_localize(None)
    d1v = ffill_to(d1_bull, idx).values

    long_sig = level_long & d1v

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
    print(f"    Stoch(3) nivel (Long Only) | SLM={SLM}×ATR | TP={TP_R}×ATR | Hold={HOLD} barras | RP={RP*100:.1f}%")
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
