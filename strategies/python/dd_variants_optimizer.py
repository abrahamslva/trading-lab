"""
Optimizador de variantes DD5% y DD10% para estrategias XAUUSD
==============================================================
Misma señal que las estrategias ganadoras base, solo cambian:
  - DD objetivo: -5% y -10%
  - SLM y RP según grid de búsqueda por TF

Uso:
  python src/strategies/winning/dd_variants_optimizer.py

Genera:
  results/dd_variants_results.csv
  Imprime mejores params para DD5 y DD10 por TF
"""
import sys, time, warnings, itertools
import numpy as np
import pandas as pd

sys.path.insert(0, '.')
from src.backtesting.rsi_pullback_optimizer import precompute, _bt, mets

warnings.filterwarnings('ignore')

# ── Constantes ────────────────────────────────────────────────────────────────
MONTHS   = 123.6
INITIAL  = 100_000.0
OBJ_M    = 2.0      # retorno mínimo mensual %
OBJ_TPM  = 7.0      # trades/mes mínimo
OBJ_WD   = -3.0     # peor día % límite
OBJ_DD5  = -5.0     # drawdown objetivo variante DD5
OBJ_DD10 = -10.0    # drawdown objetivo variante DD10

DATA_PATH = 'data/dukascopy/XAUUSD_15min_mt5.parquet'

# ── Helpers compartidos ───────────────────────────────────────────────────────
def ema(s, n): return s.ewm(n, adjust=False).mean()

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

def load_data():
    df = pd.read_parquet(DATA_PATH)
    df.index = pd.to_datetime(df.index)
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert('UTC').tz_localize(None)
    return df

# ── Señales por TF (idénticas a las estrategias ganadoras) ───────────────────

def signal_m15(df, m15):
    idx = df.index
    hour_ok = (idx.hour >= 6) & (idx.hour < 20)
    time_ok = (idx.dayofweek < 5) & hour_ok
    sk = stoch_k(df, 14).fillna(50).values
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
    w = 300
    sig[w:] = np.where(stoch_long[w:] & h4v[w:] & d1v[w:], 1,
              np.where(stoch_short[w:] & ~h4v[w:] & ~d1v[w:], -1, 0))
    return sig

def signal_30m(df, m15):
    idx = df.index
    hour_ok = (idx.hour >= 6) & (idx.hour < 20)
    time_ok = (idx.dayofweek < 5) & hour_ok
    sk = stoch_k(df, 14).fillna(50).values
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
    w = 150
    sig[w:] = np.where(stoch_long[w:] & h4v[w:] & d1v[w:], 1,
              np.where(stoch_short[w:] & ~h4v[w:] & ~d1v[w:], -1, 0))
    return sig

