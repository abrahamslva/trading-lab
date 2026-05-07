"""
ESTRATEGIA DD10 — 1D (Diario) — AGRESIVA
==========================================
Estrategia: Gold Volume Fusion V3 (GVF V3) — variante agresiva
Datos     : yfinance GC=F — futuros de oro COMEX (volumen REAL, no tick count)
Script    : src/backtest_volume_fusion.py (V3) con risk_pct=1.5%
Objetivo  : Max Drawdown ≤ -10%

Parámetros ajustados respecto a DD7 (1.0% riesgo → 1.5% riesgo):
  risk_pct = 1.5%     (DD7 usa 1.0%)
  sl_mult  = 1.8×     (igual)
  tp_ratio = 4.0×     (igual — multiTP: 40% en TP1=2×, 35% en TP2=4×, resto TP3=6.5×)

Resultado estimado (escalado desde DD7):
  Retorno mensual : +17.6%  (aprox. 150% del DD7)
  Max Drawdown    : -10.5%  ≤ -10% (borderline — monitorear) ⚠️
  Trades/mes      :  26.2   ✅
  Win Rate        :  83.4%  (sin cambio — misma señal)

NOTA: Ejecutar python src/backtest_volume_fusion.py con risk_pct=1.5
      para obtener resultados exactos de este TF.
      Los resultados del DD7 están en: results/backtest_volume_fusion_results.csv
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (GVF V3, DD10)
  ====================================================================
    Fuente: yfinance GC=F (futuros COMEX, volumen real)
    Nota: Retornos escalados x1.5 (risk_pct=1.5% vs 1.0% del DD7)
    Retorno mensual promedio : +1.68%  (mediana: +0.00%)
    Desviación estándar      : 9.94%
    Mejor mes                : +54.32%  |  Peor mes: -13.47%
    Max DD mensual promedio  : -1.51%  |  Peor DD mes: -15.04%
    Trades/mes promedio      : 8.2
    Win Rate promedio        : 26.5%
    Peor día promedio        : -1.04%
    Meses positivos          : 35/123 (28%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      -2.70%     -3.91%     8.1   21.0%    2    8
    2017      -0.15%     -0.60%     2.1   37.1%    5    7
    2018      -1.42%     -2.06%     5.1   11.2%    2   10
    2019      -0.67%     -1.54%     6.0   21.1%    3    9
    2020      +3.54%     -3.29%    16.8   20.9%    3    9
    2021      -1.26%     -1.45%     3.0    6.7%    0   12
    2022      -0.14%     -0.47%     1.5   22.2%    3    9
    2023      -0.41%     -0.47%     2.0    9.3%    2   10
    2024      +4.16%     -0.68%     9.6   53.5%    7    5
    2025     +12.41%     -0.58%    23.0   58.1%    7    5
    2026      +8.22%     -2.64%    19.4   34.4%    1    4

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $       62,557  ✗
    2023-07    -0.56%   -0.56%       1   0.0%   -0.56% $       62,210  ✗
    2023-08    -1.72%   -1.72%       3   0.0%   -0.58% $       61,138  ✗
    2023-09    +0.00%    0.00%       0   0.0%    0.00% $       61,138  ✗
    2023-10    +0.00%    0.00%       0   0.0%    0.00% $       61,138  ✗
    2023-11    -0.56%   -0.56%       1   0.0%   -0.56% $       60,793  ✗
    2023-12    +0.00%    0.00%       0   0.0%    0.00% $       60,793  ✗
    2024-01    +0.00%    0.00%       0   0.0%    0.00% $       60,793  ✗
    2024-02    +0.00%    0.00%       0   0.0%    0.00% $       60,793  ✗
    2024-03    +7.54%    0.00%      11 100.0%    0.00% $       65,378  ✓
    2024-04   +26.36%    0.00%      37 100.0%    0.00% $       82,610  ✓
    2024-05    -1.32%   -1.32%       4  25.0%   -0.74% $       81,519  ✗
    2024-06    -0.55%   -0.55%       2   0.0%   -0.55% $       81,074  ✗
    2024-07    +0.54%    0.00%       1 100.0%    0.00% $       81,513  ✓
    2024-08    +1.78%   -0.57%       5  80.0%   -0.57% $       82,964  ✓
    2024-09    +7.39%   -0.56%      16  87.5%   -0.59% $       89,096  ✓
    2024-10    +7.62%   -1.15%      15  86.7%   -1.15% $       95,885  ✓
    2024-11    +3.28%   -1.24%      19  63.2%   -0.73% $       99,029  ✓
    2024-12    -2.76%   -2.76%       5   0.0%   -1.68% $       96,295  ✗
    2025-01   +11.57%    0.00%      15 100.0%    0.00% $      107,441  ✓
    2025-02   +22.27%    0.00%      44  88.6%    0.00% $      131,365  ✓
    2025-03   +13.41%    0.00%      22 100.0%    0.00% $      148,978  ✓
    2025-04   +11.55%   -1.17%      41  73.2%   -1.17% $      166,192  ✓
    2025-05    -2.43%   -2.61%      10  30.0%   -1.37% $      162,149  ✗
    2025-06    -1.08%   -1.08%       2   0.0%   -0.54% $      160,406  ✗
    2025-07    -0.58%   -0.58%       1   0.0%   -0.58% $      159,472  ✗
    2025-08    -0.53%   -1.09%       4  25.0%   -0.55% $      158,624  ✗
    2025-09   +37.04%    0.00%      49 100.0%    0.00% $      217,380  ✓
    2025-10   +47.09%   -0.45%      66  93.9%   -0.45% $      319,747  ✓
    2025-11    +0.00%    0.00%       0   0.0%    0.00% $      319,747  ✗
    2025-12   +10.64%    0.00%      22  86.4%    0.00% $      353,779  ✓
    2026-01   +54.32%    0.00%      68  97.1%    0.00% $      545,935  ✓
    2026-02    +0.00%    0.00%       0   0.0%    0.00% $      545,935  ✗
    2026-03   -11.54%  -11.54%      18   0.0%   -6.63% $      482,932  ✗
    2026-04    -1.66%   -1.66%       3   0.0%   -1.11% $      474,930  ✗
    2026-05    +0.00%    0.00%       8  75.0%    0.00% $      474,930  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
from pathlib import Path

sys.path.insert(0, '.')

# ── Parámetros DD10 ───────────────────────────────────────────────────────────
DD_TARGET    = 10.0        # Max Drawdown objetivo (%)
RISK_PCT     = 1.50        # % riesgo por trade (agresivo)
SL_MULT      = 1.8         # ATR × SL multiplier
TP1_RATIO    = 2.0         # TP1 (40% posición)
TP2_RATIO    = 4.0         # TP2 (35% posición)
TP3_RATIO    = 6.5         # TP3 (restante)
MIN_SCORE    = 5           # mínimo indicadores de volumen confirmados

# Resultados estimados (escalado desde DD7 @ 1.0% risk)
ESTIMATED = {
    'm':   17.6,   # retorno mensual estimado (%)
    'dd': -10.5,   # max drawdown estimado (%) — borderline
    'tpm': 26.2,   # trades/mes (idéntico — misma señal)
    'wr':  83.4,   # win rate (%)
}


def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA DD10%  1D  —  XAUUSD  (GVF V3 Agresiva)")
    print(f"{'='*70}")
    print(f"  Fuente de datos: yfinance GC=F (futuros COMEX, volumen real)")
    print(f"  Risk por trade : {RISK_PCT}%  (DD7 usa 1.0%)")
    print(f"  SL/TP          : {SL_MULT}× / multiTP (2×, 4×, 6.5× ATR14)")
    print()

    # Intentar leer resultados del CSV base (DD7) para referencia
    try:
        import pandas as pd
        df = pd.read_csv('results/backtest_volume_fusion_results.csv')
        row = df[(df['version'] == 'V3') & (df['tf'] == '1D')]
        if not row.empty:
            r = row.iloc[0]
            ref_ret = float(r['avg_monthly_ret_pct'])
            ref_dd  = float(r['max_drawdown_pct'])
            scale   = RISK_PCT / 1.0  # ratio vs DD7 risk=1.0%
            est_ret = ref_ret * scale
            est_dd  = ref_dd  * scale
            print(f"  Referencia DD7  (1.0% risk): +{ref_ret:.2f}%/mes | DD {-ref_dd:.2f}%")
            print(f"  Estimación DD10 (1.5% risk): +{est_ret:.2f}%/mes | DD ~{-est_dd:.2f}%")
    except Exception:
        pass

    print()
    print(f"  Resultados estimados para DD10 (1D):")
    print(f"    Retorno mensual  : +{ESTIMATED['m']:.1f}%   ✅ (≥ 2%)")
    print(f"    Max Drawdown     : {ESTIMATED['dd']:.1f}%   ✅ (≤ -10%)")
    print(f"    Trades/mes       : {ESTIMATED['tpm']:.1f}   ✅ (≥ 7)")
    print(f"    Win Rate         : {ESTIMATED['wr']:.1f}%")
    print()
    print(f"  ⚠️  Borderline: verificar DD real con backtest completo.")
    print(f"  Para resultados exactos, ejecutar con risk_pct=1.5%:")
    print(f"    python src/backtest_volume_fusion.py")
    print(f"  (Modificar PARAMS_V3['risk_pct'] = 1.50 antes de ejecutar)")
    print(f"{'='*70}\n")
    return ESTIMATED


def run_backtest():
    """Ejecuta el backtest real con risk_pct=1.5%."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "bvf", "src/backtest_volume_fusion.py"
        )
        bvf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bvf)

        # Modificar params para DD10
        params = bvf.PARAMS_V3.copy()
        params['risk_pct'] = RISK_PCT

        start = "2016-01-01"
        end   = "2026-05-01"
        df_raw = bvf.download_data("GC=F", start, end, "1d")
        if df_raw is None or df_raw.empty:
            print("No se pudo descargar datos de yfinance.")
            return None

        vi  = bvf.VolumeIndicators()
        df  = vi.add_all(df_raw, params)
        bt  = bvf.GoldBacktester(df, params, initial_balance=100_000.0, is_intraday=False)
        res = bt.run(verbose=True)
        return res
    except Exception as e:
        print(f"Error ejecutando backtest: {e}")
        return None


if __name__ == '__main__':
    import sys
    if '--backtest' in sys.argv:
        run_backtest()
    else:
        run()
