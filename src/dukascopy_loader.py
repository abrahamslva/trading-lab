"""
src/dukascopy_loader.py
-----------------------
Dukascopy XAUUSD data loader — descarga ticks bi5 del CDN público de Dukascopy
(sin credenciales, sin API key — datos gratuitos hasta ~20 años de historia).

CDN público: https://datafeed.dukascopy.com/datafeed/{instrument}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5
Formato bi5: LZMA-compressed, registros de 20 bytes cada uno:
  [ms_offset: uint32, ask*1e5: uint32, bid*1e5: uint32, ask_vol: float32, bid_vol: float32]

Uso rápido:
    from src.dukascopy_loader import download_xauusd_m15
    df = download_xauusd_m15("2020-01-01", "2025-01-01", cache_dir="data/dukascopy")
    # df → DataFrame OHLCV en M15, columnas: Open High Low Close Volume (tick vol)
"""

from __future__ import annotations

import io
import logging
import lzma
import os
import struct
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import urllib.request

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes Dukascopy
# ---------------------------------------------------------------------------

# XAUUSD en Dukascopy se llama "XAUUSD"
_CDN = "https://datafeed.dukascopy.com/datafeed/{instrument}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

# XAUUSD: precio almacenado como int(precio * 1000)
# Ejemplo: precio 2054.00 → almacenado como 2054000 → dividir por 1000
# (EURUSD usaría 1e5, pero XAUUSD usa 1e3 por el rango de precio)
_PRICE_DIV = 1000.0


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseLoader(ABC):
    @abstractmethod
    def load(self, start: str, end: Optional[str] = None) -> pd.DataFrame:
        """Retorna DataFrame OHLCV con DatetimeIndex UTC."""


# ---------------------------------------------------------------------------
# Utilidad de decodificación bi5
# ---------------------------------------------------------------------------

def _decode_bi5(data: bytes, day_start_ms: int) -> pd.DataFrame:
    """
    Decodifica un archivo bi5 de Dukascopy.
    Formato: registros de 20 bytes (big-endian):
      uint32  ms_offset  — milisegundos desde inicio de la hora
      uint32  ask * 1e5
      uint32  bid * 1e5
      float32 ask_volume
      float32 bid_volume
    """
    if not data:
        return pd.DataFrame()

    try:
        raw = lzma.decompress(data)
    except lzma.LZMAError:
        return pd.DataFrame()

    n = len(raw) // 20
    if n == 0:
        return pd.DataFrame()

    records = np.frombuffer(raw[:n * 20], dtype=">u4,>u4,>u4,>f4,>f4")
    ms_offset = records["f0"].astype(np.int64)
    ask       = records["f1"].astype(np.float64) / _PRICE_DIV
    bid       = records["f2"].astype(np.float64) / _PRICE_DIV
    ask_vol   = records["f3"].astype(np.float64)
    bid_vol   = records["f4"].astype(np.float64)

    timestamps = pd.to_datetime(day_start_ms + ms_offset, unit="ms", utc=True)
    mid = (ask + bid) / 2.0
    volume = ask_vol + bid_vol

    return pd.DataFrame({
        "timestamp": timestamps,
        "price":     mid,
        "volume":    volume,
    })


def _fetch_bi5(instrument: str, dt: datetime,
               cache_dir: Optional[Path] = None,
               retries: int = 2,
               save_bi5: bool = False) -> bytes:
    """
    Descarga un archivo bi5 (1 hora de ticks) del CDN de Dukascopy.
    Guarda en caché local solo si save_bi5=True y cache_dir está definido.
    """
    url = _CDN.format(
        instrument=instrument,
        year=dt.year,
        month=dt.month - 1,   # Dukascopy usa mes 0-based (Ene=00)
        day=dt.day,
        hour=dt.hour,
    )

    # Caché en disco (solo si save_bi5=True)
    if cache_dir is not None and save_bi5:
        cache_path = cache_dir / f"{instrument}_{dt.strftime('%Y%m%d_%H')}.bi5"
        if cache_path.exists():
            return cache_path.read_bytes()

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer":    "https://www.dukascopy.com/",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if cache_dir is not None and save_bi5:
                cache_path = cache_dir / f"{instrument}_{dt.strftime('%Y%m%d_%H')}.bi5"
                cache_path.write_bytes(data)
            return data
        except Exception:
            if attempt < retries:
                time.sleep(1.0)
    return b""


# ---------------------------------------------------------------------------
# Función principal de descarga — XAUUSD M15
# ---------------------------------------------------------------------------

