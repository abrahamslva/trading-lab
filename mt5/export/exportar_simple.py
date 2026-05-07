"""
mt5/exportar_simple.py  —  VERSION SIMPLE
==========================================
Exporta XAUUSD M15 desde MT5 con UNA sola llamada.
No usa fechas — pide las ultimas N barras directamente.

EJECUTAR EN WINDOWS con MT5 abierto:
    python mt5\exportar_simple.py

Luego arrastra el archivo generado al VS Code (carpeta data/dukascopy/).

Requisitos: pip install MetaTrader5 pandas pyarrow
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: pip install MetaTrader5")
    sys.exit(1)

SYMBOL   = "XAUUSD"
N_BARS   = 500_000          # pide hasta 500k barras (el broker devuelve lo que tenga)
OUT_FILE = Path(__file__).parent.parent / "data" / "dukascopy" / "XAUUSD_15min_mt5.parquet"

if not mt5.initialize():
    print(f"ERROR al conectar MT5: {mt5.last_error()}")
    sys.exit(1)

mt5.symbol_select(SYMBOL, True)

print(f"Descargando hasta {N_BARS:,} barras M15 de {SYMBOL}...")
rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M15, 0, N_BARS)
mt5.shutdown()

if rates is None or len(rates) == 0:
    print(f"ERROR: sin datos. {mt5.last_error()}")
    sys.exit(1)

df = pd.DataFrame(rates)
df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
df = df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                         "close": "Close", "tick_volume": "Volume"})
df = df.set_index("timestamp")[["Open", "High", "Low", "Close", "Volume"]]
df = df.sort_index()

OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT_FILE)

size_mb = OUT_FILE.stat().st_size / 1024 / 1024
print(f"\n✓ Listo!")
print(f"  Barras : {len(df):,}")
print(f"  Desde  : {df.index[0]}")
print(f"  Hasta  : {df.index[-1]}")
print(f"  Archivo: {OUT_FILE}  ({size_mb:.1f} MB)")
print(f"\nAhora arrastra el archivo al VS Code en:")
print(f"  data/dukascopy/XAUUSD_15min_mt5.parquet")
