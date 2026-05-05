#!/usr/bin/env bash
# setup.sh — idempotent environment bootstrap for trading-lab
set -euo pipefail

MARKER=".setup_done"

if [[ -f "$MARKER" ]]; then
  echo "Environment already set up. Delete '$MARKER' to re-run."
  exit 0
fi

echo "==> Upgrading pip..."
pip install --quiet --upgrade pip

echo "==> Installing pinned dependencies..."
pip install --quiet \
  "numpy==1.24.4" \
  "pandas==2.0.3" \
  "numba==0.57.1" \
  "llvmlite==0.40.1" \
  "vectorbt==0.26.1" \
  "yfinance==0.2.40" \
  "plotly==5.18.0" \
  "kaleido==0.2.1" \
  "jupyterlab==4.1.5" \
  "optuna==3.5.0" \
  "scipy==1.11.4" \
  "scikit-learn==1.3.2" \
  "lean==1.2.6"

echo "==> Creating project directories..."
mkdir -p data notebooks results src configs

echo "==> Verifying key packages..."
python - <<'EOF'
import importlib, sys
pkgs = ["numpy", "pandas", "numba", "vectorbt", "yfinance", "plotly", "optuna", "scipy", "sklearn"]
failed = []
for p in pkgs:
    try:
        importlib.import_module(p)
    except ImportError:
        failed.append(p)
if failed:
    print(f"WARN: could not import: {failed}", file=sys.stderr)
else:
    print("All key packages imported successfully.")
EOF

touch "$MARKER"
echo "==> Setup complete."
