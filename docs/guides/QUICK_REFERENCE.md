# 🚀 Trading Lab — Quick Reference Guide

## Current Status (Session Summary)

**Date**: May 6, 2026  
**Time**: ~6 hours into session  
**Progress**: 38.7% (Atlas GIC integration COMPLETE)

---

## 📊 What's Running Right Now

### 1️⃣ **Dukascopy Download** (Background)
- **Status**: ✅ In Progress (Chunk 9/21)
- **Progress**: 38.7% (59,018 M15 bars)
- **Current**: 2020-01-01 to 2020-07-01
- **ETA**: ~1.6 hours remaining
- **File**: `/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet` (2.4 MB)
- **Recovery**: Checkpoint-based resume (no data loss risk)

### 2️⃣ **Auto-Trigger Watcher** (Background)
- **Status**: ✅ Running (PID 16050)
- **Function**: Polls every 30s for parquet >10MB
- **Action**: Auto-launches `src/backtest_full.py` when ready
- **Expected**: In ~1.6 hours

### 3️⃣ **Atlas GIC Integration** (NEW THIS SESSION)
- **Status**: ✅ COMPLETE
- **Files**: 20 integrated (3,416 lines code + 1,025 lines docs)
- **Location**: `/workspaces/trading-lab/atlas-gic/`
- **Guide**: `ATLAS_GIC_INTEGRATION.md` (278 lines)

---

## 📁 Key Locations

### Data
```
/workspaces/trading-lab/data/
├── dukascopy/
│   └── XAUUSD_15min_mt5.parquet        ← In-progress download
└── download.log                        ← Real-time progress
```

### Code
```
/workspaces/trading-lab/src/
├── backtest_full.py                    ← 9 strategies × 7 timeframes
├── download_data.py                    ← Dukascopy downloader (resumable)
├── run_when_ready.py                   ← Auto-trigger watcher
└── strategies/
    ├── ma_cross.py                     ← Simple baseline
    └── ... (others)
```

### Atlas GIC Integration
```
/workspaces/trading-lab/atlas-gic/
├── src/
│   ├── janus.py                        ← Meta-weighting (cohort blending)
│   └── mirofish/                       ← Training framework
├── architecture/                       ← System documentation
├── prompts/                            ← Agent role examples
└── results/                            ← Historical backtests
```

### Results (When Complete)
```
/workspaces/trading-lab/results/
├── backtest_full_results.csv           ← 63 test results (9×7)
├── backtest_full_params.json           ← Parameter sets
└── [auto-generated on backtest completion]
```

---

## 🎯 What Happens Next (Automatic)

```
1. Download reaches 100% (in ~1.6h)
        ↓
2. Watcher detects parquet >10MB
        ↓
3. Auto-triggers: python src/backtest_full.py
        ↓
4. All 63 combinations run (~45 min)
        ↓
5. Results saved: results/backtest_full_results.csv
        ↓
6. Manual review: Identify best strategies
        ↓
7. JANUS integration: Blend top performers
```

---

## 🔍 How to Monitor Progress

### Check Download Status
```bash
tail -f /workspaces/trading-lab/data/download.log
```

### Check Parquet Size
```bash
ls -lh /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
```

### Verify Watcher is Running
```bash
ps aux | grep run_when_ready.py
```

### Once Backtest Completes
```bash
# View results
head -20 /workspaces/trading-lab/results/backtest_full_results.csv

# Find best strategy
python3 << 'EOF'
import pandas as pd
results = pd.read_csv('/workspaces/trading-lab/results/backtest_full_results.csv')
best = results[results['all_objectives_ok'] == True].nlargest(3, 'sharpe_ratio')[['version', 'timeframe', 'sharpe_ratio', 'avg_monthly_ret_pct']]
print(best)
EOF
```

---

## 📋 Objectives Status

| Metric | Target | V1_2H Result | Status |
|--------|--------|--------------|--------|
| Monthly Return | ≥1.5% | 0.43% | ⚠️ Below (M15 expected to improve) |
| Max Drawdown | ≤9% | 2.0% | ✅ Pass |
| Trades/Month | ≥7 | 4.7 | ⚠️ Below (M15 expected 15+) |
| Daily Loss | ≤5% | Enforced | ✅ Pass |
| Sharpe Ratio | ≥0.5 | 1.53 | ✅ Pass |

**Note**: M15 timeframe (in-progress download) expected to pass all objectives

---

## 🤖 Atlas GIC Integration Summary

### What Was Added
✅ **JANUS** — Dynamic cohort weighting  
✅ **Mirofish** — Training framework (5 modules)  
✅ **4-Layer Architecture** — Macro → Sectors → Superinvestors → CIO  
✅ **Autoresearch** — Self-improving prompt system  
✅ **4 Agent Examples** — CIO, Macro, Sector, Superinvestor  
✅ **Complete Documentation** — 1,025 lines (architecture + theory)  

