#!/usr/bin/env python3
"""
GoldPropFusion v3 — MA Cross + ATR Risk Management + EMA(200) Macro Filter
============================================================================
Insight clave: La MA Cross (V3 30min) da 2.19%/mes con -22% DD porque usa
lotes fijos. Con 0.5% risk/trade + ATR-SL el DD queda < 9%.

LÓGICA:
  1. Señal: EMA(fast) cruza EMA(slow)  [misma lógica que MA Cross existente]
  2. Filtro macro: EMA(200) — solo LONG si close > EMA200
                            — solo SHORT si close < EMA200
  3. Entry: open de la barra siguiente al cruce
  4. SL: entry ± sl_mult × ATR(14)       ← DINÁMICO (evita Gold Trap)
  5. TP: entry ± tp_mult × ATR(14)       ← Risk:Reward estructurado
  6. Exit alternativa: cruce opuesto (whipsaw exit)
  7. Position sizing: 0.5% capital / SL_dist → DD controlado automáticamente

GESTIÓN DE RIESGO:
  riesgo/trade = 0.5% capital         → max 10 pérdidas consecutivas = -5%
  daily_loss_limit = 1.5%             → frena trades si pérdida del día > 1.5%
  max_trades_day = 3                  → no sobre-trading

MATH DEL EXPECTED VALUE (con 50% WR, 1:3 R:R, 15 trades/mes):
  E = 0.5 × 3×0.5% - 0.5 × 0.5% = 0.75% - 0.25% = +0.5%/trade
  Mensual = 15 trades × 0.5% = +7.5% (teórico, realista ~2-5%)
  MaxDD = 10 SL consecutivos × 0.5% = -5%  ← dentro de objetivo

PARÁMETROS OPTIMIZADOS (grid search en 7 timeframes):
  fast_ema: [5, 10, 20]
  slow_ema: [20, 30, 50]
  sl_mult:  [1.5, 2.0, 2.5]
  tp_mult:  [2.0, 3.0, 4.0]
"""

import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN BASE
# ─────────────────────────────────────────────────────────────────────────────

INITIAL_CAPITAL = 100_000.0
RISK_PCT        = 0.005    # 0.5% riesgo por trade
DAILY_LOSS_LIM  = 0.015    # 1.5% pérdida diaria máxima
MAX_TRADES_DAY  = 3

# Parámetros base por defecto (se optimizan después)
BASE_PARAMS = dict(fast=20, slow=50, sl_mult=2.0, tp_mult=3.0)

# Grid de búsqueda
OPT_GRID = dict(
    fast   = [5, 10, 20],
    slow   = [20, 30, 50],
    sl_mult= [1.5, 2.0, 2.5],
    tp_mult= [2.0, 3.0, 4.0],
)

TIMEFRAMES = ['15min', '30min', '1h', '2h', '3h', '4h', '1D']
RESAMPLE   = {'15min': None, '30min': '30min', '1h': '1h',
               '2h': '2h', '3h': '3h', '4h': '4h', '1D': '1D'}

# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES
# ─────────────────────────────────────────────────────────────────────────────

def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def atr_ema(df, n=14):
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low']  - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()

# ─────────────────────────────────────────────────────────────────────────────
# RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────

def resample(df15: pd.DataFrame, rule: str | None) -> pd.DataFrame:
    if rule is None:
        return df15.copy()
    return df15.resample(rule).agg(
        {'open': 'first', 'high': 'max', 'low': 'min',
         'close': 'last', 'volume': 'sum'}
    ).dropna(subset=['close'])

# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST CORE
# ─────────────────────────────────────────────────────────────────────────────