def download_xauusd_m15(
    start: str,
    end: str,
    timeframe: str = "15min",
    instrument: str = "XAUUSD",
    cache_dir: str = "data/dukascopy",
    max_workers: int = 4,
    show_progress: bool = True,
    save_bi5: bool = False,
    save_parquet: bool = True,
) -> pd.DataFrame:
    """
    Descarga datos XAUUSD del CDN público de Dukascopy y los remuestrea al timeframe pedido.

    Parámetros
    ----------
    start        : "YYYY-MM-DD"  fecha inicio (UTC)
    end          : "YYYY-MM-DD"  fecha fin    (UTC)
    timeframe    : regla pandas  ("15min", "30min", "1h", "4h", …)
    instrument   : nombre en Dukascopy
    cache_dir    : carpeta para guardar el parquet final (y bi5 si save_bi5=True)
    max_workers  : threads paralelos de descarga
    show_progress: imprime progreso
    save_bi5     : si True guarda cada hora como .bi5 en cache_dir (mucho espacio)
    save_parquet : si True guarda el resultado OHLCV como .parquet (recomendado)

    Retorna
    -------
    pd.DataFrame con columnas [Open, High, Low, Close, Volume] e índice UTC.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cache_path = Path(cache_dir) if cache_dir else None
    if cache_path:
        cache_path.mkdir(parents=True, exist_ok=True)

    # Si ya existe el parquet, cargarlo directamente
    if cache_path and save_parquet:
        parquet_file = cache_path / f"{instrument}_{timeframe}_{start}_{end}.parquet"
        if parquet_file.exists():
            if show_progress:
                print(f"  Cargando desde parquet: {parquet_file}")
            return pd.read_parquet(parquet_file)

    start_dt = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt   = datetime.strptime(end,   "%Y-%m-%d").replace(tzinfo=timezone.utc)

    # Generar lista de horas a descargar (lun-vie, 00-23 UTC)
    hours = []
    cur = start_dt
    while cur < end_dt:
        # Dukascopy no tiene datos de sábado 21:00+ ni domingo ~00:00-21:00
        if cur.weekday() < 5 or (cur.weekday() == 6 and cur.hour >= 21):
            hours.append(cur)
        cur += timedelta(hours=1)

    total = len(hours)
    if show_progress:
        print(f"  Dukascopy XAUUSD: descargando {total} horas ({start} → {end})...")

    all_ticks = []
    done = 0
    failed = 0

    def _worker(dt: datetime):
        day_start_ms = int(dt.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
        raw = _fetch_bi5(instrument, dt, cache_path, save_bi5=save_bi5)
        return _decode_bi5(raw, day_start_ms)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_worker, h): h for h in hours}
        for fut in as_completed(futures):
            done += 1
            df_h = fut.result()
            if df_h is not None and not df_h.empty:
                all_ticks.append(df_h)
            else:
                failed += 1
            if show_progress and done % 500 == 0:
                pct = done / total * 100
                print(f"    {done}/{total} ({pct:.0f}%) — {len(all_ticks)} horas con datos")

    if not all_ticks:
        raise RuntimeError(
            f"No se descargaron datos de Dukascopy. "
            f"Verifica conectividad y que {instrument} sea válido."
        )

    ticks = pd.concat(all_ticks, ignore_index=True).sort_values("timestamp")
    ticks.set_index("timestamp", inplace=True)

    # Remuestrear a timeframe solicitado
    ohlcv = ticks["price"].resample(timeframe).ohlc()
    ohlcv.columns = ["Open", "High", "Low", "Close"]
    ohlcv["Volume"] = ticks["volume"].resample(timeframe).sum()
    ohlcv = ohlcv.dropna(subset=["Open"])
    ohlcv = ohlcv[ohlcv["Volume"] > 0]

    if show_progress:
        print(f"  OK: {len(ohlcv)} barras {timeframe} "
              f"desde {ohlcv.index[0]} hasta {ohlcv.index[-1]}")
        print(f"  (Horas fallidas/sin datos: {failed}/{total})")

    # Guardar parquet para recargas futuras instantáneas
    if cache_path and save_parquet:
        parquet_file = cache_path / f"{instrument}_{timeframe}_{start}_{end}.parquet"
        ohlcv.to_parquet(parquet_file)
        size_mb = parquet_file.stat().st_size / 1024 / 1024
        if show_progress:
            print(f"  Parquet guardado: {parquet_file} ({size_mb:.1f} MB)")

    return ohlcv


# ---------------------------------------------------------------------------
# DukascopyLoader — compatible con la interfaz anterior
# ---------------------------------------------------------------------------

class DukascopyLoader(BaseLoader):
    """
    Loader OHLCV de Dukascopy usando el CDN público (sin credenciales).

    Parámetros
    ----------
    instrument    : str   — nombre en Dukascopy, p.ej. "XAUUSD"
    cfg           : dict  — configuración (opcional, compatible con data.yaml)
    base_timeframe: str   — regla pandas p.ej. "15min", "1h"
    cache_dir     : str   — carpeta caché local
    """

    def __init__(
        self,
        instrument: str = "XAUUSD",
        cfg: dict = None,
        base_timeframe: str = "15min",
        cache_dir: str = "data/dukascopy",
    ) -> None:
        self.instrument = instrument
        self.cfg = cfg or {}
        self.base_timeframe = base_timeframe
        self.cache_dir = cache_dir

    def load(self, start: str, end: Optional[str] = None) -> pd.DataFrame:
        end_dt = end or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return download_xauusd_m15(
            start=start,
            end=end_dt,
            timeframe=self.base_timeframe,
            instrument=self.instrument,
            cache_dir=self.cache_dir,
        )

