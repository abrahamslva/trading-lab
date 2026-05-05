# trading-lab

Minimal quant-research environment for **GOLD backtesting** using [VectorBT](https://vectorbt.dev/) and [LEAN](https://www.lean.io/), designed to run in GitHub Codespaces.

---

## Repository layout

```
.devcontainer/devcontainer.json   # Codespaces: Python 3.10 + Docker-in-Docker
setup.sh                          # Idempotent dependency installer
data/                             # Raw & processed market data
notebooks/                        # Jupyter research notebooks
results/                          # Backtest outputs (PnL, charts, reports)
src/                              # Reusable Python modules / strategies
configs/                          # LEAN project configs, algo params
```

---

## Quick start in Codespaces

### 1. Open in Codespaces

Click **Code → Codespaces → Create codespace on main** in GitHub.  
The `postCreateCommand` in `devcontainer.json` will run `setup.sh` automatically.

### 2. Manual setup (if needed)

```bash
bash setup.sh
```

### 3. Launch JupyterLab

```bash
jupyter lab --no-browser --port=8888 --ip=0.0.0.0
```

Codespaces will auto-forward port `8888`. Click the popup URL to open JupyterLab.

### 4. Download GOLD data (example)

```bash
python - <<'EOF'
import yfinance as yf
df = yf.download("GC=F", start="2015-01-01", end="2024-12-31")
df.to_parquet("data/gold_daily.parquet")
print(df.tail())
EOF
```

### 5. Run a minimal VectorBT backtest

```bash
python - <<'EOF'
import vectorbt as vbt
import pandas as pd

price = pd.read_parquet("data/gold_daily.parquet")["Close"].squeeze()

fast_ma = vbt.MA.run(price, 20)
slow_ma = vbt.MA.run(price, 50)

entries = fast_ma.ma_crossed_above(slow_ma)
exits   = fast_ma.ma_crossed_below(slow_ma)

pf = vbt.Portfolio.from_signals(price, entries, exits, freq="1D")
print(pf.stats())
pf.plot().write_html("results/gold_ma_backtest.html")
EOF
```

### 6. Initialize a LEAN project

```bash
lean login                              # authenticate with QuantConnect
lean create-project --language python configs/gold-strategy
lean research configs/gold-strategy     # opens Jupyter inside LEAN sandbox
lean backtest configs/gold-strategy     # run full LEAN backtest
```

---

## Pinned dependencies

| Package | Version |
|---|---|
| numpy | 1.24.4 |
| pandas | 2.0.3 |
| numba | 0.57.1 |
| llvmlite | 0.40.1 |
| vectorbt | 0.26.1 |
| yfinance | 0.2.40 |
| plotly | 5.18.0 |
| kaleido | 0.2.1 |
| jupyterlab | 4.1.5 |
| optuna | 3.5.0 |
| scipy | 1.11.4 |
| scikit-learn | 1.3.2 |
| lean | 1.2.6 |

To reinstall from scratch:

```bash
rm .setup_done && bash setup.sh
```