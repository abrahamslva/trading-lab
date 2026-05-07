"""
mt5/import_csv.py — Convierte CSV exportado desde MT5 → parquet para backtesting
==================================================================================
FUNCIONA EN WINDOWS Y LINUX/CODESPACE (no requiere MetaTrader5 instalado).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 1 — Exportar CSV desde MT5 (en tu PC Windows)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Abre MetaTrader 5
  2. Menú: Herramientas → Centro de Historia (History Center)
     [atajo: Ctrl+H]
  3. En el panel izquierdo: XAUUSD → M15
  4. Clic derecho → "Exportar barras" (Export Bars)
  5. Guardar como: XAUUSD_M15.csv  (en cualquier carpeta)

  MT5 acepta estos formatos de separador — todos son compatibles:
    Tab, coma o punto y coma

  Formato típico del CSV exportado:
    <DATE>    <TIME>    <OPEN>   <HIGH>   <LOW>    <CLOSE>  <TICKVOL> <VOL> <SPREAD>
    2016.01.04 02:00    1075.03  1076.20  1074.90  1075.53  120       0     0

  También compatible con exportación desde Charts:
    Clic derecho en gráfico XAUUSD M15 → Save As Picture... → no
    En cambio: File → Open Data Folder → history\ → <broker>\ → XAUUSD15.hcc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 2 — Ejecutar este script
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Opción A — Pasar el CSV como argumento:
    python mt5/import_csv.py XAUUSD_M15.csv

  Opción B — El script busca automáticamente cualquier CSV de XAUUSD:
    python mt5/import_csv.py

  El parquet resultante se guarda en:
    data/dukascopy/XAUUSD_15min_mt5.parquet

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PASO 3 — Subir al Codespace (solo si corriste en Windows)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Opción A — GitHub CLI (recomendado):
    gh codespace cp data\\dukascopy\\XAUUSD_15min_mt5.parquet ^
      remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet

  Opción B — VS Code:
    Arrastra el archivo al explorador del Codespace (panel lateral)

  Opción C — También puedes subir el CSV directamente al Codespace
    y correr este script allá (funciona igual en Linux).
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
import re

# ── Dependencias ──────────────────────────────────────────────────────────────
try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas no instalado.  pip install pandas pyarrow")
    sys.exit(1)

# ── Configuración ─────────────────────────────────────────────────────────────
OUT_DIR  = Path("data") / "dukascopy"
OUT_FILE = OUT_DIR / "XAUUSD_15min_mt5.parquet"

# Formatos de fecha que MT5 puede exportar
DATE_FORMATS = [
    "%Y.%m.%d %H:%M",      # 2016.01.04 02:00  (más común)
    "%Y-%m-%d %H:%M:%S",   # 2016-01-04 02:00:00
    "%Y-%m-%d %H:%M",      # 2016-01-04 02:00
    "%d/%m/%Y %H:%M",      # 04/01/2016 02:00
    "%Y.%m.%d %H:%M:%S",   # 2016.01.04 02:00:00
]

# Variaciones de nombre de columna que MT5 puede usar
COL_ALIASES = {
    "open":   ["open",   "<open>",   "OPEN",   "Open"],
    "high":   ["high",   "<high>",   "HIGH",   "High"],
    "low":    ["low",    "<low>",    "LOW",    "Low"],
    "close":  ["close",  "<close>",  "CLOSE",  "Close"],
    "volume": ["tickvol","<tickvol>","TICKVOL","tick_volume",
               "vol",    "<vol>",    "VOL",    "Volume","volume"],
    "date":   ["date",   "<date>",   "DATE",   "Date"],
    "time":   ["time",   "<time>",   "TIME",   "Time"],
}
# ─────────────────────────────────────────────────────────────────────────────


def find_csv(hint: str | None = None) -> Path:
    """Encuentra el CSV a usar: argumento, en directorio actual, o en data/."""
    if hint:
        p = Path(hint)
        if p.exists():
            return p
        raise FileNotFoundError(f"No se encontró: {hint}")

    # Buscar automáticamente
    search_dirs = [Path("."), Path("data"), Path("data/dukascopy"), Path("mt5")]
    patterns    = ["*XAUUSD*M15*.csv", "*XAUUSD*.csv", "*gold*.csv", "*GOLD*.csv",
                   "*xauusd*.csv", "*.csv"]
    for d in search_dirs:
        if not d.exists():
            continue
        for pat in patterns:
            matches = sorted(d.glob(pat))
            if matches:
                print(f"  CSV encontrado automáticamente: {matches[0]}")
                return matches[0]

    raise FileNotFoundError(
        "No se encontró ningún CSV de MT5.\n"
        "  Pasa la ruta como argumento:  python mt5/import_csv.py XAUUSD_M15.csv\n"
        "  O copia el CSV a la carpeta raíz del repo."
    )


def detect_separator(raw_text: str) -> str:
    """Detecta el separador del CSV (tab, coma, punto y coma)."""
    first_line = raw_text.split("\n")[0]
    counts = {"\t": first_line.count("\t"),
              ",":  first_line.count(","),
              ";":  first_line.count(";")}
    return max(counts, key=counts.get)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Mapea los nombres de columna de MT5 a los estándar (open/high/low/close/volume)."""
    # Limpiar nombres: quitar espacios y < >
    df.columns = [re.sub(r"[<>\s]", "", c).lower() for c in df.columns]

    rename = {}
    for std_name, aliases in COL_ALIASES.items():
        aliases_lower = [a.lower().replace("<","").replace(">","").strip() for a in aliases]
        for col in df.columns:
            if col in aliases_lower and col != std_name:
                rename[col] = std_name
                break

    if rename:
        df.rename(columns=rename, inplace=True)

    return df


