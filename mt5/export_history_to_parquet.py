"""
mt5/export_history_to_parquet.py
---------------------------------
Exporta historial XAUUSD M15 desde MetaTrader 5 a un archivo Parquet.

EJECUTAR EN WINDOWS con MT5 abierto:
    python export_history_to_parquet.py

Luego copiar el archivo generado al contenedor Linux:
    data/dukascopy/XAUUSD_15min_mt5.parquet

Requisitos:
    pip install MetaTrader5 pandas pyarrow
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: Instala el paquete:  pip install MetaTrader5")
    sys.exit(1)

# ── Configuración ──────────────────────────────────────────────────────────
SYMBOL     = "XAUUSD"
TIMEFRAME  = mt5.TIMEFRAME_M15
START_DATE = datetime(2015, 1, 1)   # MT5 en Windows NO acepta tzinfo — usar naive
END_DATE   = datetime.now()
OUT_FILE   = Path(__file__).parent.parent / "data" / "dukascopy" / "XAUUSD_15min_mt5.parquet"
# ──────────────────────────────────────────────────────────────────────────


def main():
    # Inicializar MT5
    if not mt5.initialize():
        print(f"ERROR: No se pudo conectar a MT5: {mt5.last_error()}")
        print("  Asegúrate de que MetaTrader 5 está abierto y logueado.")
        sys.exit(1)

    info = mt5.terminal_info()
    print(f"Conectado a: {info.name}  build={info.build}")
    print(f"Descargando {SYMBOL} M15 desde {START_DATE.date()} hasta {END_DATE.date()}...")

    # Asegurar que el símbolo está visible en Market Watch
    mt5.symbol_select(SYMBOL, True)

    # Descargar barras
    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, START_DATE, END_DATE)

    if rates is None or len(rates) == 0:
        print(f"ERROR: No se obtuvieron datos. {mt5.last_error()}")
        print("  Verifica que el símbolo XAUUSD está disponible en Market Watch.")
        mt5.shutdown()
        sys.exit(1)

    mt5.shutdown()

    # Convertir a DataFrame
    df = pd.DataFrame(rates)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.rename(columns={
        "open":        "Open",
        "high":        "High",
        "low":         "Low",
        "close":       "Close",
        "tick_volume": "Volume",
    })
    df = df.set_index("timestamp")[["Open", "High", "Low", "Close", "Volume"]]
    df = df.sort_index()

    # Guardar
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE)

    size_mb = OUT_FILE.stat().st_size / 1024 / 1024
    print(f"\n✓ Guardado: {OUT_FILE}")
    print(f"  Barras    : {len(df):,}")
    print(f"  Desde     : {df.index[0]}")
    print(f"  Hasta     : {df.index[-1]}")
    print(f"  Tamaño    : {size_mb:.1f} MB")
    print(f"  Precio min: {df.Low.min():.2f}  max: {df.High.max():.2f}")
    print("\nSiguiente paso:")
    print(f"  Copia este archivo a tu contenedor Linux en:")
    print(f"  /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet")


if __name__ == "__main__":
    main()
