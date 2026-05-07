"""
generate_1d_monthly.py — Extrae breakdown mensual de GVF V3 (1D)
Corre el backtest de backtest_volume_fusion.py para V3/1D y genera CSV mensual.
"""
import sys, os
sys.path.insert(0, '.')
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from src.backtest_volume_fusion import (
    download_data, VolumeIndicators, GoldBacktester,
    compute_metrics, PARAMS_V3
)

OUT_DIR = 'results/monthly_report'
os.makedirs(OUT_DIR, exist_ok=True)

INITIAL = 100_000.0

def run_1d_monthly():
    print("Descargando datos 1D GC=F via yfinance...")
    df_raw = download_data("GC=F", start="2015-01-01", end="2026-06-01", interval="1d")
    if df_raw is None or df_raw.empty:
        print("ERROR: no se pudo descargar datos 1D")
        return None

    print(f"  {len(df_raw)} barras diarias: {df_raw.index[0].date()} → {df_raw.index[-1].date()}")

    # Usar params V3 (la estrategia ganadora)
    params = PARAMS_V3.copy()
    df     = VolumeIndicators.add_all(df_raw.copy(), params)
    bt     = GoldBacktester(df, params, INITIAL, is_intraday=False)
    trades = bt.run(verbose=False)

    if trades.empty:
        print("ERROR: sin trades generados")
        return None

    print(f"  {len(trades)} trades generados")

    # ── Equity curve mensual
    eq_list  = bt.equity_curve
    eq_index = [t for t, _ in eq_list]
    eq_vals  = [e for _, e in eq_list]
    eq_series = pd.Series(eq_vals, index=pd.to_datetime(eq_index))

    # Retorno mensual
    month_eq  = eq_series.resample('ME').last().dropna()
    prev_eq   = month_eq.shift(1).fillna(INITIAL)
    monthly_ret = (month_eq / prev_eq - 1.0) * 100.0

    # Max DD intra-mes
    def _month_dd(group):
        if len(group) == 0: return 0.0
        peak = group.expanding().max()
        dd   = (group - peak) / (peak + 1e-12) * 100.0
        return float(dd.min())
    monthly_dd = eq_series.resample('ME').apply(_month_dd)

    # Peor día
    daily_eq  = eq_series.resample('D').last().dropna()
    daily_ret = daily_eq.pct_change().fillna(0.0) * 100.0
    monthly_wd = daily_ret.resample('ME').min()

    # Stats por mes desde trades
    trades['close_time'] = pd.to_datetime(trades['close_time'])
    if trades['close_time'].dt.tz is not None:
        trades['close_time'] = trades['close_time'].dt.tz_localize(None)
    trades['month_end']  = trades['close_time'].dt.to_period('M').dt.to_timestamp('M')
    g = trades.groupby('month_end').agg(
        n_trades = ('pnl_usd', 'count'),
        n_wins   = ('pnl_usd', lambda x: (x > 0).sum()),
        pnl_sum  = ('pnl_usd', 'sum'),
    )
    g['wr_pct'] = g['n_wins'] / g['n_trades'] * 100.0

    # Asegurar que ambos índices estén sin tz
    if hasattr(month_eq.index, 'tz') and month_eq.index.tz is not None:
        month_eq.index = month_eq.index.tz_localize(None)
        monthly_ret.index = monthly_ret.index.tz_localize(None)
        monthly_dd.index = monthly_dd.index.tz_localize(None)
        monthly_wd.index = monthly_wd.index.tz_localize(None)

    # Combinar
    result = pd.DataFrame({
        'equity_end':    month_eq,
        'return_pct':    monthly_ret,
        'max_dd_pct':    monthly_dd,
        'worst_day_pct': monthly_wd,
    }).join(g[['n_trades','wr_pct']], how='left')
    result['n_trades'] = result['n_trades'].fillna(0).astype(int)
    result['wr_pct']   = result['wr_pct'].fillna(0.0)

    result['obj_m']   = result['return_pct']   >= 2.0
    result['obj_dd']  = result['max_dd_pct']   >= -7.0
    result['obj_tpm'] = result['n_trades']     >= 7
    # Peor día exento en 1D (swing, hold varios días)
    result['passes']  = result['obj_m'] & result['obj_dd'] & result['obj_tpm']

    # Guardar CSV
    csv_path = os.path.join(OUT_DIR, '1D_monthly.csv')
    save = result.copy()
    save.index.name = 'month_end'
    save = save.reset_index()
    save['month_end'] = save['month_end'].dt.strftime('%Y-%m')
    save['tf'] = '1D'
    save.to_csv(csv_path, index=False, float_format='%.4f')
    print(f"  → CSV guardado: {csv_path}")

    # Imprimir tabla
    print()
    print('='*80)
    print('  1D  —  GVF V3 (Gold Volume Fusion) — yfinance GC=F')
    print('  Señal: OBV + CMF + MFI + VROC + Score ≥ threshold')
    print('='*80)
    print(f"  {'Mes':<10} {'Retorno':>8} {'MaxDD':>8} {'PeorDia':>9} {'Trades':>7} {'WR%':>6} {'Equity':>12}  {'Obj?':>5}")
    print('  ' + '-'*75)
    for date, row in result.iterrows():
        ok = '✅' if row['passes'] else ('➖' if row['n_trades'] == 0 else '❌')
        print(f"  {date.strftime('%b %Y'):<10} {row['return_pct']:>+8.2f}% "
              f"{row['max_dd_pct']:>+8.2f}% {row['worst_day_pct']:>+9.2f}% "
              f"{row['n_trades']:>7}  {row['wr_pct']:>5.1f}%  {row['equity_end']:>12,.0f}  {ok}")

    p = result['passes'].sum(); t = len(result)
    print('  ' + '-'*75)
    print(f"  RESUMEN: {p}/{t} meses pasan | "
          f"Ȳ Ret={result['return_pct'].mean():+.2f}% | "
          f"Ȳ DD={result['max_dd_pct'].mean():.2f}% | "
          f"Ȳ T/mes={result['n_trades'].mean():.1f} | "
          f"Ȳ WR={result[result['wr_pct']>0]['wr_pct'].mean():.1f}%")
    print('='*80)

    return result

if __name__ == '__main__':
    run_1d_monthly()
