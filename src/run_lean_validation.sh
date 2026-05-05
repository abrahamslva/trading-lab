#!/usr/bin/env bash
# src/run_lean_validation.sh
# ---------------------------------------------------------------------------
# Run a LEAN backtest for GoldAlgorithm and store all outputs under
# results/lean/<run_id>/
#
# Prerequisites
# -------------
#   lean CLI installed  (pip install lean==1.2.6)
#   lean login          (run once to authenticate with QuantConnect)
#
# Usage
# -----
#   bash src/run_lean_validation.sh                          # forex, 1D, params from best_params.json
#   INSTRUMENT=futures bash src/run_lean_validation.sh       # GC futures
#   TIMEFRAME=1h bash src/run_lean_validation.sh             # use 1h params
#   FAST=10 SLOW=30 bash src/run_lean_validation.sh          # manual overrides
#
# Environment variable overrides (all optional)
# ---------------------------------------------
#   INSTRUMENT        forex | futures         (default: forex)
#   TIMEFRAME         1D | 1h | 4h | ...      (default: 1D)
#   FAST, SLOW        integer window overrides
#   MA_TYPE           simple | exponential    (override)
#   START_DATE        YYYY-MM-DD              (default: 2020-01-01)
#   END_DATE          YYYY-MM-DD              (default: 2024-12-31)
#   INIT_CASH         integer                 (default: 100000)
#   BEST_PARAMS_JSON  path                    (default: results/best_params.json)
#   LEAN_PROJECT_DIR  path                    (default: lean_project)
#   RESULTS_BASE      path                    (default: results/lean)
# ---------------------------------------------------------------------------

set -euo pipefail

# ---- repo root (parent of src/) ----------------------------------------
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- configuration -------------------------------------------------------
INSTRUMENT="${INSTRUMENT:-forex}"
TIMEFRAME="${TIMEFRAME:-1D}"
BEST_PARAMS_JSON="${BEST_PARAMS_JSON:-results/best_params.json}"
LEAN_PROJECT_DIR="${LEAN_PROJECT_DIR:-lean_project}"
RESULTS_BASE="${RESULTS_BASE:-results/lean}"
START_DATE="${START_DATE:-2020-01-01}"
END_DATE="${END_DATE:-2024-12-31}"
INIT_CASH="${INIT_CASH:-100000}"

# ---- read best_params for this timeframe ---------------------------------
# Values from best_params.json are used as defaults; CLI vars take precedence.
FAST_FROM_JSON=""
SLOW_FROM_JSON=""
MA_FROM_JSON=""

if [[ -f "$BEST_PARAMS_JSON" ]]; then
    FAST_FROM_JSON=$(python3 - <<EOF
import json, sys
try:
    d = json.load(open("$BEST_PARAMS_JSON"))
    tf = "$TIMEFRAME"
    params = d.get(tf, d) if isinstance(d, dict) else {}
    print(params.get("fast_window", ""))
except Exception:
    print("")
EOF
)
    SLOW_FROM_JSON=$(python3 - <<EOF
import json, sys
try:
    d = json.load(open("$BEST_PARAMS_JSON"))
    tf = "$TIMEFRAME"
    params = d.get(tf, d) if isinstance(d, dict) else {}
    print(params.get("slow_window", ""))
except Exception:
    print("")
EOF
)
    MA_FROM_JSON=$(python3 - <<EOF
import json, sys
try:
    d = json.load(open("$BEST_PARAMS_JSON"))
    tf = "$TIMEFRAME"
    params = d.get(tf, d) if isinstance(d, dict) else {}
    print(params.get("ma_type", ""))
except Exception:
    print("")
EOF
)
else
    echo "WARNING: $BEST_PARAMS_JSON not found. Using defaults from config.json."
fi

FAST="${FAST:-${FAST_FROM_JSON:-20}}"
SLOW="${SLOW:-${SLOW_FROM_JSON:-50}}"
MA_TYPE="${MA_TYPE:-${MA_FROM_JSON:-simple}}"

# ---- derive start/end year/month/day from dates --------------------------
START_YEAR=$(echo "$START_DATE"  | cut -d- -f1)
START_MONTH=$(echo "$START_DATE" | cut -d- -f2 | sed 's/^0//')
START_DAY=$(echo "$START_DATE"   | cut -d- -f3 | sed 's/^0//')
END_YEAR=$(echo "$END_DATE"      | cut -d- -f1)
END_MONTH=$(echo "$END_DATE"     | cut -d- -f2 | sed 's/^0//')
END_DAY=$(echo "$END_DATE"       | cut -d- -f3 | sed 's/^0//')

