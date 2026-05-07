#!/usr/bin/env python3
"""
src/monitor_and_autotest.py — Monitor descarga Dukascopy + Auto-backtest
=========================================================================
Monitorea descarga Dukascopy en tiempo real.
Cuando complete (150 MB), lanza backtest_full.py automáticamente.
Corre en background sin interrución.
"""
import time
import subprocess
import sys
from pathlib import Path
import logging

# Configuración logs
log_file = Path("data/autotest.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("monitor")

DATA_FILE = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
MIN_SIZE_MB = 150  # Cambiar a 12 cuando pruebe yfinance
CHECK_INTERVAL = 60  # segundos

logger.info("=" * 70)
logger.info("  MONITOR & AUTO-BACKTEST PIPELINE")
logger.info("=" * 70)
logger.info(f"  Monitoreo: {DATA_FILE}")
logger.info(f"  Umbral: {MIN_SIZE_MB} MB")
logger.info(f"  Intervalo: {CHECK_INTERVAL} seg")
logger.info("=" * 70)

def get_file_size_mb():
    """Retorna tamaño en MB, 0 si no existe."""
    if DATA_FILE.exists():
        return DATA_FILE.stat().st_size / 1024 / 1024
    return 0

def launch_backtest(data_source="dukascopy"):
    """Lanza backtest completo en background."""
    script = "src/backtest_full.py"
    logger.info(f"🚀 LANZANDO BACKTEST: python {script}")
    
    try:
        proc = subprocess.Popen(
            ["python3", script],
            stdout=open("data/backtest.log", "w"),
            stderr=subprocess.STDOUT,
            cwd="/workspaces/trading-lab",
        )
        logger.info(f"✓ Backtest iniciado (PID {proc.pid})")
        return proc.pid
    except Exception as e:
        logger.error(f"ERROR lanzando backtest: {e}")
        return None

# Monitoreo principal
last_size = 0
check_count = 0

try:
    while True:
        current_size = get_file_size_mb()
        check_count += 1
        
        # Log cada 10 chequeos
        if check_count % 10 == 0:
            progress = (current_size / MIN_SIZE_MB * 100) if MIN_SIZE_MB > 0 else 0
            logger.info(f"📊 Progreso: {current_size:.1f} MB / {MIN_SIZE_MB} MB ({progress:.1f}%)")
        
        # Si creció desde último chequeo
        if current_size > last_size:
            last_size = current_size
        
        # Cuando alcanza umbral
        if current_size >= MIN_SIZE_MB:
            logger.info(f"🎯 DATOS COMPLETOS: {current_size:.1f} MB >= {MIN_SIZE_MB} MB")
            logger.info("⚗️ INICIANDO BACKTEST COMPLETO...")
            
            pid = launch_backtest()
            if pid:
                logger.info("✓ Backtest en ejecución. Monitoreo completado.")
            break
        
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    logger.warning("Monitoreo detenido por usuario (Ctrl+C)")
    sys.exit(0)
except Exception as e:
    logger.error(f"ERROR CRÍTICO: {e}")
    sys.exit(1)
