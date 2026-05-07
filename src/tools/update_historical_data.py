"""
update_historical_data.py
Descarga los datos M15 XAUUSD faltantes desde Dukascopy y los merge con el parquet principal.
Funciona en bloques trimestrales con resume automático si se interrumpe.

Uso:
    python3 src/tools/update_historical_data.py
"""
import sys, time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from src.dukascopy_loader import download_xauusd_m15

MAIN_PARQUET = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
TEMP_DIR     = Path("data/dukascopy/tmp_quarters")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Bloques trimestrales para mejor control de progreso y resume
QUARTERS = [
    ("2024-07-01", "2024-10-01"),
    ("2024-10-01", "2025-01-01"),
    ("2025-01-01", "2025-04-01"),
    ("2025-04-01", "2025-07-01"),
    ("2025-07-01", "2025-10-01"),
    ("2025-10-01", "2026-01-01"),
    ("2026-01-01", "2026-04-01"),
    ("2026-04-01", "2026-05-07"),
]

def download_all_quarters():
    results = []

    for start, end in QUARTERS:
        cache_file = TEMP_DIR / f"XAUUSD_15min_{start}_{end}.parquet"

        if cache_file.exists():
            df_q = pd.read_parquet(cache_file)
            print(f"✓ [{start} → {end}] ya descargado ({len(df_q):,} barras) — usando cache")
            results.append(df_q)
            continue

        print(f"\n▶ Descargando [{start} → {end}]...")
        t0 = time.time()
        try:
            df_q = download_xauusd_m15(
                start=start,
                end=end,
                save_parquet=False,
                max_workers=8,
            )
            df_q.to_parquet(cache_file, compression="snappy")
            elapsed = time.time() - t0
            print(f"  ✓ {len(df_q):,} barras guardadas en {elapsed:.0f}s → {cache_file.name}")
            results.append(df_q)
        except Exception as e:
            print(f"  ✗ Error en [{start}→{end}]: {e}")

    return results


def merge_and_save(new_parts):
    print(f"\n=== Mergeando datos ===")

    df_old = pd.read_parquet(MAIN_PARQUET)
    print(f"Datos existentes: {len(df_old):,} barras | {df_old.index[0]} → {df_old.index[-1]}")

    # Normalizar columnas a mayúsculas
    df_old.columns = [c.capitalize() for c in df_old.columns]

    new_frames = []
    for df in new_parts:
        if df is not None and not df.empty:
            df.columns = [c.capitalize() for c in df.columns]
            new_frames.append(df)

    if not new_frames:
        print("No hay datos nuevos para mergear.")
        return df_old

    df_new = pd.concat(new_frames).sort_index()
    df_new = df_new[~df_new.index.duplicated(keep="last")]
    print(f"Datos nuevos:     {len(df_new):,} barras | {df_new.index[0]} → {df_new.index[-1]}")

    df_merged = pd.concat([df_old, df_new]).sort_index()
    df_merged = df_merged[~df_merged.index.duplicated(keep="last")]
    df_merged = df_merged.sort_index()

    # Backup del original
    backup = MAIN_PARQUET.with_suffix(".parquet.bak")
    import shutil
    shutil.copy2(MAIN_PARQUET, backup)

    df_merged.to_parquet(MAIN_PARQUET, compression="snappy")
    size_mb = MAIN_PARQUET.stat().st_size / 1e6
    print(f"\n✅ Parquet actualizado: {MAIN_PARQUET}")
    print(f"   Total: {len(df_merged):,} barras | {df_merged.index[0]} → {df_merged.index[-1]}")
    print(f"   Tamaño: {size_mb:.1f} MB | Backup: {backup.name}")
    return df_merged


if __name__ == "__main__":
    print("=" * 60)
    print("  Actualización datos históricos XAUUSD M15")
    print("  Fuente: Dukascopy CDN (libre)")
    print("=" * 60)

    # Ver estado actual
    df_current = pd.read_parquet(MAIN_PARQUET)
    print(f"\nEstado actual: {len(df_current):,} barras | hasta {df_current.index[-1]}")

    t_total = time.time()
    parts = download_all_quarters()
    df_final = merge_and_save(parts)

    elapsed = time.time() - t_total
    print(f"\nTiempo total: {elapsed/60:.1f} min")
    years = (df_final.index[-1] - df_final.index[0]).days / 365.25
    print(f"Cobertura: {years:.1f} años de datos M15 disponibles")
