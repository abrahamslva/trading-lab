"""
ESTRATEGIA ESTRATEGIA DD5% — 1H (DD objetivo: -5.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando zona + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.2 × ATR14 | tp=5.0 × ATR14 | hold=2 barras | rp=0.3%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +9.40%
  Max Drawdown    : -4.03%
  Trades/mes      : 33.0
  Win Rate        : 41.6%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -5.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +6.38%  (mediana: +5.78%)
    Desviación estándar      : 4.83%
    Mejor mes                : +23.43%  |  Peor mes: -1.72%
    Max DD mensual promedio  : -1.29%  |  Peor DD mes: -3.07%
    Trades/mes promedio      : 19.5
    Win Rate promedio        : 42.8%
    Peor día promedio        : -0.59%
    Meses positivos          : 119/125 (95%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +7.04%     -1.28%    18.8   46.6%   12    0
    2017      +3.78%     -1.44%    16.5   39.2%   10    2
    2018      +5.44%     -1.38%    18.4   38.4%   10    2
    2019      +4.84%     -1.17%    17.8   41.1%   12    0
    2020      +7.59%     -0.95%    18.7   49.1%   12    0
    2021      +5.80%     -1.11%    17.0   43.9%   12    0
    2022      +8.33%     -1.00%    18.6   48.4%   12    0
    2023      +4.37%     -1.38%    17.8   37.2%   10    2
    2024      +5.95%     -1.60%    22.6   38.1%   12    0
    2025     +10.68%     -1.60%    28.6   46.6%   12    0
    2026      +6.26%     -1.24%    20.6   40.4%    5    0

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +2.59%   -0.73%      15  46.7%   -0.60% $   17,475,586  ✓
    2023-07    +9.13%   -0.60%      15  53.3%   -0.30% $   19,070,332  ✓
    2023-08    +6.25%   -0.90%      20  40.0%   -0.60% $   20,261,837  ✓
    2023-09    +2.59%   -1.44%      21  33.3%   -0.60% $   20,786,311  ✓
    2023-10    +0.96%   -2.16%      22  27.3%   -0.60% $   20,986,066  ✓
    2023-11    -0.37%   -1.08%      13  23.1%   -0.60% $   20,908,779  ✗
    2023-12    +8.99%   -2.18%      22  45.5%   -0.90% $   22,787,471  ✓
    2024-01    +4.75%   -2.37%      20  35.0%   -0.30% $   23,870,491  ✓
    2024-02    +8.07%   -0.90%      21  42.9%   -0.60% $   25,797,932  ✓
    2024-03    +1.90%   -1.49%      13  30.8%   -0.30% $   26,289,201  ✓
    2024-04    +6.28%   -1.49%      23  43.5%   -0.30% $   27,940,400  ✓
    2024-05    +3.70%   -2.68%      23  30.4%   -0.90% $   28,973,957  ✓
    2024-06    +4.42%   -1.08%      19  42.1%   -0.60% $   30,253,268  ✓
    2024-07   +12.95%   -0.90%      26  50.0%   -0.60% $   34,171,345  ✓
    2024-08    +5.81%   -1.15%      25  44.0%   -0.60% $   36,157,279  ✓
    2024-09    +7.67%   -1.79%      32  37.5%   -0.90% $   38,930,613  ✓
    2024-10    +4.14%   -2.08%      23  30.4%   -0.60% $   40,541,778  ✓
    2024-11    +3.30%   -1.49%      17  29.4%   -0.60% $   41,881,353  ✓
    2024-12    +8.36%   -1.82%      29  41.4%   -0.60% $   45,382,414  ✓
    2025-01    +2.61%   -2.96%      37  29.7%   -1.19% $   46,565,204  ✓
    2025-02    +6.23%   -1.79%      27  40.7%   -0.60% $   49,465,535  ✓
    2025-03   +17.33%   -0.90%      25  60.0%   -0.60% $   58,036,930  ✓
    2025-04    +7.71%   -1.49%      24  45.8%   -1.19% $   62,509,459  ✓
    2025-05    +0.11%   -2.52%      22  22.7%   -0.90% $   62,580,407  ✓
    2025-06    +2.98%   -2.36%      22  36.4%   -0.60% $   64,446,163  ✓
    2025-07   +13.85%   -1.49%      34  55.9%   -0.90% $   73,372,199  ✓
    2025-08   +23.43%   -1.49%      33  60.6%   -0.60% $   90,561,179  ✓
    2025-09   +20.92%   -0.60%      38  63.2%   -0.30% $  109,504,138  ✓
    2025-10   +12.77%   -1.19%      22  54.5%   -0.90% $  123,485,645  ✓
    2025-11   +12.39%   -0.90%      25  52.0%   -0.60% $  138,782,778  ✓
    2025-12    +7.83%   -1.49%      34  38.2%   -0.60% $  149,650,891  ✓
    2026-01   +21.78%   -0.60%      30  63.3%   -0.60% $  182,247,614  ✓
    2026-02    +4.70%   -1.27%      24  41.7%   -0.90% $  190,819,070  ✓
    2026-03    +1.42%   -2.08%      19  26.3%   -0.90% $  193,521,354  ✓
    2026-04    +2.89%   -1.64%      24  37.5%   -0.60% $  199,105,315  ✓
    2026-05    +0.51%   -0.60%       6  33.3%   -0.30% $  200,111,855  ✓

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
SLM         = 0.2
TP_R        = 5.0
HOLD        = 2
RP          = 0.003
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
    stoch_long  = (sk < 30) & (sk_p >= 30) & time_ok
    stoch_short = (sk > 70) & (sk_p <= 70) & time_ok
    h4 = resample_ohlcv(m15, '4h')
    h4_bull = rsi_calc(h4['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    sig[75:] = np.where(
        stoch_long[75:] & h4v[75:] & d1v[75:], 1,
        np.where(stoch_short[75:] & ~h4v[75:] & ~d1v[75:], -1, 0)
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
