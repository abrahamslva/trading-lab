# lean_project/GoldAlgorithm.py
# -------------------------------------------------------------------------------------------------
# LEAN QCAlgorithm — Gold MA-Cross strategy
#
# Reads best_params.json (written by src/optimize.py) at initialisation and configures:
#   - Symbol    : XAUUSD (Forex, default) or GC (Futures) — set via config.json parameter
#   - Indicator : EMA or SMA fast/slow crossover from best_params
#
# Config parameters (set in config.json → "parameters" section or via CLI --parameters):
#   instrument_type   "forex"   | "futures"
#   best_params_path  path to results/best_params.json  (relative to LEAN project root)
#   timeframe         "1D" | "1h" | "4h" | ...  — key inside best_params.json
#   fast_window       optional override (int)
#   slow_window       optional override (int)
#   ma_type           optional override "simple" | "exponential"
#
# Risk controls (mirroring constraints in configs/objectives.yaml):
#   max_drawdown_pct   10.0  — liquidate all if portfolio drawdown exceeds this
#   max_daily_loss_pct  2.0  — stop trading for the session if day-loss exceeds this
# -------------------------------------------------------------------------------------------------

import json
import os
from datetime import timedelta

from AlgorithmImports import (
    Currencies,
    DataNormalizationMode,
    ExtendedMarketHours,
    ExponentialMovingAverage,
    Futures,
    Language,
    Market,
    QCAlgorithm,
    Resolution,
    SecurityType,
    SimpleMovingAverage,
    TimeRules,
    DateRules,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TF_TO_RESOLUTION = {
    "1m":  Resolution.Minute,
    "5m":  Resolution.Minute,   # use Minute; consolidator handles the rest
    "15m": Resolution.Minute,
    "1h":  Resolution.Hour,
    "4h":  Resolution.Hour,
    "1D":  Resolution.Daily,
}

_TF_TO_MINUTES = {
    "1m": 1, "5m": 5, "15m": 15,
    "1h": 60, "4h": 240, "1D": 1440,
}


def _load_best_params(path: str, timeframe: str) -> dict:
    """
    Load best params from JSON.  Falls back to empty dict if file is missing
    (algorithm will use the parameter defaults from config.json).
    """
    if not os.path.isfile(path):
        return {}
    with open(path) as fh:
        data = json.load(fh)
    # best_params.json is keyed by timeframe, e.g. {"1D": {...}, "1h": {...}}
    return data.get(timeframe, data) if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# Algorithm
# ---------------------------------------------------------------------------

class GoldAlgorithm(QCAlgorithm):

    # ------------------------------------------------------------------
    # Initialise
    # ------------------------------------------------------------------

    def Initialize(self):  # noqa: N802
        # ---- backtest window (overrideable via config.json) ----------
        self.SetStartDate(int(self.GetParameter("start_year",  "2020")),
                          int(self.GetParameter("start_month", "1")),
                          int(self.GetParameter("start_day",   "1")))
        self.SetEndDate(  int(self.GetParameter("end_year",    "2024")),
                          int(self.GetParameter("end_month",   "12")),
                          int(self.GetParameter("end_day",     "31")))
        self.SetCash(float(self.GetParameter("init_cash", "100000")))

        # ---- load params from best_params.json -----------------------
        instrument_type = self.GetParameter("instrument_type", "forex").lower()
        tf              = self.GetParameter("timeframe", "1D")
        params_path     = self.GetParameter("best_params_path",
                                             "results/best_params.json")

        best = _load_best_params(params_path, tf)
        self.Log(f"best_params loaded (tf={tf}): {best}")

        self._fast_period = int(
            self.GetParameter("fast_window", str(best.get("fast_window", 20)))
        )
        self._slow_period = int(
            self.GetParameter("slow_window", str(best.get("slow_window", 50)))
        )
        self._ma_type = self.GetParameter(
            "ma_type", str(best.get("ma_type", "simple"))
        ).lower()

        # ---- risk limits (mirror objectives.yaml) --------------------
        self._max_dd_pct    = float(self.GetParameter("max_drawdown_pct",  "10.0"))
        self._max_day_loss  = float(self.GetParameter("max_daily_loss_pct", "2.0"))
        self._peak_value    = None   # set after first bar
        self._day_open_val  = None
        self._halted        = False  # daily halt flag

        # ---- add security -------------------------------------------
        resolution = _TF_TO_RESOLUTION.get(tf, Resolution.Daily)

        if instrument_type == "futures":
            future = self.AddFuture(
                Futures.Metals.Gold,
                resolution=resolution,
                dataNormalizationMode=DataNormalizationMode.BackwardsRatio,
                extendedMarketHours=False,
            )
            future.SetFilter(timedelta(0), timedelta(182))
            self._symbol = future.Symbol
            self._is_futures = True
        else:
            # Forex: XAUUSD
            forex = self.AddForex(
                "XAUUSD",
                resolution=resolution,
                market=Market.Oanda,
            )
            self._symbol = forex.Symbol
            self._is_futures = False

        # ---- build indicators ----------------------------------------
        if self._ma_type == "exponential":
            self._fast_ma = self.EMA(self._symbol, self._fast_period, resolution)
            self._slow_ma = self.EMA(self._symbol, self._slow_period, resolution)
        else:
            self._fast_ma = self.SMA(self._symbol, self._fast_period, resolution)
            self._slow_ma = self.SMA(self._symbol, self._slow_period, resolution)

        self._prev_fast = None
        self._prev_slow = None

        # ---- warm-up --------------------------------------------------
        self.SetWarmUp(self._slow_period + 5, resolution)

        # ---- daily reset scheduled event -----------------------------
        self.Schedule.On(
            self.DateRules.EveryDay(self._symbol),
            self.TimeRules.AfterMarketOpen(self._symbol, 1),
            self._on_day_start,
        )

        self.Log(
            f"GoldAlgorithm: instrument={instrument_type}  tf={tf}  "
            f"fast={self._fast_period}  slow={self._slow_period}  "
            f"ma_type={self._ma_type}"
        )

    # ------------------------------------------------------------------
    # Scheduled: reset daily halt flag + capture day-open value
    # ------------------------------------------------------------------

    def _on_day_start(self):
        self._halted = False
        pv = self.Portfolio.TotalPortfolioValue
        self._day_open_val = pv
        if self._peak_value is None or pv > self._peak_value:
            self._peak_value = pv

    # ------------------------------------------------------------------
    # OnData
    # ------------------------------------------------------------------

    def OnData(self, data):  # noqa: N802
        if self.IsWarmingUp:
            return
        if not self._fast_ma.IsReady or not self._slow_ma.IsReady:
            return

        # ---- risk checks --------------------------------------------
        pv = self.Portfolio.TotalPortfolioValue

        # Update peak
        if self._peak_value is None:
            self._peak_value = pv
        elif pv > self._peak_value:
            self._peak_value = pv

        # Portfolio-wide drawdown guard
        if self._peak_value > 0:
            dd_pct = (self._peak_value - pv) / self._peak_value * 100
            if dd_pct >= self._max_dd_pct:
                if self.Portfolio.Invested:
                    self.Log(
                        f"RISK: global drawdown {dd_pct:.2f}% >= {self._max_dd_pct}%. "
                        "Liquidating all positions."
                    )
                    self.Liquidate()
                return   # no new trades while in protection mode

        # Daily loss guard
        if self._day_open_val and self._day_open_val > 0:
            day_loss_pct = (self._day_open_val - pv) / self._day_open_val * 100
            if day_loss_pct >= self._max_day_loss:
                if not self._halted:
                    self.Log(
                        f"RISK: daily loss {day_loss_pct:.2f}% >= {self._max_day_loss}%. "
                        "Halting for today."
                    )
                    self._halted = True
        if self._halted:
            return

        # ---- symbol check -------------------------------------------
        symbol = self._symbol
        # For futures, use the canonical mapped symbol
        if self._is_futures:
            mapped = self.Securities.Keys
            symbol = next(
                (k for k in mapped if k.SecurityType == SecurityType.Future
                 and k.Canonical == self._symbol),
                None,
            )
            if symbol is None:
                return

        if symbol not in data or data[symbol] is None:
            return

        # ---- signal detection ---------------------------------------
        fast = float(self._fast_ma.Current.Value)
        slow = float(self._slow_ma.Current.Value)

        is_invested = self.Portfolio[symbol].Invested

        if self._prev_fast is not None and self._prev_slow is not None:
            # Long entry: fast crossed above slow
            if (not is_invested
                    and fast > slow
                    and self._prev_fast <= self._prev_slow):
                self.SetHoldings(symbol, 1.0)
                self.Log(f"ENTRY  fast={fast:.4f} slow={slow:.4f}")

            # Exit: fast crossed below slow
            elif is_invested and fast < slow and self._prev_fast >= self._prev_slow:
                self.Liquidate(symbol)
                self.Log(f"EXIT   fast={fast:.4f} slow={slow:.4f}")

        self._prev_fast = fast
        self._prev_slow = slow

    # ------------------------------------------------------------------
    # OnEndOfAlgorithm — log final summary
    # ------------------------------------------------------------------

    def OnEndOfAlgorithm(self):  # noqa: N802
        pv   = self.Portfolio.TotalPortfolioValue
        ret  = (pv / 100_000 - 1) * 100
        self.Log(f"=== END OF BACKTEST ===")
        self.Log(f"  Final portfolio value : ${pv:,.2f}")
        self.Log(f"  Total return          : {ret:.2f}%")