def parse_datetime(df: pd.DataFrame) -> pd.DatetimeIndex:
    """
    Construye el índice datetime desde columnas date+time de MT5,
    probando todos los formatos conocidos.
    """
    # Caso 1: columna única ya parseada (poco común)
    if "datetime" in df.columns:
        return pd.to_datetime(df["datetime"], utc=True)

    # Caso 2: columnas separadas date y time
    if "date" in df.columns and "time" in df.columns:
        dt_str = df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip()
    elif "date" in df.columns:
        dt_str = df["date"].astype(str).str.strip()
    else:
        # Intentar con la primera columna
        dt_str = df.iloc[:, 0].astype(str).str.strip()
        if df.shape[1] > 1:
            # Si la segunda columna parece hora, concatenar
            second = df.iloc[:, 1].astype(str).str.strip()
            if second.str.match(r"^\d{1,2}:\d{2}").any():
                dt_str = dt_str + " " + second

    # Probar formatos
    for fmt in DATE_FORMATS:
        try:
            idx = pd.to_datetime(dt_str, format=fmt, utc=True)
            print(f"  Formato de fecha detectado: {fmt!r}")
            return idx
        except (ValueError, TypeError):
            continue

    # Fallback: pandas infiere
    try:
        idx = pd.to_datetime(dt_str, utc=True, infer_datetime_format=True)
        print("  Formato de fecha: inferido automáticamente")
        return idx
    except Exception as e:
        raise ValueError(
            f"No se pudo parsear la columna de fecha.\n"
            f"  Primeras filas:\n{dt_str.head()}\n"
            f"  Error: {e}\n"
            f"  Formatos soportados: {DATE_FORMATS}"
        )


def load_csv(csv_path: Path) -> pd.DataFrame:
    """Carga el CSV de MT5 y normaliza columnas + índice."""
    print(f"  Leyendo: {csv_path}  ({csv_path.stat().st_size / 1024:.0f} KB)")
    raw = csv_path.read_text(encoding="utf-8", errors="replace")
    sep = detect_separator(raw)
    sep_name = {"\\t": "tab", "\t": "tab", ",": "coma", ";": "punto y coma"}.get(sep, repr(sep))
    print(f"  Separador detectado: {sep_name}")

    # Saltar encabezados de comentario que MT5 a veces incluye
    skip = sum(1 for line in raw.split("\n") if line.startswith("#"))
    df = pd.read_csv(csv_path, sep=sep, skiprows=skip, encoding="utf-8",
                     on_bad_lines="skip")

    print(f"  Filas cargadas: {len(df):,} | Columnas: {list(df.columns)}")
    df = normalize_columns(df)
    df.index = parse_datetime(df)
    df.index.name = "time"

    # Seleccionar solo columnas OHLCV estándar
    required = ["open", "high", "low", "close"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Columnas faltantes: {missing}\n"
            f"  Columnas disponibles: {list(df.columns)}\n"
            f"  Revisa que exportaste OHLCV desde MT5."
        )

    # Volume es opcional (algunos brokers no lo exportan)
    if "volume" not in df.columns:
        print("  ⚠ Sin columna volume — se asignará 1 a todas las barras.")
        df["volume"] = 1.0

    df = df[["open","high","low","close","volume"]].copy()
    df = df.apply(pd.to_numeric, errors="coerce")
    df.dropna(subset=["open","high","low","close"], inplace=True)
    df = df[df["close"] > 0]
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep="last")]

    return df


