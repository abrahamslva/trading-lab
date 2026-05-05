"""
mt5/mt5_connector.py
--------------------
Python ↔ MetaTrader 5 connector.

Requires the ``MetaTrader5`` package (Windows only):
    pip install MetaTrader5

Credentials are read from configs/mt5.yaml; environment variables
MT5_LOGIN / MT5_PASSWORD / MT5_SERVER override yaml values.

Usage
-----
    from mt5.mt5_connector import MT5Connector

    with MT5Connector() as mt5c:
        bar  = mt5c.get_latest_bar("XAUUSD")
        mt5c.place_market_order("XAUUSD", "buy", lots=0.01)
        mt5c.close_position(ticket=123456)
        positions = mt5c.get_positions("XAUUSD")
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).parent.parent / "configs" / "mt5.yaml"

# Lazy import so the module can be imported on Linux (for IDE / CI purposes)
try:
    import MetaTrader5 as _mt5  # type: ignore[import]
    _MT5_AVAILABLE = True
except ImportError:
    _mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _load_cfg(path: Path = _CFG_PATH) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class MT5Connector:
    """
    Thin wrapper around the MetaTrader5 Python package.

    Parameters
    ----------
    config_path : Path, optional
        Path to configs/mt5.yaml.  Defaults to the repo-level config.
    """

    def __init__(self, config_path: Path = _CFG_PATH) -> None:
        if not _MT5_AVAILABLE:
            raise RuntimeError(
                "MetaTrader5 package is not installed or not available on this OS.\n"
                "Install it on Windows with:  pip install MetaTrader5"
            )
        cfg = _load_cfg(config_path)
        conn = cfg["connection"]
        trd  = cfg["trading"]
        sym  = cfg["symbol"]

        # Credentials: env vars take precedence
        self._server   = os.environ.get("MT5_SERVER",   conn.get("server",   ""))
        self._login    = int(os.environ.get("MT5_LOGIN", str(conn.get("login", 0))))
        self._password = os.environ.get("MT5_PASSWORD", conn.get("password", ""))

        self._terminal_path = conn.get("terminal_path", "")
        self._timeout       = int(conn.get("timeout",   10000))

        self._symbol      = sym["forex"] if sym["active"] == "forex" else sym["futures"]
        self._magic       = int(trd.get("magic_number", 20240101))
        self._deviation   = int(trd.get("deviation",   10))
        self._risk_pct    = float(trd.get("risk_percent", 1.0))
        self._sl_points   = int(trd.get("sl_points",  0))
        self._tp_points   = int(trd.get("tp_points",  0))

        self._connected = False

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MT5Connector":
        self.initialize()
        return self

    def __exit__(self, *_) -> None:
        self.shutdown()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Start MT5, connect and authenticate."""
        kwargs: dict = {"timeout": self._timeout}
        if self._terminal_path:
            kwargs["path"] = self._terminal_path

        ok = _mt5.initialize(**kwargs)
        if not ok:
            err = _mt5.last_error()
            raise ConnectionError(f"MT5 initialize() failed: {err}")

        if self._login and self._password and self._server:
            ok = _mt5.login(
                login=self._login,
                password=self._password,
                server=self._server,
            )
            if not ok:
                err = _mt5.last_error()
                _mt5.shutdown()
                raise ConnectionError(f"MT5 login() failed: {err}")
            logger.info("MT5 logged in: account=%d  server=%s", self._login, self._server)
        else:
            logger.info("MT5 initialized (no login credentials provided — using active session).")

        self._connected = True

    def shutdown(self) -> None:
        """Disconnect from MT5."""
        if self._connected:
            _mt5.shutdown()
            self._connected = False
            logger.info("MT5 shutdown.")

    def _require_connection(self) -> None:
        if not self._connected:
            raise RuntimeError("MT5Connector is not connected. Call initialize() first.")

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def get_latest_bar(
        self,
        symbol: Optional[str] = None,
        timeframe: int = None,
        count: int = 1,
    ) -> list[dict]:
        """
        Fetch the most recent OHLCV bar(s).

        Parameters
        ----------
        symbol : str, optional
            Defaults to the symbol from config.
        timeframe : int
            MT5 timeframe constant, e.g. ``_mt5.TIMEFRAME_D1``.
            Defaults to TIMEFRAME_D1.
        count : int
            Number of bars to return.

        Returns
        -------
        list of dicts with keys: time, open, high, low, close, tick_volume, spread
        """
        self._require_connection()
        sym = symbol or self._symbol
        tf  = timeframe if timeframe is not None else _mt5.TIMEFRAME_D1
        rates = _mt5.copy_rates_from_pos(sym, tf, 0, count)
        if rates is None:
            err = _mt5.last_error()
            raise RuntimeError(f"copy_rates_from_pos failed for {sym}: {err}")
        return [dict(r) for r in rates]

    # ------------------------------------------------------------------
    # Account / positions
    # ------------------------------------------------------------------

    def get_account_info(self) -> dict:
        """Return account info as a plain dict."""
        self._require_connection()
        info = _mt5.account_info()
        if info is None:
            raise RuntimeError(f"account_info() failed: {_mt5.last_error()}")
        return info._asdict()

    def get_positions(self, symbol: Optional[str] = None) -> list[dict]:
        """
        Return open positions for *symbol* (or all positions if None).

        Returns
        -------
        list of dicts with all TradePosition fields.
        """
        self._require_connection()
        sym = symbol or self._symbol
        positions = _mt5.positions_get(symbol=sym)
        if positions is None:
            return []
        return [dict(p._asdict()) for p in positions]

    # ------------------------------------------------------------------
    # Order helpers
    # ------------------------------------------------------------------

    def _compute_lots(self, symbol: str) -> float:
        """
        Compute lot size based on risk_percent of account balance.
        Uses a fixed fractional approximation; a full implementation
        would use ATR or SL distance.
        """
        info = _mt5.account_info()
        if info is None:
            return 0.01
        balance    = info.balance
        sym_info   = _mt5.symbol_info(symbol)
        if sym_info is None:
            return 0.01
        tick_value = sym_info.trade_tick_value
        tick_size  = sym_info.trade_tick_size
        min_lot    = sym_info.volume_min
        lot_step   = sym_info.volume_step

        # Simple: risk as % of balance, assume SL=50 ticks
        sl_ticks   = max(self._sl_points, 50)
        risk_cash  = balance * self._risk_pct / 100.0
        lots       = risk_cash / (sl_ticks * tick_value / tick_size) if tick_value else min_lot

        # Round to lot_step precision
        lots = max(min_lot, round(round(lots / lot_step) * lot_step, 8))
        return lots

    def _build_request(
        self,
        symbol: str,
        order_type: int,
        lots: float,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "GoldAlgo",
    ) -> dict:
        req = {
            "action":       _mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       lots,
            "type":         order_type,
            "price":        price,
            "deviation":    self._deviation,
            "magic":        self._magic,
            "comment":      comment,
            "type_time":    _mt5.ORDER_TIME_GTC,
            "type_filling": _mt5.ORDER_FILLING_IOC,
        }
        if sl:
            req["sl"] = sl
        if tp:
            req["tp"] = tp
        return req

    def place_market_order(
        self,
        symbol: Optional[str] = None,
        direction: str = "buy",
        lots: Optional[float] = None,
        comment: str = "GoldAlgo",
    ) -> dict:
        """
        Place a market buy or sell order.

        Parameters
        ----------
        symbol : str, optional
            Defaults to symbol from config.
        direction : "buy" | "sell"
        lots : float, optional
            Position size.  If None, computed from risk_percent.
        comment : str

        Returns
        -------
        dict with order result fields.
        """
        self._require_connection()
        sym = symbol or self._symbol

        dir_lower = direction.lower()
        if dir_lower not in ("buy", "sell"):
            raise ValueError(f"direction must be 'buy' or 'sell', got {direction!r}")

        tick = _mt5.symbol_info_tick(sym)
        if tick is None:
            raise RuntimeError(f"symbol_info_tick() failed for {sym}: {_mt5.last_error()}")

        if dir_lower == "buy":
            otype = _mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl    = (price - self._sl_points * _mt5.symbol_info(sym).point) if self._sl_points else 0.0
            tp    = (price + self._tp_points * _mt5.symbol_info(sym).point) if self._tp_points else 0.0
        else:
            otype = _mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl    = (price + self._sl_points * _mt5.symbol_info(sym).point) if self._sl_points else 0.0
            tp    = (price - self._tp_points * _mt5.symbol_info(sym).point) if self._tp_points else 0.0

        volume = lots if lots is not None else self._compute_lots(sym)
        req    = self._build_request(sym, otype, volume, price, sl, tp, comment)

        result = _mt5.order_send(req)
        if result is None:
            raise RuntimeError(f"order_send() returned None: {_mt5.last_error()}")

        ret = result._asdict()
        if result.retcode != _mt5.TRADE_RETCODE_DONE:
            logger.warning("Order not executed: retcode=%d  comment=%s", result.retcode, result.comment)
        else:
            logger.info(
                "Order sent: %s %s %.2f lots @ %.5f  ticket=%d",
                dir_lower, sym, volume, price, result.order,
            )
        return ret

    def close_position(
        self,
        ticket: int,
        comment: str = "GoldAlgo-close",
    ) -> dict:
        """
        Close an open position by ticket number.

        Parameters
        ----------
        ticket : int
            Position ticket as returned by ``get_positions()``.
        comment : str

        Returns
        -------
        dict with order result fields.
        """
        self._require_connection()
        positions = _mt5.positions_get(ticket=ticket)
        if not positions:
            raise ValueError(f"No open position found with ticket={ticket}")

        pos = positions[0]
        sym = pos.symbol

        tick = _mt5.symbol_info_tick(sym)
        if tick is None:
            raise RuntimeError(f"symbol_info_tick() failed for {sym}: {_mt5.last_error()}")

        # Closing direction is opposite to position type
        if pos.type == _mt5.POSITION_TYPE_BUY:
            otype = _mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            otype = _mt5.ORDER_TYPE_BUY
            price = tick.ask

        req = {
            "action":       _mt5.TRADE_ACTION_DEAL,
            "symbol":       sym,
            "volume":       pos.volume,
            "type":         otype,
            "position":     ticket,
            "price":        price,
            "deviation":    self._deviation,
            "magic":        self._magic,
            "comment":      comment,
            "type_time":    _mt5.ORDER_TIME_GTC,
            "type_filling": _mt5.ORDER_FILLING_IOC,
        }
        result = _mt5.order_send(req)
        if result is None:
            raise RuntimeError(f"order_send() (close) returned None: {_mt5.last_error()}")

        ret = result._asdict()
        if result.retcode != _mt5.TRADE_RETCODE_DONE:
            logger.warning("Close not executed: retcode=%d  comment=%s", result.retcode, result.comment)
        else:
            logger.info("Position closed: ticket=%d  sym=%s", ticket, sym)
        return ret
