"""
src/download_data.py — descarga 10 años XAUUSD M15 de Dukascopy.
=================================================================
RESUME AUTOMÁTICO:
  - Descarga en chunks de 6 meses.
  - Guarda checkpoint parquet después de cada chunk.
  - Al reiniciar detecta el último timestamp guardado y continúa
    desde ahí — nunca descarga dos veces el mismo período.

Uso:
    python -u src/download_data.py
    nohup python -u src/download_data.py >> data/download.log 2>&1 &
"""
import warnings; warnings.filterwarnings('ignore')
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
import pandas as pd
from src.dukascopy_loader import download_xauusd_m15

# ── Configuración ────────────────────────────────────────────────────────────
OUT       = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
START     = "2016-01-01"
END       = "2026-05-06"
TIMEFRAME = "15min"
CHUNK_MONTHS = 6   # checkpoint cada ~3 300 horas ≈ 7-10 min de descarga
MAX_WORKERS  = 32
# ─────────────────────────────────────────────────────────────────────────────

OUT.parent.mkdir(parents=True, exist_ok=True)


def get_resume_date() -> str:
    """Lee el parquet existente y devuelve la fecha desde la que continuar."""
    if OUT.exists() and OUT.stat().st_size > 10_000:   # >10 KB = datos reales
        try:
            df_prev = pd.read_parquet(OUT)
            if not df_prev.empty:
                last_ts  = df_prev.index[-1]
                # Continúa desde la siguiente hora completa tras la última barra
                resume   = (last_ts + pd.Timedelta(hours=1)).strftime("%Y-%m-%d")
                elapsed  = (pd.Timestamp(resume, tz="UTC") -
                            pd.Timestamp(START,  tz="UTC")).days
                total    = (pd.Timestamp(END,    tz="UTC") -
                            pd.Timestamp(START,  tz="UTC")).days
                pct      = elapsed / total * 100
                print(f"✦ Resume detectado: {len(df_prev):,} barras "
                      f"hasta {last_ts.date()} ({pct:.1f}% completado)")
                print(f"  Continuando desde {resume}", flush=True)
                return resume
        except Exception as e:
            print(f"⚠ No se pudo leer checkpoint: {e} — reiniciando desde {START}.")
    print(f"✦ Descarga nueva desde {START}", flush=True)
    return START


def generate_chunks(start: str, end: str, months: int = 6):
    """Devuelve lista de (chunk_start, chunk_end) de N meses cada uno."""
    cur    = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end,   tz="UTC")
    chunks = []
    while cur < end_ts:
        nxt = min(cur + pd.DateOffset(months=months), end_ts)
        chunks.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt
    return chunks


# ── Main ─────────────────────────────────────────────────────────────────────
resume_from = get_resume_date()

if resume_from >= END:
    print("✓ Descarga ya completa.")
    df_final = pd.read_parquet(OUT)
    size_mb  = OUT.stat().st_size / 1024 / 1024
    print(f"  {len(df_final):,} barras | {df_final.index[0]} → {df_final.index[-1]}")
    print(f"  Archivo: {OUT}  ({size_mb:.1f} MB)")
    sys.exit(0)

chunks = generate_chunks(resume_from, END, CHUNK_MONTHS)
total_elapsed = (pd.Timestamp(END,         tz="UTC") -
                 pd.Timestamp(START,        tz="UTC")).days
already_elapsed = (pd.Timestamp(resume_from, tz="UTC") -
                   pd.Timestamp(START,        tz="UTC")).days

print(f"  Chunks pendientes: {len(chunks)} × {CHUNK_MONTHS} meses\n", flush=True)

for i, (c_start, c_end) in enumerate(chunks, 1):
    print(f"\n[{i}/{len(chunks)}] {c_start} → {c_end} ...", flush=True)
    try:
        df_chunk = download_xauusd_m15(
            start=c_start, end=c_end,
            timeframe=TIMEFRAME,
            cache_dir="data/dukascopy",
            max_workers=MAX_WORKERS,
            show_progress=True,
            save_bi5=False,
            save_parquet=False,
        )
    except Exception as e:
        print(f"  ✗ ERROR en chunk {c_start}→{c_end}: {e}", flush=True)
        continue

    if df_chunk is None or df_chunk.empty:
        print(f"  ⚠ Chunk vacío ({c_start}→{c_end}), saltando.", flush=True)
        continue

    # Merge con checkpoint existente y guardar inmediatamente
    if OUT.exists() and OUT.stat().st_size > 10_000:
        try:
            df_prev   = pd.read_parquet(OUT)
            df_merged = pd.concat([df_prev, df_chunk]).sort_index()
            df_merged = df_merged[~df_merged.index.duplicated(keep="last")]
        except Exception:
            df_merged = df_chunk
    else:
        df_merged = df_chunk

    df_merged.to_parquet(OUT)
    size_mb  = OUT.stat().st_size / 1024 / 1024
    chunk_elapsed = (pd.Timestamp(c_end, tz="UTC") -
                     pd.Timestamp(START,  tz="UTC")).days
    pct = chunk_elapsed / total_elapsed * 100
    print(f"  ✓ Checkpoint: {len(df_merged):,} barras | {size_mb:.1f} MB | "
          f"{pct:.1f}% total", flush=True)

# ── Resumen final ─────────────────────────────────────────────────────────────
df_final = pd.read_parquet(OUT)
size_mb  = OUT.stat().st_size / 1024 / 1024
print(f"\n{'='*60}")
print(f"✓ DESCARGA COMPLETA")
print(f"  {len(df_final):,} barras M15")
print(f"  {df_final.index[0]} → {df_final.index[-1]}")
print(f"  {size_mb:.1f} MB  →  {OUT}")
