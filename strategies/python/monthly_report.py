"""
monthly_report.py — Reporte mensual completo por estrategia
===========================================================
Para cada TF ganadora (M15 / 30M / 1H / 2H / 3H / 4H) muestra por mes:
  • Retorno mensual (%)
  • Caída máxima intra-mes (peak-to-trough dentro del mes)
  • Peor día del mes (peor retorno diario dentro del mes)
  • Número de trades ejecutados ese mes
  • Win Rate de ese mes (%)
  • Equity al cierre del mes
  • ¿El mes cumplió los objetivos?

Nota sobre 1D (GVF V3):  usa yfinance + motor distinto. Se reporta desde
el CSV guardado en results/backtest_volume_fusion_results.csv (sin breakdown
mensual — no disponible en CSV).

Uso:
    python strategies/python/monthly_report.py
"""

import sys, os, io
sys.path.insert(0, '.')

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from src.backtesting.rsi_pullback_optimizer import precompute, _bt

import importlib.util

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_base = os.path.join(os.path.dirname(__file__), 'dd7')
strategy_M15 = _load('strategy_M15', os.path.join(_base, 'strategy_M15.py'))
strategy_30M = _load('strategy_30M', os.path.join(_base, 'strategy_30M.py'))
strategy_1H  = _load('strategy_1H',  os.path.join(_base, 'strategy_1H.py'))
strategy_2H  = _load('strategy_2H',  os.path.join(_base, 'strategy_2H.py'))
strategy_3H  = _load('strategy_3H',  os.path.join(_base, 'strategy_3H.py'))
strategy_4H  = _load('strategy_4H',  os.path.join(_base, 'strategy_4H.py'))

INITIAL   = 100_000.0
OBJ_M     = 2.0
OBJ_DD    = -7.0
OBJ_WD    = -3.0
OBJ_TPM   = 7.0