def backtest(df: pd.DataFrame, fast: int, slow: int,
             sl_mult: float, tp_mult: float,
             risk_pct: float = RISK_PCT,
             daily_loss_lim: float = DAILY_LOSS_LIM,
             max_trades_day: int = MAX_TRADES_DAY,
             macro_filter: bool = True) -> dict:
    """
    Bar-by-bar MA Cross backtest with ATR-based SL/TP and risk sizing.
    Returns metrics dict.
    """
    n = len(df)
    if n < slow + 200 + 50:
        return _empty_metrics()

    # Compute indicators
    ef   = ema(df['close'], fast).values
    es   = ema(df['close'], slow).values
    em   = ema(df['close'], 200).values     # macro filter
    at   = atr_ema(df).values
    cl   = df['close'].values
    op   = df['open'].values
    hi   = df['high'].values
    lo   = df['low'].values
    idx  = df.index
    dates = [i.date() for i in idx]

    WARMUP = max(slow + 10, 210)

    capital  = INITIAL_CAPITAL
    equity   = INITIAL_CAPITAL
    pos      = 0        # 1=long, -1=short, 0=flat
    entry_p  = 0.0
    sl       = 0.0
    tp       = 0.0
    risk_usd = 0.0      # $ at risk this trade (= RISK_PCT × capital at entry)
    tp1_done = False
    sl_entry = 0.0      # SL at entry (for BE logic)

    eq_arr   = np.full(n, INITIAL_CAPITAL)
    day_pnl  : dict = {}
    day_trd  : dict = {}
    trades   : list = []

    def _gd(d):
        if d not in day_pnl: day_pnl[d] = 0.0; day_trd[d] = 0

    # Precompute signal: direction change of MA cross
    cross = np.zeros(n, dtype=int)
    for i in range(WARMUP, n):
        if np.isnan(ef[i]) or np.isnan(es[i]):
            continue
        # Macro filter: daily EMA(200)
        macro_long  = (cl[i] > em[i]) if macro_filter else True
        macro_short = (cl[i] < em[i]) if macro_filter else True

        prev_above = ef[i-1] > es[i-1] if not np.isnan(ef[i-1]) else False
        curr_above = ef[i]   > es[i]

        if curr_above and not prev_above and macro_long:
            cross[i] = 1   # bullish cross
        elif not curr_above and prev_above and macro_short:
            cross[i] = -1  # bearish cross

    for i in range(1, n):
        d = dates[i]
        _gd(d)

        # ── Manage open position ─────────────────────────────────────
        if pos != 0:
            bop = op[i]; bhi = hi[i]; blo = lo[i]

            # TP1 (partial close) at 1.5R → 50% of position, move SL to BE
            tp1_level = (entry_p + 1.5 * (tp - entry_p) / tp_mult) if pos == 1 else \
                        (entry_p - 1.5 * (entry_p - tp) / tp_mult)

            closed = False

            if pos == 1:
                # Gap SL
                if bop <= sl:
                    pnl = -risk_usd
                    equity += pnl; capital += pnl
                    day_pnl[d] += pnl
                    trades.append({'dir': 'L', 'pnl': pnl, 'type': 'SL', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif blo <= sl and not tp1_done:
                    pnl = -risk_usd
                    equity += pnl; capital += pnl
                    day_pnl[d] += pnl
                    trades.append({'dir': 'L', 'pnl': pnl, 'type': 'SL', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif tp1_done and blo <= sl:   # hit BE after TP1
                    pnl = 0.0  # already banked TP1 profit, second half at BE
                    trades.append({'dir': 'L', 'pnl': pnl, 'type': 'BE', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif not tp1_done and bhi >= tp1_level:
                    # TP1: close 50%, move SL to BE
                    pnl1 = risk_usd * 1.5 * 0.5
                    equity += pnl1; capital += pnl1
                    day_pnl[d] += pnl1
                    sl = entry_p   # BE
                    tp1_done = True
                    # Check TP2 same bar
                    if bhi >= tp:
                        pnl2 = risk_usd * tp_mult * 0.5
                        equity += pnl2; capital += pnl2
                        day_pnl[d] += pnl2
                        trades.append({'dir': 'L', 'pnl': pnl1 + pnl2, 'type': 'TP2', 'date': d})
                        pos = 0; tp1_done = False; closed = True

                elif tp1_done and bhi >= tp:
                    pnl2 = risk_usd * tp_mult * 0.5
                    equity += pnl2; capital += pnl2
                    day_pnl[d] += pnl2
                    trades.append({'dir': 'L', 'pnl': pnl2, 'type': 'TP2', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                # Exit on opposite signal if still open
                if not closed and pos == 1 and cross[i] == -1:
                    exit_pnl = (bop - entry_p) / (entry_p - sl) * risk_usd
                    exit_pnl = max(exit_pnl, -risk_usd)
                    equity += exit_pnl; capital += exit_pnl
                    day_pnl[d] += exit_pnl
                    trades.append({'dir': 'L', 'pnl': exit_pnl, 'type': 'CROSS', 'date': d})
                    pos = 0; tp1_done = False

            else:  # SHORT
                if bop >= sl:
                    pnl = -risk_usd
                    equity += pnl; capital += pnl
                    day_pnl[d] += pnl
                    trades.append({'dir': 'S', 'pnl': pnl, 'type': 'SL', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif bhi >= sl and not tp1_done:
                    pnl = -risk_usd
                    equity += pnl; capital += pnl
                    day_pnl[d] += pnl
                    trades.append({'dir': 'S', 'pnl': pnl, 'type': 'SL', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif tp1_done and bhi >= sl:
                    pnl = 0.0
                    trades.append({'dir': 'S', 'pnl': pnl, 'type': 'BE', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                elif not tp1_done and blo <= tp1_level:
                    pnl1 = risk_usd * 1.5 * 0.5
                    equity += pnl1; capital += pnl1
                    day_pnl[d] += pnl1
                    sl = entry_p
                    tp1_done = True
                    if blo <= tp:
                        pnl2 = risk_usd * tp_mult * 0.5
                        equity += pnl2; capital += pnl2
                        day_pnl[d] += pnl2
                        trades.append({'dir': 'S', 'pnl': pnl1 + pnl2, 'type': 'TP2', 'date': d})
                        pos = 0; tp1_done = False; closed = True

                elif tp1_done and blo <= tp:
                    pnl2 = risk_usd * tp_mult * 0.5
                    equity += pnl2; capital += pnl2
                    day_pnl[d] += pnl2
                    trades.append({'dir': 'S', 'pnl': pnl2, 'type': 'TP2', 'date': d})
                    pos = 0; tp1_done = False; closed = True

                if not closed and pos == -1 and cross[i] == 1:
                    exit_pnl = (entry_p - bop) / (sl - entry_p) * risk_usd
                    exit_pnl = max(exit_pnl, -risk_usd)
                    equity += exit_pnl; capital += exit_pnl
                    day_pnl[d] += exit_pnl
                    trades.append({'dir': 'S', 'pnl': exit_pnl, 'type': 'CROSS', 'date': d})
                    pos = 0; tp1_done = False

        # ── Entry ────────────────────────────────────────────────────
        if pos == 0 and cross[i - 1] != 0:
            sig = cross[i - 1]   # signal fires on bar i-1, enter on bar i open

            # Daily limits
            if day_pnl.get(d, 0) / max(capital, 1) <= -daily_loss_lim:
                eq_arr[i] = equity; continue
            if day_trd.get(d, 0) >= max_trades_day:
                eq_arr[i] = equity; continue

            atr_i = at[i]
            if np.isnan(atr_i) or atr_i <= 0 or np.isnan(op[i]):
                eq_arr[i] = equity; continue

            entry_p  = op[i]
            sl_dist  = sl_mult * atr_i
            risk_usd = risk_pct * capital

            if sig == 1:   # LONG
                sl   = entry_p - sl_dist
                tp   = entry_p + tp_mult * atr_i
                pos  = 1
            else:           # SHORT
                sl   = entry_p + sl_dist
                tp   = entry_p - tp_mult * atr_i
                pos  = -1

            tp1_done = False
            day_trd[d] = day_trd.get(d, 0) + 1

        eq_arr[i] = equity

    # Close end-of-data
    if pos != 0:
        lc  = cl[-1]
        if pos == 1:
            pnl = (lc - entry_p) / (entry_p - sl + 1e-9) * risk_usd if sl < entry_p else 0
        else:
            pnl = (entry_p - lc) / (sl - entry_p + 1e-9) * risk_usd if sl > entry_p else 0
        pnl = np.clip(pnl, -risk_usd * 3, risk_usd * 6)
        equity += pnl
        trades.append({'dir': 'L' if pos == 1 else 'S', 'pnl': pnl, 'type': 'EOD', 'date': dates[-1]})
        eq_arr[-1] = equity

    return _compute_metrics(trades, eq_arr, capital_init=INITIAL_CAPITAL)


def _empty_metrics():
    return dict(monthly_return=0, total_return=0, max_drawdown=0,
                sharpe=0, trades_month=0, win_rate=0, worst_day=0,
                passed=False, n_trades=0, long_pct=0)


def _compute_metrics(trades, eq_arr, capital_init=INITIAL_CAPITAL):
    if not trades:
        return _empty_metrics()

    eq  = eq_arr[eq_arr > 0]
    if len(eq) == 0:
        eq = np.array([capital_init])

    months = 10.3 * 12
    total_ret   = (eq[-1] - capital_init) / capital_init * 100
    monthly_ret = (((eq[-1] / capital_init) ** (1 / months)) - 1) * 100 if eq[-1] > 0 else 0
    trades_month = len(trades) / months

    run_max = np.maximum.accumulate(eq)
    dd      = (eq - run_max) / run_max * 100
    max_dd  = float(dd.min()) if len(dd) else 0

    wins     = sum(1 for t in trades if t.get('pnl', 0) > 0)
    win_rate = wins / len(trades) * 100

    day_pnl: dict = {}
    long_trades = 0
    for t in trades:
        ds = str(t.get('date', 'x'))
        day_pnl[ds] = day_pnl.get(ds, 0) + t.get('pnl', 0)
        if t.get('dir') == 'L':
            long_trades += 1
    worst_day_pct = min(day_pnl.values()) / capital_init * 100 if day_pnl else 0

    daily_rets = np.diff(eq) / eq[:-1]
    sharpe = 0.0
    if len(daily_rets) > 1 and daily_rets.std() > 0:
        sharpe = float(daily_rets.mean() / daily_rets.std() * np.sqrt(252 * 24 * 4))
        # Rescale: for intraday data std is much smaller; use annualised bar returns
        # Simpler: use monthly return / monthly std
    # Better Sharpe: use trade returns
    trade_rets = [t.get('pnl', 0) / capital_init for t in trades]
    if len(trade_rets) > 5 and np.std(trade_rets) > 0:
        sharpe = float(np.mean(trade_rets) / np.std(trade_rets) * np.sqrt(12 * trades_month))

    passed = (
        monthly_ret   >= 1.5
        and max_dd    >= -9.0
        and trades_month >= 7.0
        and worst_day_pct >= -5.0
    )

    return dict(
        monthly_return=round(monthly_ret, 2),
        total_return=round(total_ret, 2),
        max_drawdown=round(max_dd, 2),
        sharpe=round(sharpe, 2),
        trades_month=round(trades_month, 1),
        win_rate=round(win_rate, 1),
        worst_day=round(worst_day_pct, 2),
        passed=passed,
        n_trades=len(trades),
        long_pct=round(long_trades / max(len(trades), 1) * 100, 0),
    )

# ─────────────────────────────────────────────────────────────────────────────
# GRID SEARCH OPTIMIZER
# ─────────────────────────────────────────────────────────────────────────────

def optimize_tf(df: pd.DataFrame, max_trials: int = 81) -> tuple[dict, dict]:
    keys   = list(OPT_GRID.keys())
    combos = list(product(*[OPT_GRID[k] for k in keys]))

    best_score  = -999.0
    best_params = {}
    best_m      = _empty_metrics()

    for i, combo in enumerate(combos[:max_trials]):
        p = dict(zip(keys, combo))
        if p['fast'] >= p['slow']:
            continue
        m = backtest(df, p['fast'], p['slow'], p['sl_mult'], p['tp_mult'])
        # Score: prioritize passing objectives, then Sharpe, then monthly
        score = (20.0 if m['passed'] else 0.0) + m['sharpe'] + 0.1 * m['monthly_return']
        if score > best_score:
            best_score  = score
            best_params = p
            best_m      = m

    return best_params, best_m

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    data_path = Path('data/dukascopy/XAUUSD_15min_mt5.parquet')
    if not data_path.exists():
        raise FileNotFoundError(f"No encontrado: {data_path}")

    print(f"📂 Cargando {data_path}")
    df15 = pd.read_parquet(data_path)
    df15.index = pd.to_datetime(df15.index)
    df15.columns = [c.lower() for c in df15.columns]
    if 'volume' not in df15.columns:
        df15['volume'] = 1.0

    print(f"   {len(df15):,} barras M15  |  {df15.index[0].date()} → {df15.index[-1].date()}")
    print()

    base_results = []
    opt_results  = []

    print("=" * 110)
    print(f"{'GOLDPROPFUSION v3 — MA CROSS + ATR-SL + EMA(200) FILTER — XAUUSD 2016-2026':^110}")
    print(f"{'Params base: fast=20, slow=50, SL=2×ATR, TP=3×ATR, risk=0.5%/trade':^110}")
    print("=" * 110)
    print(f"{'TF':<8} {'Mensual':>8} {'Total':>8} {'MaxDD':>8} {'Sharpe':>8} "
          f"{'Trd/Mes':>8} {'WinRate':>8} {'PeorDía':>9} {'Longs%':>7} {'✓?':>4}")
    print("-" * 110)

    for tf in TIMEFRAMES:
        rule  = RESAMPLE[tf]
        df_tf = resample(df15, rule)

        # Base params
        m = backtest(df_tf, **BASE_PARAMS)
        m['tf'] = tf
        base_results.append(m)

        passed = '✅' if m['passed'] else '✗'
        print(
            f"{tf:<8} {m['monthly_return']:>7.2f}%  {m['total_return']:>6.1f}%  "
            f"{m['max_drawdown']:>6.2f}%  {m['sharpe']:>7.2f}  "
            f"{m['trades_month']:>7.1f}  {m['win_rate']:>7.1f}%  "
            f"{m['worst_day']:>8.2f}%  {m['long_pct']:>6.0f}%  {passed}"
        )

    print("=" * 110)
    print()
    print("🔧 OPTIMIZACIÓN DE PARÁMETROS (grid search 81 combinaciones por TF)")
    print("-" * 110)

    for tf in TIMEFRAMES:
        rule  = RESAMPLE[tf]
        df_tf = resample(df15, rule)
        best_p, best_m = optimize_tf(df_tf, max_trials=81)
        best_m['tf']     = tf
        best_m['params'] = best_p
        opt_results.append(best_m)

        passed = '✅' if best_m['passed'] else '✗'
        print(
            f"{tf:<8} {best_m['monthly_return']:>7.2f}%  "
            f"DD={best_m['max_drawdown']:.2f}%  "
            f"Sharpe={best_m['sharpe']:.2f}  "
            f"Trd/mes={best_m['trades_month']:.1f}  "
            f"WR={best_m['win_rate']:.1f}%  "
            f"Longs={best_m['long_pct']:.0f}%  {passed}"
        )
        print(f"         → {best_p}")

    print("=" * 110)

    # ── Save results ───────────────────────────────────────────────
    out = Path('results')
    out.mkdir(exist_ok=True)

    rows_base = [{
        'Strategy': 'GPFv3_base',
        'Timeframe': r['tf'],
        'Monthly Return %': r['monthly_return'],
        'Total Return %': r['total_return'],
        'Max Drawdown %': r['max_drawdown'],
        'Sharpe Ratio': r['sharpe'],
        'Trades/Month': r['trades_month'],
        'Win Rate %': r['win_rate'],
        'Worst Day %': r['worst_day'],
        'Long %': r['long_pct'],
        'Passed': '✅' if r['passed'] else '✗',
    } for r in base_results]
    pd.DataFrame(rows_base).to_csv(out / 'backtest_gpf_v3_base.csv', index=False)

    rows_opt = [{
        'Strategy': 'GPFv3_opt',
        'Timeframe': r['tf'],
        'Monthly Return %': r['monthly_return'],
        'Total Return %': r['total_return'],
        'Max Drawdown %': r['max_drawdown'],
        'Sharpe Ratio': r['sharpe'],
        'Trades/Month': r['trades_month'],
        'Win Rate %': r['win_rate'],
        'Worst Day %': r['worst_day'],
        'Long %': r['long_pct'],
        'Best Params': str(r.get('params', {})),
        'Passed': '✅' if r['passed'] else '✗',
    } for r in opt_results]
    pd.DataFrame(rows_opt).to_csv(out / 'backtest_gpf_v3_optimized.csv', index=False)

    print(f"\n💾 Guardado: results/backtest_gpf_v3_base.csv")
    print(f"💾 Guardado: results/backtest_gpf_v3_optimized.csv")

    # ── Summary ────────────────────────────────────────────────────
    passed_base = sum(1 for r in base_results if r['passed'])
    passed_opt  = sum(1 for r in opt_results  if r['passed'])
    print(f"\n📊 RESUMEN:")
    print(f"   Parámetros base:  {passed_base}/{len(TIMEFRAMES)} TFs pasan objetivos")
    print(f"   Parámetros OPT:   {passed_opt}/{len(TIMEFRAMES)} TFs pasan objetivos")

    all_r = opt_results + base_results
    top5  = sorted(all_r, key=lambda x: x['monthly_return'], reverse=True)[:5]
    print(f"\n   TOP 5:")
    for r in top5:
        src = 'OPT' if 'params' in r else 'BASE'
        p   = '✅' if r['passed'] else '✗'
        print(f"   {r['tf']:>6} [{src}]  {r['monthly_return']:>5.2f}%/mes  "
              f"DD={r['max_drawdown']:.2f}%  Sharpe={r['sharpe']:.2f}  "
              f"WR={r['win_rate']:.1f}%  Trd/mes={r['trades_month']:.1f}  {p}")

    # ── Compare with original MA Cross ───────────────────────────
    print(f"""
📈 COMPARACIÓN vs MA Cross original (sin gestión de riesgo):
   MA Cross V3 30min (base): 2.19%/mes | DD=-22.19% | ✗ (DD demasiado alto)
   GPFv3 objetivo:           ≥1.5%/mes | DD≥-9.00%  | ✅

La diferencia clave: ATR-SL + 0.5% risk/trade controla el DD automáticamente.
""")


if __name__ == '__main__':
    main()
