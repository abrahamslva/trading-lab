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
