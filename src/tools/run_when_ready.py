"""
src/run_when_ready.py
----------------------
Espera a que el parquet de datos esté listo y lanza el backtest automáticamente.
Corre en background con: nohup python -u src/run_when_ready.py > data/backtest.log 2>&1 &
"""
import time
import subprocess
import sys
import os
from pathlib import Path

PARQUET    = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
MIN_SIZE_MB = 150  # parquet 10 años M15 debe pesar ~150 MB (DATOS COMPLETOS)

print("Esperando TODOS los datos (10 años XAUUSD M15 completos, ~150 MB)...", flush=True)

while True:
    if PARQUET.exists():
        size_mb = PARQUET.stat().st_size / 1024 / 1024
        percent_complete = (size_mb / MIN_SIZE_MB) * 100
        if size_mb >= MIN_SIZE_MB:
            print(f"\n✓✓✓ DATOS COMPLETOS: {size_mb:.1f} MB ({percent_complete:.1f}%) — lanzando backtest completo...", flush=True)
            break
        else:
            print(f"  Parquet: {size_mb:.1f} MB de {MIN_SIZE_MB} MB ({percent_complete:.1f}%)... esperando...", flush=True)
    else:
        print("  Esperando parquet...", flush=True)
    time.sleep(30)

# Lanzar backtest_full (nuevo engine: 6 versiones × 7 timeframes)
print("\n▶ src/backtest_full.py  (6 iteraciones × 7 TFs = 42 combinaciones)", flush=True)
result = subprocess.run(
    [sys.executable, "-u", "src/backtest_full.py"],
    cwd=Path(__file__).parent.parent,
)
sys.exit(result.returncode)