def signal_1h(df, m15):
    idx = df.index
    time_ok = idx.dayofweek < 5
    sk = stoch_k(df, 3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    # Nivel: K entrando en sobrevendido/sobrecomprado
    stoch_long  = (sk < 30) & (sk_p >= 30) & time_ok
    stoch_short = (sk > 70) & (sk_p <= 70) & time_ok
    h4 = resample_ohlcv(m15, '4h')
    h4_bull = rsi_calc(h4['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    w = 75
    sig[w:] = np.where(stoch_long[w:] & h4v[w:] & d1v[w:], 1,
              np.where(stoch_short[w:] & ~h4v[w:] & ~d1v[w:], -1, 0))
    return sig

def signal_2h(df, m15):
    idx = df.index
    time_ok = idx.dayofweek < 5
    sk = stoch_k(df, 3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    # Cruce: K saliendo de sobrevendido/sobrecomprado
    stoch_long  = (sk > 20) & (sk_p <= 20) & time_ok
    stoch_short = (sk < 80) & (sk_p >= 80) & time_ok
    h4 = resample_ohlcv(m15, '4h')
    h4_bull = rsi_calc(h4['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    h4v = ffill_to(h4_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    w = 40
    sig[w:] = np.where(stoch_long[w:] & h4v[w:] & d1v[w:], 1,
              np.where(stoch_short[w:] & ~h4v[w:] & ~d1v[w:], -1, 0))
    return sig

def signal_3h(df, m15):
    """LONG ONLY — W1+D1 RSI (no 4H porque 3H no alinea con 4H)"""
    idx = df.index
    time_ok = idx.dayofweek < 5
    sk = stoch_k(df, 3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long = (sk < 30) & (sk_p >= 30) & time_ok
    w1 = resample_ohlcv(m15, 'W')
    w1_bull = rsi_calc(w1['close'], 14) > 50
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    w1v = ffill_to(w1_bull, idx).values
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    w = 25
    sig[w:] = np.where(stoch_long[w:] & w1v[w:] & d1v[w:], 1, 0)
    return sig

def signal_4h(df, m15):
    """LONG ONLY — solo D1 RSI"""
    idx = df.index
    time_ok = idx.dayofweek < 5
    sk = stoch_k(df, 3).fillna(50).values
    sk_p = np.roll(sk, 1); sk_p[0] = 50
    stoch_long = (sk < 30) & (sk_p >= 30) & time_ok
    d1 = resample_ohlcv(m15, 'D')
    d1_bull = rsi_calc(d1['close'], 14) > 50
    d1v = ffill_to(d1_bull, idx).values
    sig = np.zeros(len(df), dtype=np.int8)
    w = 20
    sig[w:] = np.where(stoch_long[w:] & d1v[w:], 1, 0)
    return sig

# ── Grid de parámetros por TF ─────────────────────────────────────────────────

GRIDS = {
    'M15': {
        'resample': None, 'hold': 12, 'sig_fn': signal_m15,
        'long_only': False,
        'DD5':  {'slm': [0.3, 0.4, 0.5], 'rp': [0.002, 0.003]},
        'DD10': {'slm': [1.0, 1.2, 1.5], 'rp': [0.005, 0.008]},
    },
    '30M': {
        'resample': '30min', 'hold': 24, 'sig_fn': signal_30m,
        'long_only': False,
        'DD5':  {'slm': [0.5, 0.6, 0.7], 'rp': [0.003, 0.004]},
        'DD10': {'slm': [1.2, 1.5], 'rp': [0.008, 0.010]},
    },
    '1H': {
        'resample': '1h', 'hold': 2, 'sig_fn': signal_1h,
        'long_only': False,
        'DD5':  {'slm': [0.2, 0.3], 'rp': [0.003, 0.004]},
        'DD10': {'slm': [0.7, 0.8, 1.0], 'rp': [0.008, 0.010]},
    },
    '2H': {
        'resample': '2h', 'hold': 2, 'sig_fn': signal_2h,
        'long_only': False,
        'DD5':  {'slm': [0.2, 0.3], 'rp': [0.003, 0.004]},
        'DD10': {'slm': [0.7, 0.8], 'rp': [0.007, 0.010]},
    },
    '3H': {
        'resample': '3h', 'hold': 2, 'sig_fn': signal_3h,
        'long_only': True,
        'DD5':  {'slm': [0.15, 0.2, 0.25], 'rp': [0.003, 0.004]},
        'DD10': {'slm': [0.4, 0.5, 0.6], 'rp': [0.007, 0.010]},
    },
    '4H': {
        'resample': '4h', 'hold': 2, 'sig_fn': signal_4h,
        'long_only': True,
        'DD5':  {'slm': [0.2, 0.3, 0.4], 'rp': [0.005, 0.006]},
        'DD10': {'slm': [0.7, 0.8, 1.0], 'rp': [0.012, 0.015]},
    },
}

TP_GRID = {
    'M15': [5.0], '30M': [3.0], '1H': [5.0],
    '2H': [3.0], '3H': [4.0], '4H': [2.5],
}

# ── Motor de optimización ─────────────────────────────────────────────────────

def warmup_numba(cache):
    dummy = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache['op'][:600], cache['hi'][:600], cache['lo'][:600],
        cache['atr14'][:600], dummy, 0.005, 0.015, 0.5, 2.0, 5, 2,
        cache['day_idx'][:600])

def run_tf(tf_name, cfg, dd_target, m15, verbose=True):
    """Busca mejor (slm, rp) para un TF y un objetivo de DD."""
    resample    = cfg['resample']
    hold        = cfg['hold']
    sig_fn      = cfg['sig_fn']
    long_only   = cfg['long_only']
    slm_list    = cfg[dd_target]['slm']
    rp_list     = cfg[dd_target]['rp']
    tp_list     = TP_GRID[tf_name]

    # Preparar DataFrame del TF
    if resample is None:
        df = m15.copy()
    else:
        df = resample_ohlcv(m15, resample)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

    cache = precompute(df, resample)
    warmup_numba(cache)
    sig = sig_fn(df, m15)

    dd_obj = OBJ_DD5 if dd_target == 'DD5' else OBJ_DD10

    best = None
    best_score = -np.inf

    for slm, rp, tp_r in itertools.product(slm_list, rp_list, tp_list):
        eq, pnl, nt = _bt(
            cache['op'], cache['hi'], cache['lo'], cache['atr14'],
            sig, rp, 0.015, slm, tp_r, 5, hold, cache['day_idx']
        )
        if nt < 2:
            continue
        m = mets(pnl[:nt], eq)
        month_ret = m['m']           # retorno mensual %
        trades_pm = m['tpm']         # trades por mes
        dd        = m['dd']          # max drawdown %
        wd        = m.get('wd', -999)  # peor día %
        wr        = m.get('wr', 0)   # win rate %

        ok_m   = month_ret >= OBJ_M
        ok_tpm = trades_pm >= OBJ_TPM
        ok_dd  = dd_obj <= dd < 0.0       # dentro del rango del objetivo
        ok_wd  = long_only or (wd >= OBJ_WD)
        passes = ok_m and ok_tpm and ok_dd and ok_wd

        # Score: prioridad por passes, luego por retorno mensual
        score = (1000 if passes else 0) + month_ret
        if score > best_score:
            best_score = score
            best = {
                'tf': tf_name, 'dd_target': dd_target, 'slm': slm, 'rp': rp,
                'tp_r': tp_r, 'hold': hold, 'resample': resample,
                'month_ret': round(month_ret, 2), 'max_dd': round(dd, 2),
                'trades_pm': round(trades_pm, 1), 'win_rate': round(wr, 1),
                'worst_day': round(wd, 2), 'passes': passes,
            }
    return best


def main():
    print("=" * 70)
    print("  OPTIMIZADOR VARIANTES DD5% y DD10% — XAUUSD")
    print("=" * 70)
    t0 = time.time()
    m15 = load_data()
    print(f"  Datos: {len(m15):,} barras  {m15.index[0].date()} → {m15.index[-1].date()}\n")

    rows = []
    for dd_target in ['DD5', 'DD10']:
        print(f"\n{'─'*60}")
        print(f"  Objetivo: Max DD ≤ {'-5%' if dd_target == 'DD5' else '-10%'}")
        print(f"{'─'*60}")
        print(f"  {'TF':<6} {'SLM':>5} {'RP':>6} {'TP_R':>5} {'Ret%/m':>7} {'DD%':>7} {'T/m':>5} {'WR%':>6} {'OK':>4}")

        for tf_name, cfg in GRIDS.items():
            res = run_tf(tf_name, cfg, dd_target, m15)
            if res is None:
                print(f"  {tf_name:<6}  SIN combinacion válida")
                continue
            mark = '✓' if res['passes'] else '✗'
            print(f"  {tf_name:<6} {res['slm']:>5.2f} {res['rp']:>6.3f} "
                  f"{res['tp_r']:>5.1f} {res['month_ret']:>7.2f} "
                  f"{res['max_dd']:>7.2f} {res['trades_pm']:>5.1f} "
                  f"{res['win_rate']:>6.1f} {mark:>4}")
            rows.append(res)

    elapsed = time.time() - t0
    print(f"\n  Tiempo total: {elapsed:.1f}s")

    if rows:
        out = pd.DataFrame(rows)
        out.to_csv('results/dd_variants_results.csv', index=False)
        print(f"\n  Resultados guardados en: results/dd_variants_results.csv")

        # Mostrar resumen de los mejores params para copiar a strategy files
        print(f"\n{'='*70}")
        print("  PARÁMETROS PARA COPIAR A ARCHIVOS DE ESTRATEGIA:")
        print(f"{'='*70}")
        for _, r in out.iterrows():
            print(f"  {r['dd_target']} | {r['tf']:>3} | SLM={r['slm']:.2f} RP={r['rp']:.4f} "
                  f"TP={r['tp_r']} | {r['month_ret']:+.2f}%/m DD={r['max_dd']:.2f}% "
                  f"{'✓' if r['passes'] else '✗'}")

    return out if rows else pd.DataFrame()


if __name__ == '__main__':
    main()
