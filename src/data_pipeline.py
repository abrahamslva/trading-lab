"""
src/data_pipeline.py
--------------------
Multi-provider, multi-timeframe GOLD data pipeline.

CLI usage
---------
    python -m src.data_pipeline --provider yfinance --start 2015-01-01
    python -m src.data_pipeline --provider yfinance --start 2020-01-01 --end 2024-12-31
    python -m src.data_pipeline --provider dukascopy --start 2020-01-01

Outputs (snappy-compressed Parquet, partitioned by timeframe)
-------------------------------------------------------------
    data/1m/gold.parquet
    data/5m/gold.parquet
    data/15m/gold.parquet
    data/1h/gold.parquet
    data/4h/gold.parquet
    data/1D/gold.parquet
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.dukascopy_loader import DukascopyLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent.parent / "configs" / "data.yaml"
_OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]

# pandas resample rule → output folder name
_TIMEFRAME_MAP: dict[str, str] = {
    "1min": "1m",
    "5min": "5m",
    "15min": "15m",
    "1h":   "1h",
    "4h":   "4h",
    "1D":   "1D",
}


def _load_cfg(path: Path = _CONFIG_PATH) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _parquet_path(base_dir: Path, tf_label: str) -> Path:
    p = base_dir / tf_label
    p.mkdir(parents=True, exist_ok=True)
    return p / "gold.parquet"


def _read_cache(path: Path) -> Optional[pd.DataFrame]:
    """Return cached DataFrame or None if cache doesn't exist / is corrupt."""
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        elif df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        return df
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache read failed (%s), ignoring: %s", path, exc)
        return None


def _write_parquet(df: pd.DataFrame, path: Path, compression: str = "snappy") -> None:
    df.to_parquet(path, compression=compression, index=True)
    logger.info("Saved %d rows → %s", len(df), path)


