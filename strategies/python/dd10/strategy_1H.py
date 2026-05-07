"""
ESTRATEGIA ESTRATEGIA DD10% — 1H (DD objetivo: -10.0%)
============================================================
Señal  : Stoch(3) NIVEL entrando zona + 4H/D1 RSI — BIDIRECCIONAL
Params : slm=0.7 × ATR14 | tp=5.0 × ATR14 | hold=2 barras | rp=0.8%

Resultado backtest 10 años (2016-01-04 → 2026-05-06, 123.6 meses):
  Retorno mensual : +6.74%
  Max Drawdown    : -8.75%
  Trades/mes      : 31.2
  Win Rate        : 53.3%
  Estado          : PASA OBJETIVOS ✅

NOTA: Misma señal que estrategia base, solo se ajustan SLM y RP
      para alcanzar el objetivo de DD de -10.0%.
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (123.6 meses)
  ====================================================================
    Retorno mensual promedio : +5.29%  (mediana: +4.57%)
    Desviación estándar      : 5.36%
    Mejor mes                : +23.00%  |  Peor mes: -5.05%
    Max DD mensual promedio  : -2.40%  |  Peor DD mes: -6.08%
    Trades/mes promedio      : 18.8
    Win Rate promedio        : 53.8%
    Peor día promedio        : -1.13%
    Meses positivos          : 105/125 (84%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      +6.20%     -2.05%    18.2   56.0%   11    1
    2017      +2.98%     -2.71%    16.0   50.0%    8    4
    2018      +3.26%     -3.08%    17.8   50.5%    8    4
    2019      +2.84%     -2.72%    17.2   48.5%    9    3
    2020      +6.33%     -1.79%    18.1   59.1%   11    1
    2021      +4.47%     -2.11%    16.3   55.0%   10    2
    2022      +5.60%     -1.95%    17.8   58.4%   11    1
    2023      +5.17%     -2.64%    17.7   48.9%   11    1
    2024      +6.40%     -2.62%    21.3   50.6%   11    1
    2025      +9.52%     -2.45%    27.0   61.6%   11    1
    2026      +5.63%     -2.12%    19.8   53.9%    4    1

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +3.20%   -2.26%      15  53.3%   -1.59% $    4,512,961  ✓
    2023-07   +13.51%   -0.80%      15  66.7%   -0.80% $    5,122,824  ✓
    2023-08    +2.44%   -2.38%      20  50.0%   -1.59% $    5,247,994  ✓
    2023-09   +12.13%   -2.46%      21  47.6%   -1.59% $    5,884,644  ✓
    2023-10    +2.39%   -3.82%      22  45.5%   -1.59% $    6,025,448  ✓
    2023-11    +4.70%   -3.85%      13  30.8%   -1.59% $    6,308,417  ✓
    2023-12    +8.37%   -3.87%      20  40.0%   -1.59% $    6,836,513  ✓
    2024-01    +1.34%   -3.28%      20  45.0%   -1.68% $    6,927,829  ✓
    2024-02    +8.87%   -2.38%      21  52.4%   -1.22% $    7,542,391  ✓
    2024-03    +6.93%   -3.94%      12  41.7%   -0.80% $    8,065,237  ✓
    2024-04    +5.42%   -1.96%      23  56.5%   -0.80% $    8,502,119  ✓
    2024-05   +10.60%   -3.35%      20  50.0%   -1.59% $    9,403,651  ✓
    2024-06   +12.97%   -0.98%      17  58.8%   -0.98% $   10,623,202  ✓
    2024-07    +8.92%   -2.38%      26  53.8%   -1.59% $   11,571,154  ✓
    2024-08    +3.88%   -2.69%      25  52.0%   -1.59% $   12,020,026  ✓
    2024-09   +12.00%   -1.59%      30  60.0%   -1.13% $   13,462,422  ✓
    2024-10    +1.34%   -1.81%      19  47.4%   -0.80% $   13,642,761  ✓
    2024-11    -0.03%   -4.03%      17  35.3%   -1.59% $   13,638,940  ✗
    2024-12    +4.57%   -3.09%      26  53.8%   -1.17% $   14,262,710  ✓
    2025-01    +4.32%   -2.28%      34  64.7%   -1.59% $   14,878,157  ✓
    2025-02    +4.21%   -2.77%      27  59.3%   -1.59% $   15,505,043  ✓
    2025-03   +22.85%   -1.11%      25  76.0%   -1.11% $   19,047,736  ✓
    2025-04    +5.09%   -2.45%      22  59.1%   -1.66% $   20,016,917  ✓
    2025-05    -1.53%   -2.97%      20  40.0%   -1.59% $   19,709,860  ✗
    2025-06    +2.46%   -5.34%      22  59.1%   -1.59% $   20,193,848  ✓
    2025-07   +16.41%   -1.82%      30  66.7%   -1.19% $   23,508,541  ✓
    2025-08   +23.00%   -2.00%      31  71.0%   -1.19% $   28,914,426  ✓
    2025-09    +8.44%   -1.70%      36  63.9%   -0.91% $   31,353,752  ✓
    2025-10    +7.87%   -2.38%      20  60.0%   -1.59% $   33,820,000  ✓
    2025-11   +12.50%   -2.42%      25  60.0%   -1.59% $   38,047,442  ✓
    2025-12    +8.64%   -2.15%      32  59.4%   -1.28% $   41,335,679  ✓
    2026-01   +17.97%   -1.72%      29  72.4%   -1.59% $   48,763,147  ✓
    2026-02    +2.48%   -2.02%      22  54.5%   -1.59% $   49,970,733  ✓
    2026-03    +5.14%   -3.43%      19  52.6%   -1.07% $   52,537,108  ✓
    2026-04    +4.48%   -1.37%      23  56.5%   -0.80% $   54,893,053  ✓
    2026-05    -1.91%   -2.07%       6  33.3%   -0.80% $   53,844,046  ✗

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
SLM         = 0.7
TP_R        = 5.0
HOLD        = 2
RP          = 0.008
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
