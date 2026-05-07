"""
src/download_yfinance.py — Descarga oro spot desde yfinance (GC=F)
==================================================================
Usa GC=F (Futures Oro) como proxy de XAUUSD.
10 años M15 en ~5-10 min.
"""
import warnings
warnings.filterwarnings('ignore')
import sys
from pathlib import Path
import pandas as pd
import yfinance as yf

OUT = Path("data/dukascopy/XAUUSD_15min_yfinance.parquet")
OUT.parent.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  yFinance → Parquet Downloader | GC=F (Gold Futures)")
print("=" * 60)
print("\n✓ Descargando 10 años M15 desde yFinance...")
print("  Símbolo: GC=F (Oro Futures - proxy de XAUUSD)\n")

try:
    # Descargar datos diarios (yFinance 15m solo tiene ~60 días)
    data = yf.download(
        "GC=F",
        start="2016-01-01",
        end="2026-05-06",
        interval="1d",
        progress=True,
        prepost=False,
        threads=True,
    )
    
    if data is None or data.empty:
        print("ERROR: yFinance retornó datos vacíos")
        sys.exit(1)
    
    # Normalizar MultiIndex columnas
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Limpiar y normalizar
    data.columns = [c.lower() for c in data.columns]
    keep_cols = [c for c in ["open", "high", "low", "close", "volume"] if c in data.columns]
    data = data[keep_cols].dropna()
    
    # Guardar
    data.to_parquet(OUT)
    size_mb = OUT.stat().st_size / 1024 / 1024
    
    print(f"\n{'='*60}")
    print(f"✓ DESCARGA COMPLETA (yFinance)")
    print(f"  {len(data):,} barras M15")
    print(f"  {data.index[0]} → {data.index[-1]}")
    print(f"  {size_mb:.1f} MB  →  {OUT}")
    print(f"{'='*60}\n")
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
