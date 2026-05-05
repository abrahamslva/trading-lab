# MT5 Integration — Setup & Usage Guide

## Prerequisites (Windows only)

| Requirement | Version / note |
|---|---|
| MetaTrader 5 desktop | Any broker supporting XAUUSD or GOLD futures |
| Python | 3.10 (same as Codespaces image; install from python.org) |
| MetaTrader5 package | `pip install MetaTrader5` |
| PyYAML, pandas | Already in `setup.sh` requirements |

> The `MetaTrader5` Python package only works on **Windows**. All other
> modules in this repo run on Linux/Codespaces; only `mt5/` needs Windows.

---

## 1. Install Python dependencies on Windows

```powershell
pip install MetaTrader5 pandas pyyaml
```

---

## 2. Edit `configs/mt5.yaml`

```yaml
connection:
  terminal_path: "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
  server: "YourBroker-Live"    # as shown in MT5 login screen
  login: 123456                # your account number
  password: "yourpassword"     # or set MT5_PASSWORD env var

symbol:
  active: "forex"              # forex → XAUUSD  |  futures → GOLD
```

**Security note:** prefer environment variables over plain-text credentials:

```powershell
$env:MT5_LOGIN    = "123456"
$env:MT5_PASSWORD = "yourpassword"
$env:MT5_SERVER   = "YourBroker-Live"
```

---

## 3. Install and compile GoldEA.mq5

1. Copy `mt5/GoldEA.mq5` to your MT5 data folder:
   ```
   %APPDATA%\MetaQuotes\Terminal\<id>\MQL5\Experts\GoldEA.mq5
   ```
2. Open **MetaEditor** (F4 in MT5) → open `GoldEA.mq5` → press **F7** to compile.
3. No compilation errors should appear. Warnings about `strict` are safe to ignore.

---

## 4a. Run EA in indicator mode (no Python required)

1. In MT5 chart (XAUUSD, any timeframe) drag **GoldEA** from the Navigator panel.
2. Set inputs:

   | Input | Recommended |
   |---|---|
   | FastWindow | 20 (or value from `results/best_params.json`) |
   | SlowWindow | 50 |
   | UseEMA | false |
   | SignalMode | **MODE_INDICATOR** |
   | RiskPercent | 1.0 |
   | MaxDrawdownPct | 10.0 |
   | MaxDailyLossPct | 2.0 |
   | MagicNumber | 20240101 |

3. Check **Allow Algo Trading** in the EA properties → click OK.

---

## 4b. Run EA in file-bridge mode (Python writes signals)

### Step 1 — Start the signal writer on Windows

```powershell
cd C:\path\to\trading-lab

# Uses best_params.json automatically if it exists
python mt5\signal_writer.py --timeframe D1

# Manual override
python mt5\signal_writer.py --fast 10 --slow 30 --timeframe H1
```

The script writes `mt5/bridge/signal.json` every `poll_interval` seconds (default 60 s).

### Step 2 — Point the EA to the signal file

The EA reads files from MT5's **sandbox** (`MQL5\Files\`).
Two options:

**Option A — Symlink (recommended):**
```powershell
# Run as Administrator
$mt5Files = "$env:APPDATA\MetaQuotes\Terminal\<id>\MQL5\Files"
New-Item -ItemType SymbolicLink -Path "$mt5Files\signal.json" `
         -Target "C:\path\to\trading-lab\mt5\bridge\signal.json"
```

**Option B — Absolute path in EA input:**
Set `SignalFile` input to the full absolute path (MT5 allows absolute paths in `FileOpen`):
```
C:\path\to\trading-lab\mt5\bridge\signal.json
```

### Step 3 — Configure EA inputs

| Input | Value |
|---|---|
| SignalMode | **MODE_FILE** |
| SignalFile | `signal.json` (or absolute path) |

---

## 5. Read best_params.json into EA inputs

After running the optimizer:

```powershell
python -c "
import json
d = json.load(open('results/best_params.json'))
tf = '1D'
p = d.get(tf, {})
print(f'FastWindow = {p.get(\"fast_window\", 20)}')
print(f'SlowWindow = {p.get(\"slow_window\", 50)}')
print(f'UseEMA     = {\"true\" if p.get(\"ma_type\") == \"exponential\" else \"false\"}')
"
```

Copy those values into the EA input dialog.

---

## 6. Python connector — quick test

```python
# test_connector.py  (run on Windows)
from mt5.mt5_connector import MT5Connector

with MT5Connector() as c:
    print(c.get_account_info())
    bars = c.get_latest_bar("XAUUSD", count=3)
    for b in bars:
        print(b)
    positions = c.get_positions("XAUUSD")
    print("Open positions:", positions)
```

```powershell
python test_connector.py
```

---

## 7. Signal file format reference

`mt5/bridge/signal.json`:

```json
{
  "signal":    "buy",
  "fast_ma":   2345.12345,
  "slow_ma":   2330.00000,
  "timestamp": "2024-06-01T08:00:00+00:00"
}
```

| Field | Values |
|---|---|
| `signal` | `"buy"` · `"sell"` · `"flat"` |
| `fast_ma` | Current fast MA value (informational) |
| `slow_ma` | Current slow MA value (informational) |
| `timestamp` | ISO-8601 UTC |

---

## 8. Risk controls (active in both modes)

| Control | Default | Behaviour |
|---|---|---|
| `MaxDrawdownPct` | 10% | Liquidate all + stop trading |
| `MaxDailyLossPct` | 2% | Halt until next trading day |
| `SlPoints` | 0 (off) | Set > 0 to enable hard stop-loss |
| `TpPoints` | 0 (off) | Set > 0 to enable take-profit |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `MT5 initialize() failed` | Check `terminal_path` in mt5.yaml; ensure MT5 is installed |
| `MT5 login() failed` | Verify login/password/server; check broker name spelling |
| EA not trading | Confirm **Algo Trading** button is green in MT5 toolbar |
| Signal file not read | Check `SignalFile` input; verify symlink or absolute path |
| `MetaTrader5` import error | `pip install MetaTrader5` — only works on Windows |
