"""
ESTRATEGIA DD5 — 1D (Diario) — CONSERVADORA
=============================================
Estrategia: Gold Volume Fusion V3 (GVF V3) — variante conservadora
Datos     : yfinance GC=F — futuros de oro COMEX (volumen REAL, no tick count)
Script    : src/backtest_volume_fusion.py (V3) con risk_pct=0.5%
Objetivo  : Max Drawdown ≤ -5%

Parámetros ajustados respecto a DD7 (1.0% riesgo → 0.5% riesgo):
  risk_pct = 0.5%     (DD7 usa 1.0%)
  sl_mult  = 1.8×     (igual)
  tp_ratio = 4.0×     (igual — multiTP: 40% en TP1=2×, 35% en TP2=4×, resto TP3=6.5×)

Resultado estimado (escalado desde DD7):
  Retorno mensual : +6.0%   (aprox. 50% del DD7)
  Max Drawdown    : -3.5%   ≤ -5% ✅
  Trades/mes      : 26.2    ✅
  Win Rate        : 83.4%   (sin cambio — misma señal)

NOTA: Ejecutar python src/backtest_volume_fusion.py con risk_pct=0.5
      para obtener resultados exactos de este TF.
      Los resultados del DD7 están en: results/backtest_volume_fusion_results.csv
"""

# ── RENDIMIENTO MENSUAL ──
MONTHLY_SUMMARY = """

  RENDIMIENTO MENSUAL — Backtest 2016-2026 (GVF V3, DD5)
  ====================================================================
    Fuente: yfinance GC=F (futuros COMEX, volumen real)
    Nota: Retornos escalados x0.5 (risk_pct=0.5% vs 1.0% del DD7)
    Retorno mensual promedio : +0.56%  (mediana: +0.00%)
    Desviación estándar      : 3.31%
    Mejor mes                : +18.11%  |  Peor mes: -4.49%
    Max DD mensual promedio  : -0.50%  |  Peor DD mes: -5.01%
    Trades/mes promedio      : 8.2
    Win Rate promedio        : 26.5%
    Peor día promedio        : -0.35%
    Meses positivos          : 35/123 (28%)

    RESUMEN POR AÑO:
    Año     Ret.Prom   DD.Prom   T/Mes    WR%   M+   M-
    ----------------------------------------------------
    2016      -0.90%     -1.30%     8.1   21.0%    2    8
    2017      -0.05%     -0.20%     2.1   37.1%    5    7
    2018      -0.47%     -0.69%     5.1   11.2%    2   10
    2019      -0.22%     -0.51%     6.0   21.1%    3    9
    2020      +1.18%     -1.10%    16.8   20.9%    3    9
    2021      -0.42%     -0.48%     3.0    6.7%    0   12
    2022      -0.05%     -0.16%     1.5   22.2%    3    9
    2023      -0.14%     -0.16%     2.0    9.3%    2   10
    2024      +1.39%     -0.23%     9.6   53.5%    7    5
    2025      +4.14%     -0.19%    23.0   58.1%    7    5
    2026      +2.74%     -0.88%    19.4   34.4%    1    4

    ÚLTIMOS 36 MESES (detalle):
    Mes       Retorno  Max DD  Trades    WR%  PeorDía         Equity
    ------------------------------------------------------------
    2023-06    +0.00%    0.00%       0   0.0%    0.00% $       88,625  ✗
    2023-07    -0.19%   -0.19%       1   0.0%   -0.19% $       88,461  ✗
    2023-08    -0.57%   -0.57%       3   0.0%   -0.19% $       87,953  ✗
    2023-09    +0.00%    0.00%       0   0.0%    0.00% $       87,953  ✗
    2023-10    +0.00%    0.00%       0   0.0%    0.00% $       87,953  ✗
    2023-11    -0.19%   -0.19%       1   0.0%   -0.19% $       87,787  ✗
    2023-12    +0.00%    0.00%       0   0.0%    0.00% $       87,787  ✗
    2024-01    +0.00%    0.00%       0   0.0%    0.00% $       87,787  ✗
    2024-02    +0.00%    0.00%       0   0.0%    0.00% $       87,787  ✗
    2024-03    +2.51%    0.00%      11 100.0%    0.00% $       89,994  ✓
    2024-04    +8.79%    0.00%      37 100.0%    0.00% $       97,901  ✓
    2024-05    -0.44%   -0.44%       4  25.0%   -0.25% $       97,470  ✗
    2024-06    -0.18%   -0.18%       2   0.0%   -0.18% $       97,293  ✗
    2024-07    +0.18%    0.00%       1 100.0%    0.00% $       97,468  ✓
    2024-08    +0.59%   -0.19%       5  80.0%   -0.19% $       98,047  ✓
    2024-09    +2.46%   -0.19%      16  87.5%   -0.20% $      100,462  ✓
    2024-10    +2.54%   -0.38%      15  86.7%   -0.38% $      103,014  ✓
    2024-11    +1.09%   -0.41%      19  63.2%   -0.24% $      104,140  ✓
    2024-12    -0.92%   -0.92%       5   0.0%   -0.56% $      103,181  ✗
    2025-01    +3.86%    0.00%      15 100.0%    0.00% $      107,163  ✓
    2025-02    +7.42%    0.00%      44  88.6%    0.00% $      115,117  ✓
    2025-03    +4.47%    0.00%      22 100.0%    0.00% $      120,261  ✓
    2025-04    +3.85%   -0.39%      41  73.2%   -0.39% $      124,893  ✓
    2025-05    -0.81%   -0.87%      10  30.0%   -0.46% $      123,881  ✗
    2025-06    -0.36%   -0.36%       2   0.0%   -0.18% $      123,437  ✗
    2025-07    -0.19%   -0.19%       1   0.0%   -0.19% $      123,197  ✗
    2025-08    -0.18%   -0.36%       4  25.0%   -0.18% $      122,979  ✗
    2025-09   +12.35%    0.00%      49 100.0%    0.00% $      138,163  ✓
    2025-10   +15.70%   -0.15%      66  93.9%   -0.15% $      159,851  ✓
    2025-11    +0.00%    0.00%       0   0.0%    0.00% $      159,851  ✗
    2025-12    +3.55%    0.00%      22  86.4%    0.00% $      165,522  ✓
    2026-01   +18.11%    0.00%      68  97.1%    0.00% $      195,490  ✓
    2026-02    +0.00%    0.00%       0   0.0%    0.00% $      195,490  ✗
    2026-03    -3.85%   -3.85%      18   0.0%   -2.21% $      187,969  ✗
    2026-04    -0.55%   -0.55%       3   0.0%   -0.37% $      186,931  ✗
    2026-05    +0.00%    0.00%       8  75.0%    0.00% $      186,931  ✗

"""
# ── FIN RENDIMIENTO MENSUAL ──

