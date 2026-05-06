"""
src/mt5_data_client.py
======================
Cliente que conecta al MT5 Data Server (Windows) y descarga OHLCV
de todos los timeframes en RAM — sin archivos bi5, sin Dukascopy.

Uso directo:
    from src.mt5_data_client import MT5DataClient

    client = MT5DataClient(host="192.168.1.100")   # IP de tu PC Windows
    df_m15 = client.get("XAUUSD", "15min", years=10)
    df_1h  = client.get("XAUUSD", "1h",   years=10)

Configuración automática:
    export MT5_HOST=192.168.1.100   # ← poner IP de tu PC Windows
    export MT5_PORT=8765            # opcional, default 8765

El backtest detecta MT5_HOST y usa este cliente automáticamente.
"""

from __future__ import annotations

import io
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

_DEFAULT_PORT = 8765
_DEFAULT_TIMEOUT = 60          # segundos por request
_CACHE: dict[str, pd.DataFrame] = {}   # caché en RAM para esta sesión


class MT5DataClient:
    """
    Cliente HTTP para el MT5 Data Server (mt5/mt5_data_server.py).

    Parámetros
    ----------
    host    : IP o hostname de la PC Windows con MT5 corriendo
    port    : puerto del servidor (default 8765)
    timeout : segundos de espera por request (default 60)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = _DEFAULT_PORT,
        timeout: int = _DEFAULT_TIMEOUT,
    ):
        host = host or os.environ.get("MT5_HOST", "localhost")
        port = int(os.environ.get("MT5_PORT", port))
        self.base_url = f"http://{host}:{port}"
        self.timeout  = timeout

    # ── Conexión ────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        """Comprueba que el servidor MT5 está activo."""
        try:
            url = f"{self.base_url}/ping"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = r.read()
            import json
            info = json.loads(data)
            return info.get("status") == "ok"
        except Exception:
            return False

    def server_info(self) -> dict:
        """Retorna info del terminal MT5 conectado al servidor."""
        try:
            url = f"{self.base_url}/ping"
            with urllib.request.urlopen(url, timeout=5) as r:
                import json
                return json.loads(r.read())
        except Exception as e:
            return {"error": str(e)}

    # ── Descarga de datos ──────────────────────────────────────────────────

    def get(
        self,
        symbol: str = "XAUUSD",
        timeframe: str = "15min",
        years: int = 10,
        start: Optional[str] = None,
        end: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Descarga OHLCV desde el servidor MT5.

        Parámetros
        ----------
        symbol    : símbolo MT5, ej "XAUUSD"
        timeframe : "15min", "30min", "1h", "2h", "3h", "4h", "1d"
        years     : años de historia (si no se especifica start/end)
        start     : "YYYY-MM-DD"  (alternativa a years)
        end       : "YYYY-MM-DD"  (default: hoy)
        use_cache : reutilizar resultado de esta sesión si ya se descargó

        Retorna
        -------
        pd.DataFrame  columnas: Open, High, Low, Close, Volume
                      índice:   DatetimeIndex UTC
        """
        cache_key = f"{symbol}_{timeframe}_{start or years}_{end}"
        if use_cache and cache_key in _CACHE:
            return _CACHE[cache_key]

        # Construir URL
        if start and end:
            url = (f"{self.base_url}/data"
                   f"?symbol={symbol}&tf={timeframe}&from={start}&to={end}")
        elif start:
            end_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
            url = (f"{self.base_url}/data"
                   f"?symbol={symbol}&tf={timeframe}&from={start}&to={end_str}")
        else:
            url = f"{self.base_url}/data?symbol={symbol}&tf={timeframe}&years={years}"

        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                body = r.read()
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"No se pudo conectar al MT5 Data Server en {self.base_url}\n"
                f"  Verifica que el servidor está corriendo en Windows: "
                f"python mt5/mt5_data_server.py\n"
                f"  Y que MT5_HOST apunta a tu IP Windows: export MT5_HOST=<IP>\n"
                f"  Error: {e}"
            )

        df = pd.read_parquet(io.BytesIO(body))
        if use_cache:
            _CACHE[cache_key] = df
        return df

    # ── Descarga múltiple de timeframes ────────────────────────────────────

    def get_all_timeframes(
        self,
        symbol: str = "XAUUSD",
        years: int = 10,
        timeframes: list[str] = None,
        verbose: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Descarga todos los timeframes en paralelo.

        Retorna dict: {"15min": df, "30min": df, "1h": df, ...}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if timeframes is None:
            timeframes = ["15min", "30min", "1h", "2h", "3h", "4h", "1d"]

        if verbose:
            print(f"Conectando a MT5 Server ({self.base_url})...")
            info = self.server_info()
            if "terminal" in info:
                print(f"  Terminal: {info['terminal']}  build={info.get('build')}")

        results: dict[str, pd.DataFrame] = {}

        def _fetch(tf: str):
            df = self.get(symbol, tf, years=years)
            return tf, df

        with ThreadPoolExecutor(max_workers=len(timeframes)) as pool:
            futures = {pool.submit(_fetch, tf): tf for tf in timeframes}
            for fut in as_completed(futures):
                tf_name = futures[fut]
                try:
                    tf_label, df = fut.result()
                    results[tf_label] = df
                    if verbose:
                        print(f"  ✓ {symbol} {tf_label:6s}: {len(df):,} barras "
                              f"({df.index[0].date()} → {df.index[-1].date()})")
                except Exception as e:
                    if verbose:
                        print(f"  ✗ {symbol} {tf_name}: {e}")

        return results


# ── Helper para uso directo ────────────────────────────────────────────────

def get_mt5_client() -> Optional[MT5DataClient]:
    """
    Retorna un MT5DataClient si MT5_HOST está configurado y el servidor responde.
    Retorna None si no hay servidor disponible.
    """
    host = os.environ.get("MT5_HOST")
    if not host:
        return None
    client = MT5DataClient(host=host)
    if client.ping():
        return client
    return None


# ── Demo / test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    host = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MT5_HOST", "localhost")
    client = MT5DataClient(host=host)

    print(f"Conectando a {client.base_url}...")
    if not client.ping():
        print("ERROR: Servidor no disponible.")
        print(f"  En Windows ejecuta: python mt5/mt5_data_server.py")
        sys.exit(1)

    print("Servidor OK!\n")

    all_tf = client.get_all_timeframes("XAUUSD", years=10, verbose=True)

    print(f"\nResumen:")
    for tf, df in sorted(all_tf.items()):
        print(f"  {tf:6s}: {len(df):,} barras  "
              f"precio_min={df.Low.min():.2f}  precio_max={df.High.max():.2f}")
