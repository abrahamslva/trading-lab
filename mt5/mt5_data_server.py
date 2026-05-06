"""
mt5/mt5_data_server.py  —  EJECUTAR EN WINDOWS con MetaTrader 5 abierto
=========================================================================
Servidor HTTP que expone datos OHLCV de MT5 para que el contenedor Linux
los consuma en tiempo real sin descargar archivos.

REQUISITOS (Windows):
    pip install MetaTrader5 pandas pyarrow

USO:
    python mt5\\mt5_data_server.py
    python mt5\\mt5_data_server.py --port 8765 --host 0.0.0.0

DESDE LINUX (Codespace):
    export MT5_HOST=<IP-de-tu-PC-Windows>
    python src/backtest_volume_fusion.py
    # o directamente:
    python -c "from src.mt5_data_client import MT5DataClient; ..."

ENDPOINTS:
    GET /ping                        → {"status":"ok","terminal":"..."}
    GET /timeframes                  → lista de TFs disponibles
    GET /data?symbol=XAUUSD&tf=15min&years=10  → parquet bytes
    GET /data?symbol=XAUUSD&tf=1h&from=2016-01-01&to=2026-01-01
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pandas as pd

# ── MetaTrader5 ────────────────────────────────────────────────────────────
try:
    import MetaTrader5 as mt5
    _MT5_OK = mt5.initialize()
    if not _MT5_OK:
        print(f"ERROR: No se pudo inicializar MT5: {mt5.last_error()}")
        print("  Asegúrate de que MetaTrader 5 está abierto y logueado.")
        sys.exit(1)
    info = mt5.terminal_info()
    print(f"MT5 conectado: {info.name}  build={info.build}")
except ImportError:
    print("ERROR: MetaTrader5 no instalado.  pip install MetaTrader5")
    sys.exit(1)

# ── Mapa de timeframes ─────────────────────────────────────────────────────
TF_MAP: dict[str, int] = {
    "1min":  mt5.TIMEFRAME_M1,
    "5min":  mt5.TIMEFRAME_M5,
    "15min": mt5.TIMEFRAME_M15,
    "M15":   mt5.TIMEFRAME_M15,
    "30min": mt5.TIMEFRAME_M30,
    "M30":   mt5.TIMEFRAME_M30,
    "1h":    mt5.TIMEFRAME_H1,
    "H1":    mt5.TIMEFRAME_H1,
    "2h":    mt5.TIMEFRAME_H2,
    "H2":    mt5.TIMEFRAME_H2,
    "3h":    mt5.TIMEFRAME_H3,
    "H3":    mt5.TIMEFRAME_H3,
    "4h":    mt5.TIMEFRAME_H4,
    "H4":    mt5.TIMEFRAME_H4,
    "1d":    mt5.TIMEFRAME_D1,
    "1D":    mt5.TIMEFRAME_D1,
    "D1":    mt5.TIMEFRAME_D1,
}

AVAILABLE_TFS = ["15min", "30min", "1h", "2h", "3h", "4h", "1d"]


def _fetch_ohlcv(symbol: str, tf_str: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Descarga OHLCV de MT5 y retorna DataFrame con columnas estándar."""
    mt5_tf = TF_MAP.get(tf_str)
    if mt5_tf is None:
        raise ValueError(f"Timeframe '{tf_str}' no reconocido. Válidos: {list(TF_MAP)}")

    rates = mt5.copy_rates_range(symbol, mt5_tf, start, end)
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        raise RuntimeError(f"MT5 no retornó datos para {symbol} {tf_str}: {err}")

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
    return df.sort_index()


# ── Handler HTTP ───────────────────────────────────────────────────────────
class MT5Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # silenciar log por defecto
        print(f"  [{self.address_string()}] {fmt % args}")

    def _send_json(self, data: dict, code: int = 200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_parquet(self, df: pd.DataFrame):
        buf = io.BytesIO()
        df.to_parquet(buf, engine="pyarrow")
        body = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)

        # ── /ping ──────────────────────────────────────────────────
        if parsed.path == "/ping":
            info = mt5.terminal_info()
            self._send_json({
                "status":   "ok",
                "terminal": info.name,
                "build":    info.build,
                "connected": info.connected,
            })

        # ── /timeframes ────────────────────────────────────────────
        elif parsed.path == "/timeframes":
            self._send_json({"timeframes": AVAILABLE_TFS})

        # ── /data ──────────────────────────────────────────────────
        elif parsed.path == "/data":
            try:
                symbol = qs.get("symbol", ["XAUUSD"])[0]
                tf_str = qs.get("tf", ["15min"])[0]

                # Rango de fechas
                if "from" in qs and "to" in qs:
                    start = datetime.strptime(qs["from"][0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    end   = datetime.strptime(qs["to"][0],   "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    years = int(qs.get("years", ["10"])[0])
                    end   = datetime.now(tz=timezone.utc)
                    start = end - timedelta(days=365 * years)

                print(f"  → {symbol} {tf_str}  {start.date()} → {end.date()}")
                df = _fetch_ohlcv(symbol, tf_str, start, end)
                print(f"    {len(df)} barras  precio={df.Close.mean():.2f}")
                self._send_parquet(df)

            except Exception as exc:
                traceback.print_exc()
                self._send_json({"error": str(exc)}, code=500)

        else:
            self._send_json({"error": "endpoint no encontrado"}, code=404)


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="MT5 Data Server")
    ap.add_argument("--host", default="0.0.0.0", help="Interfaz de red (default: 0.0.0.0)")
    ap.add_argument("--port", type=int, default=8765, help="Puerto (default: 8765)")
    args = ap.parse_args()

    print(f"\n{'='*60}")
    print(f"  MT5 Data Server — escuchando en {args.host}:{args.port}")
    print(f"  Desde Linux: export MT5_HOST=<tu-IP-Windows>")
    print(f"  Ctrl+C para detener")
    print(f"{'='*60}\n")

    server = HTTPServer((args.host, args.port), MT5Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        mt5.shutdown()


if __name__ == "__main__":
    main()