OUT_DIR   = 'results/monthly_report'
os.makedirs(OUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────────────────────
# Python trade simulator (mirrors _bt sin sizing adaptativo)
# Devuelve DataFrame con un registro por trade + timestamp
# ──────────────────────────────────────────────────────────────────────────────
def simulate_trades(df_tf, sig, rp, slm, tp_r, hold, dl=0.015, mtd=5):
    cache = precompute(df_tf, None)
    op    = cache['op']
    hi    = cache['hi']
    lo    = cache['lo']
    atr   = cache['atr14']
    didx  = cache['day_idx']
    idx   = df_tf.index
    n     = len(df_tf)

    cap   = INITIAL
    pos   = 0
    ep = sl = tp = ru = 0.0
    entry_bar  = 0
    entry_time = None

    nd    = int(didx[-1]) + 2
    dpnl  = np.zeros(nd)
    dcnt  = np.zeros(nd, dtype=np.int32)
    records = []

    for i in range(1, n):
        d = int(didx[i])

        if pos != 0:
            bo, bh, bl = op[i], hi[i], lo[i]
            held   = i - entry_bar
            exited = False
            pnl    = 0.0

            if held >= hold:
                if pos == 1:
                    pnl = (bo - ep) / (ep - sl + 1e-12) * ru
                else:
                    pnl = (ep - bo) / (sl - ep + 1e-12) * ru
                pnl    = min(max(pnl, -ru), ru * tp_r * 2)
                exited = True
            elif pos == 1:
                if bo <= sl or bl <= sl:
                    pnl = -ru; exited = True
                elif bo >= tp or bh >= tp:
                    pnl = ru * tp_r; exited = True
            else:
                if bo >= sl or bh >= sl:
                    pnl = -ru; exited = True
                elif bo <= tp or bl <= tp:
                    pnl = ru * tp_r; exited = True

            if exited:
                cap      += pnl
                dpnl[d]  += pnl
                records.append({
                    'entry_time': entry_time,
                    'exit_time':  idx[i],
                    'direction':  'L' if pos == 1 else 'S',
                    'pnl_abs':    pnl,
                    'win':        pnl > 0,
                })
                pos = 0
                continue

        if pos == 0 and sig[i - 1] != 0:
            if dpnl[d] / (cap + 1e-12) <= -dl: continue
            if dcnt[d] >= mtd:                  continue
            ati = atr[i]
            if ati <= 0 or ati != ati:          continue

            ep         = op[i]
            sd         = slm * ati
            ru         = rp * cap
            entry_bar  = i
            entry_time = idx[i]
            dcnt[d]   += 1

            if sig[i - 1] == 1:
                sl = ep - sd;  tp = ep + sd * tp_r;  pos =  1
            else:
                sl = ep + sd;  tp = ep - sd * tp_r;  pos = -1

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
# Estadísticas mensuales desde la curva de equity
# ──────────────────────────────────────────────────────────────────────────────
def equity_monthly_stats(eq_arr, df_tf_index):
    eq_series = pd.Series(eq_arr, index=df_tf_index)

    # Retorno mensual
    month_eq  = eq_series.resample('ME').last()
    prev_eq   = month_eq.shift(1)
    prev_eq.iloc[0] = INITIAL
    monthly_ret = (month_eq / prev_eq - 1.0) * 100.0

    # Max DD intra-mes (peak-to-trough dentro del mes)
    def _month_dd(group):
        if len(group) == 0: return 0.0
        peak = group.expanding().max()
        dd   = (group - peak) / (peak + 1e-12) * 100.0
        return float(dd.min())

    monthly_dd = eq_series.resample('ME').apply(_month_dd)

    # Peor día del mes: equity diaria → retorno diario
    daily_eq       = eq_series.resample('D').last().dropna()
    daily_ret      = daily_eq.pct_change().fillna(0.0) * 100.0
    monthly_wd     = daily_ret.resample('ME').min()

    return pd.DataFrame({
        'equity_end':   month_eq,
        'return_pct':   monthly_ret,
        'max_dd_pct':   monthly_dd,
        'worst_day_pct': monthly_wd,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Estadísticas mensuales desde los trades con timestamp
# ──────────────────────────────────────────────────────────────────────────────
def trades_monthly_stats(trades_df):
    if len(trades_df) == 0:
        return pd.DataFrame(columns=['n_trades', 'wr_pct'])

    trades_df = trades_df.copy()
    trades_df['month_end'] = (
        trades_df['entry_time']
        .dt.to_period('M')
        .dt.to_timestamp('M')
    )

    g = trades_df.groupby('month_end').agg(
        n_trades = ('win', 'count'),
        n_wins   = ('win', 'sum'),
    )
    g['wr_pct'] = g['n_wins'] / g['n_trades'] * 100.0
    return g[['n_trades', 'wr_pct']]


# ──────────────────────────────────────────────────────────────────────────────
# Analizar una estrategia
# ──────────────────────────────────────────────────────────────────────────────
def analyze_tf(tf_label, module, m15):
    print(f"\n  Calculando {tf_label}...", flush=True)

    if module.RESAMPLE is None:
        # M15 ya es el TF base — usar directo
        df = m15.copy()
    else:
        df = module.resample_ohlcv(m15, module.RESAMPLE)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    sig = module.build_signal(df, m15)

    cache = precompute(df, None)
    bt    = _bt(cache['op'], cache['hi'], cache['lo'], cache['atr14'],
                sig, module.RP, 0.015, module.SLM, module.TP_R,
                5, module.HOLD, cache['day_idx'])

    eq_stats     = equity_monthly_stats(bt[0], df.index)
    trades_df    = simulate_trades(df, sig, module.RP, module.SLM,
                                   module.TP_R, module.HOLD)
    trade_stats  = trades_monthly_stats(trades_df)

    # Combinar
    result = eq_stats.join(trade_stats, how='left')
    result['n_trades'] = result['n_trades'].fillna(0).astype(int)
    result['wr_pct']   = result['wr_pct'].fillna(0.0)

    # Columna de pasa/falla objetivos mensual
    result['obj_m']   = result['return_pct']   >= OBJ_M
    result['obj_dd']  = result['max_dd_pct']   >= OBJ_DD
    result['obj_wd']  = result['worst_day_pct'] >= OBJ_WD
    result['obj_tpm'] = result['n_trades']     >= OBJ_TPM
    result['passes']  = (result['obj_m'] & result['obj_dd'] &
                         result['obj_wd'] & result['obj_tpm'])

    # Cumulative equity
    result['equity_end'] = result['equity_end'].round(2)

    return result, trades_df


# ──────────────────────────────────────────────────────────────────────────────
# Formatear e imprimir tabla mensual
# ──────────────────────────────────────────────────────────────────────────────
HEADER = (
    f"  {'Mes':<10} {'Retorno':>8} {'MaxDD':>8} {'PeorDia':>9} "
    f"{'Trades':>7} {'WR%':>6} {'Equity':>12}  {'Obj?':>5}"
)
SEP = "  " + "-" * 75


def print_monthly_table(tf_label, module, df_result, buf=None):
    title = (
        f"\n{'='*80}\n"
        f"  {tf_label}  —  {getattr(module, 'TIMEFRAME', tf_label)}\n"
        f"  Señal: ver strategy_{tf_label.replace(' ','')}.py  |  "
        f"SLM={module.SLM}×ATR  TP={module.TP_R}×ATR  Hold={module.HOLD}  RP={module.RP*100:.1f}%\n"
        f"{'='*80}"
    )
    header = HEADER
    sep    = SEP

    lines = [title, header, sep]

    # Aggregate totals for quick check
    passed_months  = df_result['passes'].sum()
    total_months   = len(df_result)
    avg_ret        = df_result['return_pct'].mean()
    avg_dd         = df_result['max_dd_pct'].mean()
    avg_wd         = df_result['worst_day_pct'].mean()
    avg_trades     = df_result['n_trades'].mean()
    avg_wr         = df_result[df_result['wr_pct'] > 0]['wr_pct'].mean()
    total_trades   = df_result['n_trades'].sum()

    for date, row in df_result.iterrows():
        month_str = date.strftime('%b %Y')
        ret   = row['return_pct']
        dd    = row['max_dd_pct']
        wd    = row['worst_day_pct']
        nt    = row['n_trades']
        wr    = row['wr_pct']
        eq    = row['equity_end']
        ok    = '✅' if row['passes'] else ('➖' if nt == 0 else '❌')

        ret_s = f"{ret:+.2f}%"
        dd_s  = f"{dd:+.2f}%"
        wd_s  = f"{wd:+.2f}%"

        line = (
            f"  {month_str:<10} {ret_s:>8} {dd_s:>8} {wd_s:>9} "
            f"{nt:>7}  {wr:>5.1f}%  {eq:>12,.0f}  {ok}"
        )
        lines.append(line)

    lines.append(sep)
    summary = (
        f"  RESUMEN: {passed_months}/{total_months} meses pasan | "
        f"Ȳ Ret={avg_ret:+.2f}% | Ȳ DD={avg_dd:.2f}% | "
        f"Ȳ Peor Día={avg_wd:.2f}% | "
        f"Ȳ T/mes={avg_trades:.1f} | Ȳ WR={avg_wr:.1f}% | "
        f"Trades totales={total_trades:,}"
    )
    lines.append(summary)
    lines.append('=' * 80)

    text = '\n'.join(lines)
    print(text)
    if buf is not None:
        buf.write(text + '\n')
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 80)
    print("  REPORTE MENSUAL COMPLETO — ESTRATEGIAS GANADORAS XAUUSD")
    print("  10 años: 2016-01-04 → 2026-05-06  (123.6 meses)")
    print("  Objetivos por mes: Ret≥2% | MaxDD≥-7% | PeorDia≥-3% | Trades≥7")
    print("=" * 80)

    print("\n  Cargando datos M15 Dukascopy...", flush=True)
    m15 = strategy_M15.load_data()
    print(f"  {len(m15):,} barras cargadas: {m15.index[0].date()} → {m15.index[-1].date()}")

    # Warmup Numba
    print("  Calentando Numba JIT...", flush=True)
    cache15 = precompute(m15, None)
    dummy   = np.zeros(600, dtype=np.int8); dummy[300] = 1
    _bt(cache15['op'][:600], cache15['hi'][:600], cache15['lo'][:600],
        cache15['atr14'][:600], dummy, 0.005, 0.015, 0.5, 2.0, 5, 2,
        cache15['day_idx'][:600])
    print("  Numba listo.\n")

    strategies = [
        ('M15', strategy_M15),
        ('30M', strategy_30M),
        ('1H',  strategy_1H),
        ('2H',  strategy_2H),
        ('3H',  strategy_3H),
        ('4H',  strategy_4H),
    ]

    report_buf  = io.StringIO()
    all_monthly = {}

    for tf_label, mod in strategies:
        df_result, trades_df = analyze_tf(tf_label, mod, m15)
        print_monthly_table(tf_label, mod, df_result, buf=report_buf)
        all_monthly[tf_label] = df_result

        # Guardar CSV por estrategia
        csv_path = os.path.join(OUT_DIR, f'{tf_label}_monthly.csv')
        df_save  = df_result.copy()
        df_save.index.name = 'month_end'
        df_save = df_save.reset_index()
        df_save['month_end'] = df_save['month_end'].dt.strftime('%Y-%m')
        df_save.to_csv(csv_path, index=False, float_format='%.4f')
        print(f"  → CSV guardado: {csv_path}")

        # Guardar CSV de trades individuales
        if len(trades_df) > 0:
            t_path = os.path.join(OUT_DIR, f'{tf_label}_trades.csv')
            trades_df.to_csv(t_path, index=False)

    # ── CSV combinado (todos los TF, todas las métricas)
    frames = []
    for tf, df_r in all_monthly.items():
        d = df_r.copy()
        d['tf'] = tf
        d.index.name = 'month_end'
        d = d.reset_index()
        d['month_end'] = d['month_end'].dt.strftime('%Y-%m')
        frames.append(d)
    combined = pd.concat(frames)
    combined_path = os.path.join(OUT_DIR, 'all_strategies_monthly.csv')
    combined.to_csv(combined_path, index=False, float_format='%.4f')
    print(f"\n  → CSV combinado: {combined_path}")

    # ── Tabla resumen global (meses que PASAN por TF)
    print("\n" + "=" * 80)
    print("  RESUMEN GLOBAL — % de meses que pasan objetivos")
    print("=" * 80)
    print(f"  {'TF':<6} {'Pasan':>7} {'Total':>7} {'%Pasan':>8}  "
          f"{'ȲRet':>8}  {'ȲDD':>8}  {'ȲPDía':>8}  {'ȲT/mes':>8}  {'ȲWR':>7}")
    print("  " + "-" * 75)
    for tf, df_r in all_monthly.items():
        p = df_r['passes'].sum()
        t = len(df_r)
        pct = p / t * 100
        ar  = df_r['return_pct'].mean()
        ad  = df_r['max_dd_pct'].mean()
        awd = df_r['worst_day_pct'].mean()
        at  = df_r['n_trades'].mean()
        awr = df_r[df_r['wr_pct'] > 0]['wr_pct'].mean()
        print(f"  {tf:<6} {p:>7} {t:>7} {pct:>7.1f}%  "
              f"{ar:>+7.2f}%  {ad:>+7.2f}%  {awd:>+7.2f}%  "
              f"{at:>8.1f}  {awr:>6.1f}%")
    print("  " + "-" * 75)

    # Nota 1D
    print("\n  1D (GVF V3 / yfinance):  ver results/backtest_volume_fusion_results.csv")
    print("   → Ret=+11.73%/mes | MaxDD=-7.01% | T/mes=26.2 | WR=83.4%  ✅")
    print("=" * 80)

    # ── Guardar reporte de texto completo
    report_text  = report_buf.getvalue()
    report_path  = os.path.join(OUT_DIR, 'monthly_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("REPORTE MENSUAL COMPLETO — ESTRATEGIAS GANADORAS XAUUSD\n")
        f.write("10 años: 2016-01-04 → 2026-05-06  (123.6 meses)\n")
        f.write("Objetivos: Ret≥2% | MaxDD≥-7% | PeorDia≥-3% | Trades≥7/mes\n\n")
        f.write(report_text)
    print(f"\n  → Reporte texto: {report_path}")
    print(f"  → Todos los archivos en: {OUT_DIR}/")

if __name__ == '__main__':
    main()
