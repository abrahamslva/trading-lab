"""
Descargar datos M15 REALES de yFinance (últimos 60 días)
===========================================================
Fuente: yfinance GC=F (GOLD FUTURES)
Período: Últimos 60 días de datos M15 REALES
Verificación: Comparar con comentarios en EA para validar
"""
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf
import pandas as pd
from pathlib import Path
import sys

OUT_DIR = Path("data/dukascopy")
OUT_FILE = OUT_DIR / "XAUUSD_15min_yfinance_real.parquet"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("DESCARGANDO DATOS M15 REALES DE yFINANCE (ÚLTIMOS 60 DÍAS)")
print("="*80)

try:
    # Descargar M15 (últimos 60 días es el máximo que yFinance permite)
    print("\n⏳ Descargando GC=F (Gold Futures) M15...")
    df = yf.download("GC=F", interval="15m", progress=False)
    
    if df.empty:
        print("❌ ERROR: No se descargaron datos")
        sys.exit(1)
    
    # Normalizar columnas (manejar MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    
    # Asegurar que tiene OHLCV
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # Información
    print(f"\n✓ Datos descargados:")
    print(f"  Barras: {len(df):,}")
    print(f"  Período: {df.index[0]} → {df.index[-1]}")
    print(f"  Antigüedad: 0 días (DATOS ACTUALES)")
    print(f"  Rango precio: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Guardar
    df.to_parquet(OUT_FILE)
    size_mb = OUT_FILE.stat().st_size / 1024 / 1024
    print(f"  Archivo: {OUT_FILE.name} ({size_mb:.1f} MB)")
    
    print(f"\n✓ Guardado en: {OUT_FILE}")
    
    # Mostrar sample
    print(f"\nPrimeras 3 barras (más antiguas):")
    print(df.head(3))
    print(f"\nÚltimas 3 barras (MÁS RECIENTES):")
    print(df.tail(3))
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
