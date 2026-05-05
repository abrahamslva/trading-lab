"""
mt5/signal_writer.py
--------------------
File-based bridge: computes MA-cross signals from live MT5 data and
writes them to mt5/bridge/signal.json so GoldEA.mq5 can read them.

Run this script on the same Windows machine as MetaTrader 5.

Usage
-----
    # Uses configs/mt5.yaml and configs/backtest.yaml
    python mt5/signal_writer.py

    # Override parameters
    python mt5/signal_writer.py --fast 10 --slow 30 --timeframe H1

The EA must have SignalMode = MODE_FILE and SignalFile pointing to
the *same* signal.json (absolute path recommended, or copy it into
the MT5 MQL5\\Files\\ folder via a mapped path).
"""

from __future__ import annotations

import argparse
import json
import logging
import signal as _signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Allow running from repo root: python mt5/signal_writer.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.ma_cross import MACrossStrategy  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_MT5_CFG  = Path(__file__).parent.parent / "configs" / "mt5.yaml"
_BT_CFG   = Path(__file__).parent.parent / "configs" / "backtest.yaml"

# MT5 timeframe string → MetaTrader5 constant name
_TF_MAP = {
    "M1":  "TIMEFRAME_M1",
    "M5":  "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "H1":  "TIMEFRAME_H1",
    "H4":  "TIMEFRAME_H4",
    "D1":  "TIMEFRAME_D1",
}

_RUNNING = True


def _handle_sigterm(signum, frame):
    global _RUNNING
    logger.info("Stop signal received. Shutting down.")
    _RUNNING = False


def _load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


def _get_mt5_timeframe(tf_str: str):
    """Map a string like 'H1' to the MetaTrader5 TIMEFRAME_* constant."""
    try:
        import MetaTrader5 as mt5  # noqa: PLC0415
    except ImportError:
        raise RuntimeError("MetaTrader5 package not available.")
    name = _TF_MAP.get(tf_str.upper(), "TIMEFRAME_D1")
    return getattr(mt5, name)


def _fetch_close_series(mt5_conn, symbol: str, tf_str: str, count: int):
    """Fetch a pandas Series of closing prices from MT5."""
    import pandas as pd  # noqa: PLC0415
    bars = mt5_conn.get_latest_bar(symbol=symbol, timeframe=_get_mt5_timeframe(tf_str), count=count)
    if not bars:
        raise RuntimeError(f"No bars returned for {symbol} {tf_str}")
    df = pd.DataFrame(bars)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("time").sort_index()
    return df["close"].rename("Close")


def _write_signal(signal_path: Path, signal: str, fast_ma: float, slow_ma: float) -> None:
    payload = {
        "signal":    signal,
        "fast_ma":   round(fast_ma, 5),
        "slow_ma":   round(slow_ma, 5),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # Write atomically via temp file to avoid partial reads by the EA
    tmp = signal_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    tmp.replace(signal_path)
    logger.info("Signal written: %s  fast_ma=%.5f  slow_ma=%.5f", signal, fast_ma, slow_ma)


def run_loop(
    fast: int,
    slow: int,
    ma_type: str,
    symbol: str,
    tf_str: str,
    signal_path: Path,
    poll_interval: int,
) -> None:
    from mt5.mt5_connector import MT5Connector  # noqa: PLC0415

    strategy = MACrossStrategy({"fast_window": fast, "slow_window": slow, "ma_type": ma_type})
    needed_bars = slow + 10

    logger.info(
        "Signal writer started | symbol=%s tf=%s fast=%d slow=%d ma=%s poll=%ds",
        symbol, tf_str, fast, slow, ma_type, poll_interval,
    )
    logger.info("Writing signals to: %s", signal_path)

    prev_fast: float | None = None
    prev_slow: float | None = None

    with MT5Connector() as mt5c:
        while _RUNNING:
            try:
                close = _fetch_close_series(mt5c, symbol, tf_str, needed_bars)
                sigs  = strategy.generate(close)

                f_val = float(sigs.fast_ma.iloc[-1])
                s_val = float(sigs.slow_ma.iloc[-1])
                f_prev = float(sigs.fast_ma.iloc[-2]) if len(sigs.fast_ma) > 1 else None
                s_prev = float(sigs.slow_ma.iloc[-2]) if len(sigs.slow_ma) > 1 else None

                # Detect crossover on most recent two bars
                if f_prev is not None and s_prev is not None:
                    if f_val > s_val and f_prev <= s_prev:
                        sig = "buy"
                    elif f_val < s_val and f_prev >= s_prev:
                        sig = "sell"
                    elif f_val > s_val:
                        sig = "buy"   # already long — maintain
                    else:
                        sig = "flat"
                else:
                    sig = "flat"

                signal_path.parent.mkdir(parents=True, exist_ok=True)
                _write_signal(signal_path, sig, f_val, s_val)

            except Exception as exc:  # noqa: BLE001
                logger.error("Error in signal loop: %s", exc)

            # Interruptible sleep
            for _ in range(poll_interval):
                if not _RUNNING:
                    break
                time.sleep(1)

    logger.info("Signal writer stopped.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python mt5/signal_writer.py",
        description="Write MA-cross signals to a JSON file for GoldEA.mq5",
    )
    parser.add_argument("--fast", type=int, default=None, help="Fast MA window (overrides config)")
    parser.add_argument("--slow", type=int, default=None, help="Slow MA window (overrides config)")
    parser.add_argument("--ma-type", default=None, help="simple | exponential (overrides config)")
    parser.add_argument("--timeframe", default="D1", help="MT5 timeframe string, e.g. H1 D1 (default: D1)")
    parser.add_argument("--config",          default=str(_MT5_CFG), help="Path to configs/mt5.yaml")
    parser.add_argument("--backtest-config", default=str(_BT_CFG),  help="Path to configs/backtest.yaml")
    return parser


def main(argv: list[str] | None = None) -> None:
    _signal.signal(_signal.SIGTERM, _handle_sigterm)
    _signal.signal(_signal.SIGINT,  _handle_sigterm)

    parser = _build_parser()
    args   = parser.parse_args(argv)

    mt5_cfg = _load_yaml(Path(args.config))
    bt_cfg  = _load_yaml(Path(args.backtest_config))

    strat = bt_cfg["strategy"]
    fast  = args.fast     or strat.get("fast_window", 20)
    slow  = args.slow     or strat.get("slow_window", 50)
    ma_t  = args.ma_type  or strat.get("ma_type",     "simple")

    sym_cfg = mt5_cfg["symbol"]
    symbol  = sym_cfg["forex"] if sym_cfg["active"] == "forex" else sym_cfg["futures"]

    bridge_cfg    = mt5_cfg["bridge"]
    signal_path   = Path(bridge_cfg["signal_file"])
    poll_interval = int(bridge_cfg.get("poll_interval", 60))

    run_loop(
        fast=fast, slow=slow, ma_type=ma_t,
        symbol=symbol,
        tf_str=args.timeframe,
        signal_path=signal_path,
        poll_interval=poll_interval,
    )


if __name__ == "__main__":
    main()