def validate(df: pd.DataFrame) -> None:
    """Chequeos básicos de calidad de datos."""
    n = len(df)
    if n < 1000:
        print(f"  ⚠ Solo {n} barras — confirma que exportaste M15 y no D1.")
    if df.index.tz is None:
        print("  ⚠ Sin timezone — asumiendo UTC.")
    if not df.index.is_monotonic_increasing:
        print("  ⚠ Timestamps no ordenados — se ordenarán.")
        df.sort_index(inplace=True)

    null_pct = df.isnull().mean().max() * 100
    if null_pct > 5:
        print(f"  ⚠ {null_pct:.1f}% de valores nulos — puede haber problemas de formato.")

    span_years = (df.index[-1] - df.index[0]).days / 365
    print(f"  ✓ Rango: {df.index[0].date()} → {df.index[-1].date()} "
          f"({span_years:.1f} años)")

    # Precio medio razonable para XAUUSD (1000–4000 USD)
    mid = df["close"].median()
    if not (500 < mid < 5000):
        print(f"  ⚠ Precio medio={mid:.2f} — ¿Es realmente XAUUSD/GOLD?")
    else:
        print(f"  ✓ Precio medio: {mid:.2f} USD (razonable para XAUUSD)")


def merge_with_existing(df_new: pd.DataFrame) -> pd.DataFrame:
    """Si ya existe parquet, hace merge para no perder datos previos."""
    if OUT_FILE.exists() and OUT_FILE.stat().st_size > 10_000:
        try:
            df_old = pd.read_parquet(OUT_FILE)
            n_old  = len(df_old)
            df_merged = pd.concat([df_old, df_new]).sort_index()
            df_merged  = df_merged[~df_merged.index.duplicated(keep="last")]
            print(f"  ✓ Merge con parquet existente: {n_old:,} + {len(df_new):,} "
                  f"= {len(df_merged):,} barras (deduplicadas)")
            return df_merged
        except Exception as e:
            print(f"  ⚠ No se pudo hacer merge con parquet previo: {e}")
    return df_new


def main():
    print("=" * 60)
    print("  MT5 CSV → Parquet Converter")
    print("=" * 60)

    # Detectar archivo CSV
    hint = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        csv_path = find_csv(hint)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # Cargar y normalizar
    try:
        df = load_csv(csv_path)
    except Exception as e:
        print(f"\nERROR al cargar CSV: {e}")
        sys.exit(1)

    # Validar
    validate(df)

    # Merge con datos previos si existen
    df = merge_with_existing(df)

    # Guardar
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_FILE)
    size_mb = OUT_FILE.stat().st_size / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"✓ CONVERSIÓN COMPLETA")
    print(f"  {len(df):,} barras M15")
    print(f"  {df.index[0]} → {df.index[-1]}")
    print(f"  {size_mb:.2f} MB  →  {OUT_FILE}")
    print(f"{'='*60}")

    if sys.platform == "win32":
        print(f"\nPróximo paso — subir al Codespace:")
        print(f"  gh codespace cp {OUT_FILE} \\")
        print(f"    remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet")
    else:
        print(f"\n✓ En Codespace — el watcher detectará el parquet automáticamente")
        print(f"  y lanzará los 63 backtests (9 versiones × 7 timeframes).")


if __name__ == "__main__":
    main()
