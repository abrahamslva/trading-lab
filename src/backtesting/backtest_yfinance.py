"""
src/backtest_yfinance.py — Backtest rápido con yFinance data
=============================================================
Usa datos GC=F descargados recientemente.
9 estrategias × 7 timeframes = 63 combinaciones.
Ordena resultados por RENDIMIENTO MENSUAL DESC.
"""
import warnings
warnings.filterwarnings('ignore')
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Datos
DATA_FILE = Path("data/dukascopy/XAUUSD_15min_yfinance.parquet")
OUT_CSV = Path("results/backtest_yfinance_results.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    print(f"ERROR: {DATA_FILE} no existe. Ejecuta primero:")
    print("  python src/download_yfinance.py")
    sys.exit(1)

print("=" * 70)
print("  BACKTEST ENGINE | yFinance GC=F | 9 Strategies × 7 Timeframes")
print("=" * 70)

# Cargar datos
df = pd.read_parquet(DATA_FILE)
print(f"\n✓ Datos cargados: {len(df):,} barras M15 | {df.index[0]} → {df.index[-1]}\n")

# Estrategias (9 variantes)
STRATEGIES = {
    "V1": {"fast": 12, "slow": 26},
    "V2": {"fast": 10, "slow": 20},
    "V3": {"fast": 20, "slow": 50},
    "V4": {"fast": 5, "slow": 15},
    "V5": {"fast": 15, "slow": 35},
    "V6": {"fast": 8, "slow": 21},
    "V7": {"fast": 25, "slow": 75},
    "V8": {"fast": 13, "slow": 34},
    "V9": {"fast": 18, "slow": 55},
}

# Timeframes (7)
TIMEFRAMES = ["15min", "30min", "1h", "2h", "3h", "4h", "1d"]

# Resample map (pandas 2.0+: min, h, d en lugar de T, H, D)
RESAMPLE_MAP = {
    "15min": "15min",
    "30min": "30min",
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
    "1d": "1d",
}

# Objetivos
OBJECTIVES = {
    "min_monthly_return": 1.5,       # %
    "max_drawdown": 9.0,             # %
    "min_trades_per_month": 7,
    "max_daily_loss": 5.0,          # %
}

def calculate_ma_cross(data, fast, slow):
    """MA-Cross strategy: buy cuando fast > slow, sell cuando fast < slow."""
    data = data.copy()
    data["fast_ma"] = data["close"].rolling(window=fast).mean()
    data["slow_ma"] = data["close"].rolling(window=slow).mean()
    data["signal"] = 0
    data.loc[data["fast_ma"] > data["slow_ma"], "signal"] = 1
    data.loc[data["fast_ma"] <= data["slow_ma"], "signal"] = -1
    data["position"] = data["signal"].shift(1).fillna(0)
    return data

def backtest_strategy(data, fast, slow, initial_cash=100000):
    """Ejecuta backtest y retorna métricas."""
    data = calculate_ma_cross(data, fast, slow)
    
    if data["position"].sum() == 0:  # Sin trades
        return None
    
    # Simulación simple
    data["returns"] = data["close"].pct_change()
    data["pnl"] = data["position"] * data["returns"]
    data["cumulative_pnl"] = (1 + data["pnl"]).cumprod()
    data["equity"] = initial_cash * data["cumulative_pnl"]
    
    # Métricas
    total_return = (data["cumulative_pnl"].iloc[-1] - 1) * 100
    num_trades = (data["position"] != data["position"].shift()).sum() // 2
    if num_trades == 0:
        return None
    
    # Retorno mensual
    data["year_month"] = data.index.to_period("M")
    monthly_returns = data.groupby("year_month")["pnl"].sum() * 100
    monthly_avg = monthly_returns.mean()
    
    # Drawdown
    cummax = data["equity"].cummax()
    drawdown = (data["equity"] - cummax) / cummax * 100
    max_dd = drawdown.min()
    
    # Daily loss
    daily_pnl = data.groupby(data.index.date)["pnl"].sum() * 100
    worst_day = daily_pnl.min()
    
    return {
        "total_return": total_return,
        "monthly_return": monthly_avg,
        "max_drawdown": max_dd,
        "num_trades": num_trades,
        "trades_per_month": num_trades / (len(data) / (252 * 24 * 4)),
        "worst_day": worst_day,
        "win_rate": (data[data["pnl"] > 0].shape[0] / len(data)) * 100 if len(data) > 0 else 0,
    }

# Ejecutar backtests
results = []

print("  Backtesting 63 combinaciones...\n")

for strat_name, params in STRATEGIES.items():
    for tf in TIMEFRAMES:
        # Resample
        resampled = df.resample(RESAMPLE_MAP[tf]).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()
        
        # Backtest
        metrics = backtest_strategy(resampled, params["fast"], params["slow"])
        
        if metrics is None:
            continue
        
        # Check objetivos
        passed = (
            metrics["monthly_return"] >= OBJECTIVES["min_monthly_return"] and
            metrics["max_drawdown"] >= -OBJECTIVES["max_drawdown"] and
            metrics["trades_per_month"] >= OBJECTIVES["min_trades_per_month"] and
            metrics["worst_day"] >= -OBJECTIVES["max_daily_loss"]
        )
        
        result = {
            "Strategy": strat_name,
            "Timeframe": tf,
            "Monthly Return %": round(metrics["monthly_return"], 2),
            "Total Return %": round(metrics["total_return"], 2),
            "Max Drawdown %": round(metrics["max_drawdown"], 2),
            "Trades": int(metrics["num_trades"]),
            "Trades/Month": round(metrics["trades_per_month"], 1),
            "Win Rate %": round(metrics["win_rate"], 1),
            "Worst Day %": round(metrics["worst_day"], 2),
            "Passed": "✓" if passed else "✗",
        }
        results.append(result)
        
        status = "✓" if passed else "✗"
        print(f"{status} {strat_name:3} {tf:6} | Ret: {metrics['monthly_return']:6.2f}% "
              f"| DD: {metrics['max_drawdown']:6.2f}% | Trades: {metrics['num_trades']:3}")

# Ordenar por rendimiento mensual DESC
results_df = pd.DataFrame(results)
results_df = results_df.sort_values("Monthly Return %", ascending=False)

# Guardar
results_df.to_csv(OUT_CSV, index=False)

print(f"\n{'='*70}")
print(f"✓ RESULTADOS GUARDADOS: {OUT_CSV}")
print(f"{'='*70}\n")

# Mostrar top 10
print("TOP 10 ESTRATEGIAS (por Rendimiento Mensual):\n")
print(results_df[["Strategy", "Timeframe", "Monthly Return %", "Total Return %", "Max Drawdown %", "Trades/Month", "Passed"]].head(10).to_string(index=False))

# Resumen
passed_count = (results_df["Passed"] == "✓").sum()
print(f"\n{'='*70}")
print(f"📊 RESUMEN: {len(results_df)}/63 combinaciones | {passed_count} cumplen objetivos")
print(f"{'='*70}\n")
