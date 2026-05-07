"""
mt5/export_history.py — Exporta histórico XAUUSD desde MT5 a parquet
======================================================================
CORRE EN WINDOWS (donde está instalado MT5).
NO funciona en Codespace/Linux — es exclusivo del paquete MetaTrader5.

Pasos:
  1. Abrir MT5 en tu PC (estar logueado con tu broker)
  2. Abrir una terminal PowerShell/CMD en la carpeta del repo:
       cd C:\\ruta\\al\\repo\\trading-lab
  3. Instalar dependencias si no las tienes:
       pip install MetaTrader5 pandas pyarrow
  4. Ejecutar:
       python mt5/export_history.py
  5. Se crea el archivo: data/dukascopy/XAUUSD_15min_mt5.parquet
  6. Subir a Codespace:
       gh codespace cp data/dukascopy/XAUUSD_15min_mt5.parquet \\
           remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
     O bien desde VS Code: arrastrar el archivo al explorador de Codespace.

Nota sobre historia disponible en MT5:
  MT5 guarda por defecto ~2-5 años según el broker.
  Para ampliar a 10 años: abre el gráfico XAUUSD M15 → clic en fecha más
  antigua → MT5 descargará automáticamente más historia del servidor.
  Luego vuelve a ejecutar este script.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# ── Verificación plataforma ──────────────────────────────────────────────────
if sys.platform != "win32":
    print("ERROR: Este script solo funciona en Windows con MT5 instalado.")
    print("En Codespace usa: python src/download_data.py  (Dukascopy CDN)")
    sys.exit(1)

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: MetaTrader5 no instalado.")
    print("  pip install MetaTrader5")
    sys.exit(1)

try:
    import pandas as pd
    import pyarrow  # noqa: F401
except ImportError:
    print("ERROR: pandas / pyarrow no instalados.")
    print("  pip install pandas pyarrow")
    sys.exit(1)

# ── Configuración ─────────────────────────────────────────────────────────────
SYMBOL       = "XAUUSD"          # Cambia a "GOLD" si tu broker lo llama así
TIMEFRAME    = mt5.TIMEFRAME_M15  # M15 = gráfico de 15 minutos
START        = datetime(2016, 1, 1, tzinfo=timezone.utc)  # Inicio histórico
END          = datetime.now(timezone.utc)                  # Hasta hoy
CHUNK_MONTHS = 6                  # Descarga de a 6 meses para evitar timeouts

# Ruta de salida relativa al repo (corre desde la raíz del repo)
OUT_DIR  = Path("data") / "dukascopy"
OUT_FILE = OUT_DIR / "XAUUSD_15min_mt5.parquet"
# ─────────────────────────────────────────────────────────────────────────────


def connect_mt5():
    """Inicializa MT5. No requiere credenciales si ya está abierto y logueado."""
    if not mt5.initialize():
        err = mt5.last_error()
        print(f"ERROR: mt5.initialize() falló: {err}")
        print("  Asegúrate de que MT5 esté abierto y logueado con tu broker.")
        sys.exit(1)

    info = mt5.account_info()
    if info:
        print(f"✓ MT5 conectado | Cuenta: {info.login} | Broker: {info.server}")
        print(f"  Balance: {info.balance:.2f} {info.currency}")
    else:
        print("✓ MT5 inicializado (sin cuenta activa — solo lectura de historia)")


def ensure_symbol():
    """Activa el símbolo en Market Watch para que MT5 pueda entregar historia."""
    if not mt5.symbol_select(SYMBOL, True):
        print(f"ERROR: No se pudo activar {SYMBOL}.")
        print(f"  Verifica que tu broker ofrece {SYMBOL}. "
              f"Prueba 'GOLD' si XAUUSD no existe.")
        mt5.shutdown()
        sys.exit(1)

    info = mt5.symbol_info(SYMBOL)
    if info is None:
        print(f"ERROR: símbolo {SYMBOL} no encontrado.")
        mt5.shutdown()
        sys.exit(1)

    print(f"✓ Símbolo: {SYMBOL} | Dígitos: {info.digits} | "
          f"Spread: {info.spread} puntos")


def generate_chunks(start: datetime, end: datetime, months: int = 6):
    """Lista de (inicio, fin) de N meses cada uno."""
    cur    = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    chunks = []
    while cur < end_ts:
        nxt = min(cur + pd.DateOffset(months=months), end_ts)
        chunks.append((cur.to_pydatetime(), nxt.to_pydatetime()))
        cur = nxt
    return chunks


def download_history() -> pd.DataFrame:
    """Descarga el histórico completo en chunks y devuelve DataFrame OHLCV."""
    chunks = generate_chunks(START, END, CHUNK_MONTHS)
    total  = len(chunks)
    print(f"\n  Descargando {total} chunks × {CHUNK_MONTHS} meses "
          f"({START.year} → {END.year})...")

    # Resume: si ya existe parquet, continúa desde donde quedó
    all_frames = []
    resume_from = START

    if OUT_FILE.exists() and OUT_FILE.stat().st_size > 10_000:
        try:
            df_prev = pd.read_parquet(OUT_FILE)
            if not df_prev.empty:
                resume_from = df_prev.index[-1].to_pydatetime() + \
                              pd.Timedelta(minutes=15)
                pct = (resume_from - START).days / (END - START).days * 100
                print(f"  ✦ Resume: {len(df_prev):,} barras ya descargadas "
                      f"hasta {df_prev.index[-1].date()} ({pct:.1f}%)")
                all_frames.append(df_prev)
        except Exception as e:
            print(f"  ⚠ No se pudo leer parquet previo: {e}")

    # Filtrar chunks ya descargados
    pending = [(s, e) for s, e in chunks
               if pd.Timestamp(e) > pd.Timestamp(resume_from)]

    if not pending:
        print("  ✓ Descarga ya completa — cargando parquet existente.")
        return pd.read_parquet(OUT_FILE)

    print(f"  Chunks pendientes: {len(pending)}/{total}\n")

    for i, (c_start, c_end) in enumerate(pending, 1):
        rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, c_start, c_end)
        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            print(f"  [{i}/{len(pending)}] ⚠ Sin datos {c_start.date()}→"
                  f"{c_end.date()} | error={err}")
            continue

        df_c = pd.DataFrame(rates)
        df_c["time"] = pd.to_datetime(df_c["time"], unit="s", utc=True)
        df_c.set_index("time", inplace=True)
        all_frames.append(df_c)

        # Checkpoint después de cada chunk
        df_partial = pd.concat(all_frames).sort_index()
        df_partial  = df_partial[~df_partial.index.duplicated(keep="last")]
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        df_partial.to_parquet(OUT_FILE)

        pct  = i / len(pending) * 100
        size = OUT_FILE.stat().st_size / 1024 / 1024
        print(f"  [{i}/{len(pending)}] {pct:.0f}% | {c_start.date()}→{c_end.date()} "
              f"| {len(rates):,} barras | total {len(df_partial):,} | {size:.1f} MB")

    df_final = pd.concat(all_frames).sort_index()
    df_final  = df_final[~df_final.index.duplicated(keep="last")]
    return df_final


def main():
    print("=" * 60)
    print("  MT5 → Parquet Exporter | XAUUSD M15")
    print("=" * 60)

    connect_mt5()
    ensure_symbol()

    df = download_history()

    # Normalizar columnas para compatibilidad con backtest_full.py
    df.columns = [c.lower() for c in df.columns]
    rename = {"tick_volume": "volume"}
    df.rename(columns=rename, inplace=True)
    keep = [c for c in ["open","high","low","close","volume"] if c in df.columns]
    df = df[keep].dropna()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE)
    size_mb = OUT_FILE.stat().st_size / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"✓ EXPORTACIÓN COMPLETA")
    print(f"  {len(df):,} barras M15")
    print(f"  {df.index[0]} → {df.index[-1]}")
    print(f"  {size_mb:.1f} MB  →  {OUT_FILE}")
    print(f"{'='*60}")
    print(f"\nPróximo paso: subir el parquet al Codespace.")
    print(f"  Opción A — GitHub CLI:")
    print(f"    gh codespace cp {OUT_FILE} \\")
    print(f"      remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet")
    print(f"\n  Opción B — VS Code:")
    print(f"    Arrastra {OUT_FILE} al explorador del Codespace en el panel lateral.")
    print(f"\n  Opción C — scp (si tienes SSH al codespace configurado):")
    print(f"    scp {OUT_FILE} <codespace-ssh>:/workspaces/trading-lab/data/dukascopy/")

    mt5.shutdown()
    print("\n✓ MT5 desconectado.")


if __name__ == "__main__":
    main()