# ---- build run ID --------------------------------------------------------
RUN_ID="lean_${INSTRUMENT}_${TIMEFRAME}_f${FAST}s${SLOW}_$(date -u +%Y%m%d_%H%M%S)"
OUT_DIR="${RESULTS_BASE}/${RUN_ID}"
mkdir -p "$OUT_DIR"

echo "══════════════════════════════════════════════════════"
echo "  LEAN Backtest Validation"
echo "  Run ID         : $RUN_ID"
echo "  Instrument     : $INSTRUMENT"
echo "  Timeframe      : $TIMEFRAME"
echo "  Fast / Slow    : $FAST / $SLOW  ($MA_TYPE)"
echo "  Window         : $START_DATE → $END_DATE"
echo "  Output         : $OUT_DIR"
echo "══════════════════════════════════════════════════════"

# ---- build LEAN parameter overrides list ---------------------------------
# lean backtest accepts --parameters key=value (space-separated pairs)
LEAN_PARAMS=(
    "instrument_type=$INSTRUMENT"
    "timeframe=$TIMEFRAME"
    "best_params_path=../results/best_params.json"
    "fast_window=$FAST"
    "slow_window=$SLOW"
    "ma_type=$MA_TYPE"
    "start_year=$START_YEAR"
    "start_month=$START_MONTH"
    "start_day=$START_DAY"
    "end_year=$END_YEAR"
    "end_month=$END_MONTH"
    "end_day=$END_DAY"
    "init_cash=$INIT_CASH"
    "max_drawdown_pct=10.0"
    "max_daily_loss_pct=2.0"
)

# Convert array to --parameters key=value pairs
PARAM_ARGS=()
for kv in "${LEAN_PARAMS[@]}"; do
    PARAM_ARGS+=(--parameter "$kv")
done

# ---- run LEAN backtest ---------------------------------------------------
echo ""
echo "Running: lean backtest $LEAN_PROJECT_DIR ..."
echo ""

lean backtest "$LEAN_PROJECT_DIR" \
    --output "$OUT_DIR" \
    "${PARAM_ARGS[@]}" \
    2>&1 | tee "$OUT_DIR/lean_stdout.log"

LEAN_EXIT=${PIPESTATUS[0]}

# ---- post-processing -----------------------------------------------------
if [[ $LEAN_EXIT -eq 0 ]]; then
    echo ""
    echo "── LEAN backtest complete ────────────────────────────"

    # Extract key stats from the JSON result if present
    RESULT_JSON=$(find "$OUT_DIR" -name "*.json" ! -name "config.json" \
                  -newer "$LEAN_PROJECT_DIR/config.json" 2>/dev/null | head -1)

    if [[ -n "$RESULT_JSON" ]]; then
        echo "  Result JSON    : $RESULT_JSON"
        python3 - <<EOF
import json, sys

path = "$RESULT_JSON"
try:
    with open(path) as f:
        data = json.load(f)

    stats = data.get("Statistics", {})
    if not stats:
        # Some LEAN versions nest under "Results"
        stats = data.get("Results", {}).get("Statistics", {})

    keys = [
        "Total Net Profit", "Total Return",
        "Sharpe Ratio", "Drawdown",
        "Total Trades", "Win Rate",
        "Average Win", "Average Loss",
        "Profit-Loss Ratio",
    ]
    print("")
    print("  ── LEAN Statistics ─────────────────────────────")
    for k in keys:
        if k in stats:
            print(f"  {k:<30} {stats[k]}")
    print("  ────────────────────────────────────────────────")
    print("")
except Exception as exc:
    print(f"  (Could not parse result JSON: {exc})")
EOF
    fi

    # Write a compact metadata file alongside results
    python3 - <<EOF
import json, os
from datetime import datetime, timezone

meta = {
    "run_id":       "$RUN_ID",
    "instrument":   "$INSTRUMENT",
    "timeframe":    "$TIMEFRAME",
    "fast_window":  int("$FAST"),
    "slow_window":  int("$SLOW"),
    "ma_type":      "$MA_TYPE",
    "start_date":   "$START_DATE",
    "end_date":     "$END_DATE",
    "init_cash":    int("$INIT_CASH"),
    "completed_at": datetime.now(timezone.utc).isoformat(),
}
out = os.path.join("$OUT_DIR", "run_meta.json")
with open(out, "w") as fh:
    json.dump(meta, fh, indent=2)
print(f"  Metadata saved : {out}")
EOF

    echo "  All outputs    : $OUT_DIR/"
    echo ""
else
    echo ""
    echo "ERROR: lean backtest exited with code $LEAN_EXIT."
    echo "Check $OUT_DIR/lean_stdout.log for details."
    exit $LEAN_EXIT
fi
