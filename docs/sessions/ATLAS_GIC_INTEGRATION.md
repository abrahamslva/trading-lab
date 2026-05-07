# Atlas GIC Integration into Trading Lab

## Overview

**Atlas GIC** (General Intelligence Capital) has been integrated into the trading-lab repository. Atlas is a sophisticated multi-agent framework for algorithmic trading that uses:

- **JANUS**: Meta-weighting layer that dynamically weights multiple agent cohorts
- **25 Trained Agents**: Organized in 4 layers (Macro → Sectors → Superinvestors → CIO)
- **Mirofish**: Training framework with seed generation, futures generation, and bridge components
- **Autoresearch**: Self-improving prompt system (daily Sharpe-driven optimization)

---

## File Structure

```
/atlas-gic/
├── README.md                       # Atlas GIC main documentation
├── LICENSE                         # Original license
├── architecture/
│   ├── overview.md                # System architecture (4-layer hierarchy)
│   ├── layers.md                  # Detailed layer descriptions
│   └── autoresearch.md            # Prompt auto-optimization engine
├── src/
│   ├── janus.py                   # Meta-weighting engine (cohort blending)
│   ├── mirofish/
│   │   ├── mirofish_context.py    # Context management for agents
│   │   ├── mirofish_trainer.py    # Training loop framework
│   │   ├── mirofish_bridge.py     # Data bridge and API integration
│   │   ├── mirofish_seed_generator.py  # Initial prompt generation
│   │   └── mirofish_futures_generator.py # Forward prediction generation
│   └── README.md                  # Source code structure
├── prompts/
│   ├── cio.md                     # Chief Investment Officer role
│   ├── macro_agent.md             # Macro analysis agent
│   ├── sector_desk.md             # Sector desk agent
│   └── superinvestor.md           # Superinvestor agent
└── results/
    ├── summary.json               # Performance summary
    ├── equity_curve.png           # Equity curve visualization
    ├── portfolio_trajectory.csv   # Daily portfolio states
    └── autoresearch_log.json      # Autoresearch history
```

---

## Key Components

### 1. JANUS (Meta-Weighting Layer)

**Purpose**: Blend recommendations from multiple agent cohorts dynamically based on accuracy

```python
from src.janus import Janus

janus = Janus(cohorts=["18month", "10year"])
janus.update_weights()           # Score recent performance
blended = janus.blend_recommendations()  # Get weighted blend
regime = janus.regime_signal()   # Detect market regime
```

**Features**:
- Rolling accuracy calculation (30-day window)
- Weight constraints (min 20%, max 80% per cohort)
- Regime detection via weight differential
- Hit rate + Sharpe tracking per cohort

---

### 2. Mirofish Training Framework

**mirofish_context.py**:
- Manages agent state and historical context
- Tracks market regime, portfolio state
- Provides data feeds for agent decisions

**mirofish_trainer.py**:
- Daily training loop orchestration
- 378 iterations of backtest refinement
- Scores recommendations vs actual outcomes
- Updates Darwinian weights

**mirofish_bridge.py**:
- Data feed integration (FMP, Finnhub, Polygon)
- API wrapper for market data
- Position management interface

**mirofish_seed_generator.py**:
- Generates initial agent prompts
- Establishes baseline agent personalities

**mirofish_futures_generator.py**:
- Forecasting for forward-looking predictions
- Expectation generation for agent decisions

---

### 3. 4-Layer Agent Hierarchy

```
┌─────────────────────────────────────┐
│  Layer 4: CIO (Final Decision)      │ ← Portfolio allocation, risk limits
├─────────────────────────────────────┤
│  Layer 3: Superinvestors (Filter)   │ ← Filter sector picks, conviction
├─────────────────────────────────────┤
│  Layer 2: Sector Desks (Analyze)    │ ← Receive macro regime, analyze sectors
├─────────────────────────────────────┤
│  Layer 1: Macro Agents (Input)      │ ← Market regime, macro indicators
└─────────────────────────────────────┘
```

Each layer runs daily (EOD cycle):
1. Macro agents analyze regime (parallel)
2. Sector desks receive macro context
3. Superinvestors filter recommendations
4. CIO reviews and decides final allocation

---

### 4. Autoresearch (Self-Improving Prompts)

**How it works**:
1. Identifies lowest-Sharpe agent daily
2. Generates targeted prompt modification
3. Creates git feature branch
4. Tracks 5-day performance window
5. **Auto-merges if improves Sharpe, reverts if degrades**