def _merge_incremental(cached: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Append *new* rows that are strictly after the last cached timestamp."""
    if cached is None or cached.empty:
        return new
    if new is None or new.empty:
        return cached
    last_ts = cached.index.max()
    fresh = new[new.index > last_ts]
    if fresh.empty:
        logger.info("No new bars to append (cache is up-to-date).")
        return cached
    merged = pd.concat([cached, fresh]).sort_index()
    logger.info("Appended %d new bars.", len(fresh))
    return merged


# ---------------------------------------------------------------------------
# Provider A — yfinance
# ---------------------------------------------------------------------------

def _fetch_yfinance(
    ticker: str,
    start: str,
    end: Optional[str],
    cached_df: Optional[pd.DataFrame],
    incremental: bool,
) -> pd.DataFrame:
    """Download daily OHLCV from yfinance, reusing/extending cache."""
    import yfinance as yf  # noqa: PLC0415

    fetch_start = start
    if incremental and cached_df is not None and not cached_df.empty:
        last_ts = cached_df.index.max()
        fetch_start = (last_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info("Incremental mode: fetching from %s", fetch_start)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fetch_end = end or today
    if fetch_start >= fetch_end:
        logger.info("Cache already covers requested range.")
        return cached_df if cached_df is not None else pd.DataFrame(columns=_OHLCV_COLS)

    logger.info("yfinance: downloading %s [%s → %s]", ticker, fetch_start, fetch_end)
    raw = yf.download(
        ticker,
        start=fetch_start,
        end=fetch_end,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if raw.empty:
        logger.warning("yfinance returned no data.")
        return cached_df if cached_df is not None else pd.DataFrame(columns=_OHLCV_COLS)

    # Normalise columns
    raw = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    raw.index = pd.to_datetime(raw.index, utc=True)
    raw.index.name = "timestamp"

    return _merge_incremental(cached_df, raw)


# ---------------------------------------------------------------------------
# Provider B — Dukascopy
# ---------------------------------------------------------------------------

def _fetch_dukascopy(
    cfg: dict,
    start: str,
    end: Optional[str],
    cached_df: Optional[pd.DataFrame],
    incremental: bool,
) -> pd.DataFrame:
    """Load base-timeframe OHLCV from Dukascopy loader (stub)."""
    fetch_start = start
    if incremental and cached_df is not None and not cached_df.empty:
        fetch_start = (
            cached_df.index.max() + pd.Timedelta(minutes=1)
        ).strftime("%Y-%m-%d %H:%M")
        logger.info("Incremental mode: fetching from %s", fetch_start)

    loader = DukascopyLoader(
        instrument=cfg["symbol"]["dukascopy"],
        cfg=cfg.get("dukascopy", {}),
        base_timeframe=cfg["defaults"].get("base_timeframe", "1min"),
    )
    new_df = loader.load(fetch_start, end)
    return _merge_incremental(cached_df, new_df)


# ---------------------------------------------------------------------------
# Resampling
# ---------------------------------------------------------------------------

def _resample_ohlcv(base: pd.DataFrame, rule: str) -> pd.DataFrame:
    """
    Resample a daily (or finer) OHLCV DataFrame to *rule*.

    For timeframes coarser than the base (e.g., 4h from 1D), the
    function returns the base unchanged to avoid nonsensical up-sampling.
    """
    if base.empty:
        return base

    agg = {
        "Open":   "first",
        "High":   "max",
        "Low":    "min",
        "Close":  "last",
        "Volume": "sum",
    }
    resampled = base.resample(rule).agg(agg).dropna(subset=["Open"])
    return resampled


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    provider: str,
    start: str,
    end: Optional[str] = None,
    config_path: Path = _CONFIG_PATH,
) -> dict[str, Path]:
    """
    Execute the full pipeline.

    Returns
    -------
    dict mapping timeframe label → Path of the written Parquet file.
    """
    cfg = _load_cfg(config_path)
    cache_enabled = cfg["cache"]["enabled"]
    incremental = cfg["cache"]["incremental"]
    base_dir = Path(cfg["storage"]["base_dir"])
    compression = cfg["storage"]["compression"]
    tf_map: dict[str, str] = {
        rule: label for rule, label in cfg["timeframes"].items()
    }

    # ---- load base (daily/finest) data -----------------------------------
    # For the yfinance provider the natural base is "1D" (daily history).
    # For Dukascopy it is the configured base_timeframe.
    base_tf_label = "1D" if provider == "yfinance" else (
        tf_map.get(cfg["defaults"].get("base_timeframe", "1min"), "1m")
    )
    base_cache_path = _parquet_path(base_dir, base_tf_label)
    cached_base = _read_cache(base_cache_path) if cache_enabled else None

    if provider == "yfinance":
        base_df = _fetch_yfinance(
            ticker=cfg["symbol"]["yfinance"],
            start=start,
            end=end,
            cached_df=cached_base,
            incremental=incremental,
        )
    elif provider == "dukascopy":
        base_df = _fetch_dukascopy(
            cfg=cfg,
            start=start,
            end=end,
            cached_df=cached_base,
            incremental=incremental,
        )
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Choose 'yfinance' or 'dukascopy'.")

    if base_df.empty:
        logger.error("No base data retrieved. Aborting.")
        return {}

    # Persist base
    _write_parquet(base_df, base_cache_path, compression=compression)
    written: dict[str, Path] = {base_tf_label: base_cache_path}

    # ---- resample to all other timeframes --------------------------------
    skip_rules = set()
    if provider == "yfinance":
        # yfinance gives daily → skip sub-daily resamples (would be up-sampling)
        skip_rules = {"1min", "5min", "15min", "1h", "4h"}

    for rule, label in tf_map.items():
        if label == base_tf_label:
            continue  # already written
        if rule in skip_rules:
            logger.info("Skipping sub-daily resample %s (%s) for yfinance.", label, rule)
            continue

        out_path = _parquet_path(base_dir, label)
        cached_tf = _read_cache(out_path) if cache_enabled else None

        resampled = _resample_ohlcv(base_df, rule)
        merged = _merge_incremental(cached_tf, resampled)
        _write_parquet(merged, out_path, compression=compression)
        written[label] = out_path

    logger.info("Pipeline complete. Files written: %s", list(written.values()))
    return written


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.data_pipeline",
        description="Download & store multi-timeframe GOLD OHLCV data.",
    )
    parser.add_argument(
        "--provider",
        choices=["yfinance", "dukascopy"],
        default="yfinance",
        help="Data provider (default: yfinance)",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="End date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--config",
        default=str(_CONFIG_PATH),
        help=f"Path to data.yaml (default: {_CONFIG_PATH})",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Basic date validation
    try:
        datetime.strptime(args.start, "%Y-%m-%d")
        if args.end:
            datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError as exc:
        parser.error(f"Invalid date format: {exc}")

    written = run_pipeline(
        provider=args.provider,
        start=args.start,
        end=args.end,
        config_path=Path(args.config),
    )
    if not written:
        sys.exit(1)


if __name__ == "__main__":
    main()
