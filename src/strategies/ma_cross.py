"""
src/strategies/ma_cross.py
--------------------------
Moving-average crossover signal generator.

Works with any OHLCV DataFrame produced by src.data_pipeline
(any timeframe, any provider).

Signal logic
------------
- Entry  (long): fast MA crosses **above** slow MA
- Exit   (long): fast MA crosses **below** slow MA
- No shorting by default (easily extensible).

Supported MA types
------------------
- "simple"       → pandas rolling mean
- "exponential"  → pandas ewm (span-based)

Public API
----------
    signals = MACrossStrategy(cfg).generate(close)
    signals.entries   # pd.Series[bool]
    signals.exits     # pd.Series[bool]
    signals.fast_ma   # pd.Series[float]  (for plotting)
    signals.slow_ma   # pd.Series[float]
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class MACrossSignals:
    entries: pd.Series
    exits:   pd.Series
    fast_ma: pd.Series
    slow_ma: pd.Series
    params:  dict = field(default_factory=dict)

    def summary(self) -> str:
        n_entries = int(self.entries.sum())
        n_exits   = int(self.exits.sum())
        return (
            f"MACross({self.params}) → "
            f"{n_entries} entries, {n_exits} exits "
            f"over {len(self.entries)} bars"
        )


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

class MACrossStrategy:
    """
    Moving-average crossover strategy.

    Parameters
    ----------
    cfg : dict
        ``strategy`` section from ``configs/backtest.yaml``, e.g.::

            fast_window: 20
            slow_window: 50
            ma_type: "simple"

    Alternatively pass keyword overrides:

        MACrossStrategy(cfg, fast_window=10, slow_window=30)
    """

    def __init__(self, cfg: dict, **overrides) -> None:
        merged = {**cfg, **overrides}
        self.fast_window: int  = int(merged.get("fast_window", 20))
        self.slow_window: int  = int(merged.get("slow_window", 50))
        self.ma_type:     str  = str(merged.get("ma_type", "simple")).lower()

        if self.fast_window >= self.slow_window:
            raise ValueError(
                f"fast_window ({self.fast_window}) must be < "
                f"slow_window ({self.slow_window})."
            )
        if self.ma_type not in ("simple", "exponential"):
            raise ValueError(
                f"ma_type must be 'simple' or 'exponential', got {self.ma_type!r}."
            )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate(self, close: pd.Series) -> MACrossSignals:
        """
        Compute signals from a Close price series.

        Parameters
        ----------
        close : pd.Series
            Closing prices with a DatetimeIndex (any timeframe).

        Returns
        -------
        MACrossSignals
        """
        if not isinstance(close.index, pd.DatetimeIndex):
            raise TypeError("close must have a DatetimeIndex.")
        if len(close) < self.slow_window:
            raise ValueError(
                f"Series length ({len(close)}) is shorter than "
                f"slow_window ({self.slow_window}). Need more data."
            )

        fast_ma = self._ma(close, self.fast_window)
        slow_ma = self._ma(close, self.slow_window)

        # Cross detection: +1 tick delay (signal fires on next bar open)
        crossed_above = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        crossed_below = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

        entries = crossed_above.fillna(False)
        exits   = crossed_below.fillna(False)

        return MACrossSignals(
            entries=entries,
            exits=exits,
            fast_ma=fast_ma,
            slow_ma=slow_ma,
            params={
                "fast_window": self.fast_window,
                "slow_window": self.slow_window,
                "ma_type":     self.ma_type,
            },
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ma(self, series: pd.Series, window: int) -> pd.Series:
        if self.ma_type == "simple":
            return series.rolling(window, min_periods=window).mean()
        # exponential: span = window for consistency with simple MA period
        return series.ewm(span=window, min_periods=window, adjust=False).mean()