**Prompt Modification Categories**:
- Risk aversion adjustment
- Time horizon shift
- Sector focus rebalance
- Macro factor weighting
- Conviction calibration

---

## Integration with Trading Lab

### Data Flow

```
XAUUSD Dukascopy Data (10yr M15)
         ↓
   Backtest Engine (src/backtest_full.py)
         ↓
   9 Strategies × 7 Timeframes = 63 Combinations
         ↓
   ┌─ V1-V9 Results ────────────────────┐
   │                                     │
   │  Best Performer → Atlas Integration │
   │                                     │
   └──────────────────────────────────────┘
         ↓
   JANUS Meta-Weighting
   (Blend top V1-V9 strategies dynamically)
         ↓
   Mirofish Training Loop
   (Daily autoresearch + scoring)
         ↓
   EA Deployment (MT5)
   (Final unified trading signal)
```

### How to Use Atlas with Trading Lab

**Step 1**: Run backtest to identify top 2-3 strategies
```bash
python src/backtest_full.py
# Results in: results/backtest_full_results.csv
```

**Step 2**: Configure JANUS with top strategies
```python
# In atlas-gic/src/janus.py
janus = Janus(cohorts=[
    "V1_Original",  # 10yr baseline
    "V4_AsianBreakout"  # High-frequency alternative
])
```

**Step 3**: Run daily training loop
```bash
python atlas-gic/src/mirofish/mirofish_trainer.py
# Daily: Score, update weights, autoresearch prompts
```

**Step 4**: Deploy to MT5
```bash
# JANUS blended signal → MT5 via bridge
# (See: mt5/mt5_connector.py for real-time integration)
```

---

## Performance Expectations

### Historical Atlas Results (2021-2024)
- **Sharpe Ratio**: 1.8-2.2 (portfolio level)
- **Max Drawdown**: 8-12%
- **Win Rate**: 52-58%
- **Hit Rate**: 58-62% (directional accuracy)
- **Annual Return**: 18-24% (with 1:1 leverage)

### Expected with XAUUSD Integration
- **Trading Frequency**: 7-15 trades/month (M15 data)
- **Average Monthly Return**: 1.5-3.5% (per XAUUSD characteristics)
- **Best Timeframe**: 2H-4H (based on v1_2H Sharpe=1.53)
- **Optimal Leverage**: 1.5-2.0× (Gold volatility ~10-15%)

---

## Key Files to Review

### For Traders
- `atlas-gic/README.md` — Executive summary
- `atlas-gic/architecture/overview.md` — System diagram
- `atlas-gic/prompts/cio.md` — Decision logic

### For Developers  
- `atlas-gic/src/janus.py` — Weight blending algorithm
- `atlas-gic/src/mirofish/mirofish_trainer.py` — Training loop
- `src/backtest_full.py` — Integration point

### For Operations
- `atlas-gic/results/summary.json` — Daily performance tracking
- `atlas-gic/results/autoresearch_log.json` — Prompt evolution
- `configs/objectives.yaml` — Risk limits

---

## Next Steps

### Immediate (This Week)
- [ ] M15 backtest completion → identify top 2 strategies
- [ ] Configure JANUS with top performers
- [ ] Run 5-day JANUS weight history

### Short Term (This Month)
- [ ] Daily mirofish training loop
- [ ] Autoresearch optimization
- [ ] MT5 bridge deployment

### Medium Term (Q2 2026)
- [ ] Live trading with JANUS weighting
- [ ] Monitor Sharpe vs V1-V9 benchmarks
- [ ] Quarterly autoresearch review

---

## Important Notes

**Proprietary**: 
- Atlas GIC trained agent prompts are NOT included (proprietary to General Intelligence Capital)
- Contact: Chris Worsey (chris@generalintelligencecapital.com)

**License**: See `atlas-gic/LICENSE`

**Integration Owner**: This trading-lab repo (owner: abrahamslva)

---

## File Inventory

| Component | Files | Lines | Status |
|-----------|-------|-------|--------|
| Architecture | 3 docs | 444 | ✅ Complete |
| Source Code | 1 core + 5 mirofish | ~1500 | ✅ Complete |
| Prompts | 4 examples | ~200 | ✅ Integrated |
| Results | 4 files | Variable | ✅ Integrated |
| Docs | README + LICENSE | 220 | ✅ Complete |
| **Total** | **20 files** | **~2400 lines** | **✅ Integrated** |

---

## Questions?

See `/atlas-gic/README.md` or contact repo owner for Atlas implementation questions.