### Integration Points with Trading Lab
- **Backtest Results** → Feed top V1-V9 strategies into JANUS
- **Daily Scoring** → Mirofish trains on realized outcomes
- **Autoresearch** → Prompt improvements merge if Sharpe improves
- **Final Signal** → Blended weights from JANUS → MT5 EA

### Start Using Atlas
```bash
cd /workspaces/trading-lab
python atlas-gic/src/janus.py
# (After backtest results available)
```

---

## 🛠️ MT5 Options (When Ready)

### Option 1: Python API (Windows with MT5)
```bash
python mt5/export_history.py
# Exports 10yr M15 → parquet with auto-resume
```

### Option 2: CSV Export + Conversion (Any OS)
```bash
# On Windows MT5: Ctrl+H → XAUUSD M15 → Export
# Then upload CSV and run:
python mt5/import_csv.py XAUUSD_M15.csv
```

### Option 3: Dukascopy Download (Current)
```bash
# Already running, auto-resumes on interruption
tail -f /workspaces/trading-lab/data/download.log
```

### Deploy EA v4 to MT5
```
1. Copy: mt5/EA_XAUUSD_GoldVolumeFusionElite_v4_M15.mq5
2. Paste: C:\Users\[User]\AppData\Roaming\MetaTrader 5\MQL5\Experts\
3. Compile in MetaEditor
4. Run in Strategy Tester with M15 data
```

---

## 📚 Quick Links

| Document | Purpose | Lines |
|----------|---------|-------|
| [ATLAS_GIC_INTEGRATION.md](./ATLAS_GIC_INTEGRATION.md) | Integration guide + data flows | 278 |
| [atlas-gic/README.md](./atlas-gic/README.md) | Atlas framework overview | 219 |
| [atlas-gic/architecture/overview.md](./atlas-gic/architecture/overview.md) | System architecture | 102 |
| [README.md](./README.md) | Main repo guide | ? |
| [configs/objectives.yaml](./configs/objectives.yaml) | Performance targets | ~20 |

---

## 🔑 Key Commands

### Start Download (if needed)
```bash
python src/download_data.py > data/download.log 2>&1 &
```

### Start Watcher (if needed)
```bash
python src/run_when_ready.py &
```

### Manual Backtest Run
```bash
python src/backtest_full.py
# Output: results/backtest_full_results.csv + results/backtest_full_params.json
```

### Check All Running Processes
```bash
ps aux | grep -E "download_data|run_when_ready|backtest_full"
```

### View All Errors
```bash
get_errors /workspaces/trading-lab/src
```

---

## ⏱️ Timeline

| Time | Event | Status |
|------|-------|--------|
| T+0h | Session started, clone atlas-gic | ✅ Done |
| T+2h | Backtest engine created (63 combos) | ✅ Done |
| T+4h | Download reached 39% | ✅ In progress |
| T+5.5h | Atlas GIC fully integrated (20 files) | ✅ Done |
| T+6h | Report + Quick Reference created | ✅ Done |
| T+7.5h | Download completes (~1.6h from now) | ⏳ Pending |
| T+8.5h | 63 backtests complete (~45 min) | ⏳ Pending |
| T+9h | Manual review + strategy selection | ⏳ Pending |

---

## 🚨 Troubleshooting

### If Download Stops
```bash
# It will resume automatically from last checkpoint
# Check logs:
tail -50 /workspaces/trading-lab/data/download.log
```

### If Backtest Doesn't Auto-Trigger
```bash
# Check if parquet exists and is >10MB:
ls -lh /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
# If size <10MB, download still running
# If size >10MB, manually run:
python /workspaces/trading-lab/src/backtest_full.py
```

### If Atlas Import Fails
```bash
# Verify files copied correctly:
ls -la /workspaces/trading-lab/atlas-gic/src/
# Should show: janus.py, mirofish/, README.md
```

---

## 📞 Session Support

**Questions about:**
- **Download/Data**: Check `data/download.log` or `data/dukascopy/` folder
- **Backtest Results**: Check `results/backtest_full_results.csv` (after completion)
- **Atlas Integration**: Read `ATLAS_GIC_INTEGRATION.md` (278 lines)
- **MT5 Deployment**: See `mt5/README.md` or `ATLAS_GIC_INTEGRATION.md` section 3

---

**Last Updated**: May 6, 2026, 17:21 UTC  
**Repo**: /workspaces/trading-lab  
**Status**: All systems autonomous (no manual intervention needed)