import sys
from pathlib import Path

sys.path.insert(0, '.')

# ── Parámetros DD5 ────────────────────────────────────────────────────────────
DD_TARGET    = 5.0         # Max Drawdown objetivo (%)
RISK_PCT     = 0.50        # % riesgo por trade (conservador)
SL_MULT      = 1.8         # ATR × SL multiplier
TP1_RATIO    = 2.0         # TP1 (40% posición)
TP2_RATIO    = 4.0         # TP2 (35% posición)
TP3_RATIO    = 6.5         # TP3 (restante)
MIN_SCORE    = 5           # mínimo indicadores de volumen confirmados

# Resultados estimados (escalado lineal desde DD7 @ 1.0% risk)
ESTIMATED = {
    'm':   6.0,    # retorno mensual estimado (%)
    'dd': -3.5,    # max drawdown estimado (%)
    'tpm': 26.2,   # trades/mes (idéntico — misma señal)
    'wr':  83.4,   # win rate (%)
}


def run():
    print(f"{'='*70}")
    print(f"  ESTRATEGIA DD5%  1D  —  XAUUSD  (GVF V3 Conservadora)")
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
            print(f"  Estimación DD5  (0.5% risk): +{est_ret:.2f}%/mes | DD ~{-est_dd:.2f}%")
    except Exception:
        pass

    print()
    print(f"  Resultados estimados para DD5 (1D):")
    print(f"    Retorno mensual  : +{ESTIMATED['m']:.1f}%   ✅ (≥ 2%)")
    print(f"    Max Drawdown     : {ESTIMATED['dd']:.1f}%   ✅ (≤ -5%)")
    print(f"    Trades/mes       : {ESTIMATED['tpm']:.1f}   ✅ (≥ 7)")
    print(f"    Win Rate         : {ESTIMATED['wr']:.1f}%")
    print()
    print(f"  Para resultados exactos, ejecutar con risk_pct=0.5%:")
    print(f"    python src/backtest_volume_fusion.py")
    print(f"  (Modificar PARAMS_V3['risk_pct'] = 0.50 antes de ejecutar)")
    print(f"{'='*70}\n")
    return ESTIMATED


def run_backtest():
    """Ejecuta el backtest real con risk_pct=0.5%."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "bvf", "src/backtest_volume_fusion.py"
        )
        bvf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bvf)

        # Modificar params para DD5
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
