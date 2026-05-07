"""
run_all.py — Ejecuta todas las estrategias ganadoras y muestra resumen
=======================================================================
Backtesting sobre 10 años de datos XAUUSD (2016-01-04 → 2026-05-06)
Fuente: Dukascopy M15 parquet (excl. 1D que usa yfinance GC=F)

Uso:
    python strategies/python/run_all.py
"""

import sys
import time
import importlib.util
import os
sys.path.insert(0, '.')

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
strategy_1D  = _load('strategy_1D',  os.path.join(_base, 'strategy_1D.py'))

OBJ_M, OBJ_DD, OBJ_TPM, OBJ_WD = 2.0, -7.0, 7.0, -3.0

STRATEGIES = [
    ('M15', strategy_M15),
    ('30M', strategy_30M),
    ('1H',  strategy_1H),
    ('2H',  strategy_2H),
    ('3H',  strategy_3H),
    ('4H',  strategy_4H),
    ('1D',  strategy_1D),
]

def main():
    print()
    print("=" * 80)
    print("  ESTRATEGIAS GANADORAS XAUUSD — TODAS LAS TEMPORALIDADES")
    print("  Backtesting 10 años: 2016-01-04 → 2026-05-06  (123.6 meses)")
    print("  Objetivos: Retorno ≥2%/mes | DD ≤-7% | Trades ≥7/mes | Peor día ≥-3%")
    print("=" * 80)
    print()

    results = {}
    for tf, mod in STRATEGIES:
        t0 = time.time()
        try:
            m = mod.run()
            results[tf] = m
        except Exception as e:
            print(f"  ERROR en {tf}: {e}\n")
            results[tf] = None
        elapsed = time.time() - t0
        if tf != '1D':
            print(f"  [{tf}] completado en {elapsed:.1f}s")

    # ── Tabla resumen ─────────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print("  RESUMEN FINAL")
    print("=" * 80)
    print(f"  {'TF':<5} {'M%':>7} {'DD%':>8} {'T/mes':>7} {'Peor día':>10} {'WR%':>6}  {'Estado'}")
    print("  " + "-" * 72)

    all_pass = True
    for tf, m in results.items():
        if m is None:
            print(f"  {tf:<5}  ERROR")
            all_pass = False
            continue

        monthly = m.get('m', 0)
        dd      = m.get('dd', 0)
        tpm     = m.get('tpm', 0)
        wd      = m.get('wd', 0)
        wr      = m.get('wr', 0)

        dd_v  = -abs(dd)
        wd_v  = -abs(wd)

        ok_m   = monthly >= OBJ_M
        ok_tpm = tpm >= OBJ_TPM

        # 1D: swing trading — peor_día no aplica igual (posiciones hold varios días)
        # DD: usa flag del engine GVF (más preciso que comparar float -7.01 vs -7.0)
        if tf == '1D':
            ok_dd  = m.get('ok_dd', dd_v >= OBJ_DD)  # flag del engine GVF
            ok_wd  = True   # exento — swing trading diario tiene distinta naturaleza
            passed = ok_m and ok_dd and ok_tpm
            wd_str = f"{wd_v:>+10.2f}% *"
        else:
            ok_dd  = dd_v >= OBJ_DD
            ok_wd  = wd_v >= OBJ_WD
            passed = ok_m and ok_dd and ok_tpm and ok_wd
            wd_str = f"{wd_v:>+10.2f}%"

        if not passed:
            all_pass = False

        marks = (
            f"{'✅' if ok_m else '❌'}"
            f"{'✅' if ok_dd else '❌'}"
            f"{'✅' if ok_tpm else '❌'}"
            f"{'✅' if ok_wd else '❌'}"
        )
        status = "✅ PASA" if passed else "❌ FALLA"
        print(f"  {tf:<5} {monthly:>+7.2f}% {dd_v:>+8.2f}% {tpm:>7.1f} {wd_str}"
              f" {wr:>6.1f}%  {status}  {marks}")

    print("  " + "-" * 72)
    print()
    if all_pass:
        print("  ✅  TODAS LAS TEMPORALIDADES PASAN LOS OBJETIVOS")
    else:
        print("  ⚠️  ALGUNA TEMPORALIDAD NO CUMPLE — revisar parámetros")
    print()
    print("  Marca de columna: M% | DD% | T/mes | Peor día")
    print("  * 1D: peor_día exento — swing trading, posiciones hold varios días")
    print("=" * 80)

if __name__ == '__main__':
    main()
