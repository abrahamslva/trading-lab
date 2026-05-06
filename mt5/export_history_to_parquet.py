"""
mt5/export_history_to_parquet.py
---------------------------------
Exporta historial XAUUSD M15 desde MetaTrader 5 a un archivo Parquet.
Descarga por chunks anuales para evitar el límite del broker en copy_rates_range.

EJECUTAR EN WINDOWS con MT5 abierto:
    python mt5\\export_history_to_parquet.py

Luego copiar el archivo generado al contenedor Linux:
    data/dukascopy/XAUUSD_15min_mt5.parquet

Requisitos:
    pip install MetaTrader5 pandas pyarrow
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: Instala el paquete:  pip install MetaTrader5")
    sys.exit(1)

# ── Configuración ──────────────────────────────────────────────────────────
SYMBOL    = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_M15
END_DATE  = datetime.now()
OUT_FILE  = Path(__file__).parent.parent / "data" / "dukascopy" / "XAUUSD_15min_mt5.parquet"

# Años candidatos para buscar el inicio del historial (de más antiguo a más reciente)
CANDIDATE_YEARS = [2015, 2017, 2019, 2020, 2021, 2022, 2023, 2024]
# ──────────────────────────────────────────────────────────────────────────


def detect_start_year(symbol: str, timeframe: int) -> int:
    """Prueba años candidatos y devuelve el más antiguo con datos disponibles."""
    print("Detectando historial disponible en el broker...")
    found = None
    for year in CANDIDATE_YEARS:
        t0 = datetime(year, 1, 1)
        t1 = datetime(year, 1, 8)
        rates = mt5.copy_rates_range(symbol, timeframe, t0, t1)
        if rates is not None and len(rates) > 0:
            print(f"  ✓ Datos disponibles en {year}")
            if found is None:
                found = year  # guardar solo el más antiguo
        else:
            print(f"  ✗ Sin datos en {year}: {mt5.last_error()}")
    if found is None:
        print("ERROR: No se encontraron datos para ningún año candidato.")
        mt5.shutdown()
        sys.exit(1)
    print(f"  → Iniciando descarga desde {found}")
    return found


def fetch_year_chunk(symbol: str, timeframe: int, year: int, end_date: datetime):
    """Descarga un chunk de un año (o hasta end_date si es el año actual)."""
    t0 = datetime(year, 1, 1)
    t1 = datetime(year + 1, 1, 1) if year < end_date.year else end_date
    rates = mt5.copy_rates_range(symbol, timeframe, t0, t1)
    if rates is None:
        return None
    return rates


def main():
    # Inicializar MT5
    if not mt5.initialize():
        print(f"ERROR: No se pudo conectar a MT5: {mt5.last_error()}")
        print("  Asegúrate de que MetaTrader 5 está abierto y logueado.")
        sys.exit(1)

    info = mt5.terminal_info()
    print(f"Conectado a: {info.name}  build={info.build}")

    # Asegurar que el símbolo está visible en Market Watch
    mt5.symbol_select(SYMBOL, True)

    # Detectar año inicial disponible
    start_year = detect_start_year(SYMBOL, TIMEFRAME)

    # Descargar por chunks anuales
    all_chunks = []
    current_year = END_DATE.year
    years = list(range(start_year, current_year + 1))
    print(f"\nDescargando {len(years)} año(s) de datos M15...")

    for year in years:
        rates = fetch_year_chunk(SYMBOL, TIMEFRAME, year, END_DATE)
        if rates is not None and len(rates) > 0:
            all_chunks.append(pd.DataFrame(rates))
            print(f"  {year}: {len(rates):,} barras")
        else:
            err = mt5.last_error()
            # Error (-2) en años sin mercado (fines de año) es esperado
            print(f"  {year}: sin datos ({err})")

    mt5.shutdown()

    if not all_chunks:
        print("ERROR: No se obtuvieron datos en ningún chunk.")
        sys.exit(1)

    # Combinar todos los chunks
    df = pd.concat(all_chunks, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.rename(columns={
        "open":        "Open",
        "high":        "High",
        "low":         "Low",
        "close":       "Close",
        "tick_volume": "Volume",
    })
    df = df.set_index("timestamp")[["Open", "High", "Low", "Close", "Volume"]]
    df = df[~df.index.duplicated(keep="last")].sort_index()

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
    print("  Copia este archivo a tu contenedor Linux en:")
    print("  /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet")


if __name__ == "__main__":
    main()
