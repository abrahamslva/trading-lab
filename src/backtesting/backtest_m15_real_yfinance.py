"""
Backtesting REAL con datos M15 actuales de yFinance
====================================================
Datos: 1,998 barras (30 días recientes: 2026-04-06 → 2026-05-06)
Estrategias: 9 variantes MA-Cross
Timeframes: 15min, 30min, 1h, 2h, 3h, 4h, 1d
Resultado: Ordenado por RENDIMIENTO MENSUAL DESC (datos reales verificables)
"""
import warnings
warnings.filterwarnings('ignore')
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Datos
DATA_FILE = Path("data/dukascopy/XAUUSD_15min_yfinance_real.parquet")
OUT_CSV = Path("results/backtest_m15_real_yfinance.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    print(f"ERROR: {DATA_FILE} no existe")
    sys.exit(1)

print("=" * 80)
print("  BACKTEST M15 REAL | 9 Strategies × 7 Timeframes")
print("  Datos: yFinance (2026-04-06 → 2026-05-06, 1,998 barras = 30 días)")
print("=" * 80)

# Cargar datos M15 REALES
df = pd.read_parquet(DATA_FILE)
df.columns = [c.lower() for c in df.columns]
print(f"\n✓ Datos yFinance M15 cargados:")
print(f"  Barras: {len(df):,}")
print(f"  Período: {df.index[0].date()} → {df.index[-1].date()}")
print(f"  Rango: ${df['close'].min():.2f} → ${df['close'].max():.2f}")
print(f"  Volatilidad: {df['close'].pct_change().std()*100:.2f}%\n")

# Estrategias (9)
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
RESAMPLE_MAP = {
    "15min": "15min",
    "30min": "30min",
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
    "1d": "1d",
}

# Objetivos (para referencia)
OBJECTIVES = {
    "min_monthly_return": 1.5,
    "max_drawdown": 9.0,
    "min_trades_per_month": 7,
    "max_daily_loss": 5.0,
}

def calculate_ma_cross(data, fast, slow):
    """MA-Cross: buy fast>slow, sell fast<=slow."""
    data = data.copy()
    data["fast_ma"] = data["close"].rolling(window=fast, min_periods=1).mean()
    data["slow_ma"] = data["close"].rolling(window=slow, min_periods=1).mean()
    data["signal"] = 0
    data.loc[data["fast_ma"] > data["slow_ma"], "signal"] = 1
    data.loc[data["fast_ma"] <= data["slow_ma"], "signal"] = -1
    data["position"] = data["signal"].shift(1).fillna(0)
    return data

def backtest_strategy(data, fast, slow, initial_cash=100000):
    """Ejecuta backtest y retorna métricas."""
    if len(data) < max(fast, slow) + 5:
        return None
    
    data = calculate_ma_cross(data, fast, slow)
    
    # Contar trades reales
    trades = (data["position"] != data["position"].shift()).sum() // 2
    if trades < 1:
        return None
    
    # PnL
    data["returns"] = data["close"].pct_change()
    data["pnl"] = data["position"] * data["returns"]
    data["cumulative_pnl"] = (1 + data["pnl"]).cumprod()
    data["equity"] = initial_cash * data["cumulative_pnl"]
    
    # Retorno total
    total_return = (data["cumulative_pnl"].iloc[-1] - 1) * 100
    
    # Retorno por período (estimado a mes = 30 días)
    # Con 30 días de datos, es valor directo
    daily_pnl = data.groupby(data.index.date)["pnl"].sum() * 100
    num_days = len(daily_pnl)
    if num_days >= 1:
        monthly_return = (daily_pnl.mean()) * 30  # Proyectado a mes
    else:
        monthly_return = total_return
    
    # Drawdown
    cummax = data["equity"].cummax()
    drawdown = (data["equity"] - cummax) / cummax * 100
    max_dd = drawdown.min()
    
    # Daily loss
    worst_day = daily_pnl.min()
    
    # Trades por mes
    trades_per_month = (trades / num_days) * 30 if num_days > 0 else 0
    
    # Win rate
    winning_trades = (data[data["pnl"] > 0].shape[0])
    total_trades_count = len(data)
    win_rate = (winning_trades / total_trades_count * 100) if total_trades_count > 0 else 0
    
    return {
        "total_return": total_return,
        "monthly_return": monthly_return,
        "max_drawdown": max_dd,
        "num_trades": trades,
        "trades_per_month": trades_per_month,
        "worst_day": worst_day,
        "win_rate": win_rate,
        "num_days": num_days,
    }

# BACKTEST: 63 combinaciones
results = []
print(f"  Backtesting 63 combinaciones (30 días reales)...\n")

for strat_name, params in STRATEGIES.items():
    for tf in TIMEFRAMES:
        # Resample si es necesario
        if tf == "15min":
            resampled = df.copy()
        else:
            resampled = df.resample(RESAMPLE_MAP[tf]).agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna()
        
        if len(resampled) < max(params["fast"], params["slow"]) + 5:
            continue
        
        # Backtest
        metrics = backtest_strategy(resampled, params["fast"], params["slow"])
        
        if metrics is None:
            continue
        
        # Evaluar objetivos
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
            "Trades/Month": round(metrics["trades_per_month"], 2),
            "Win Rate %": round(metrics["win_rate"], 1),
            "Worst Day %": round(metrics["worst_day"], 2),
            "Passed": "✓" if passed else "✗",
        }
        results.append(result)
        
        status = "✓" if passed else "✗"
        print(f"{status} {strat_name:3} {tf:6} | Monthly: {metrics['monthly_return']:7.2f}% | "
              f"Total: {metrics['total_return']:7.2f}% | Trades: {metrics['num_trades']:2.0f}")

# Ordenar por rendimiento mensual DESC
results_df = pd.DataFrame(results)
if len(results_df) > 0:
    results_df = results_df.sort_values("Monthly Return %", ascending=False)
    
    # Guardar
    results_df.to_csv(OUT_CSV, index=False)
    
    print(f"\n{'='*80}")
    print(f"✓ RESULTADOS GUARDADOS: {OUT_CSV}")
    print(f"{'='*80}\n")
    
    # TOP 15
    print("TOP 10 ESTRATEGIAS (por Rendimiento Mensual):\n")
    top_cols = ["Strategy", "Timeframe", "Monthly Return %", "Total Return %", "Max Drawdown %", "Trades", "Passed"]
    print(results_df[top_cols].head(10).to_string(index=False))
    
    # Resumen
    passed_count = (results_df["Passed"] == "✓").sum()
    total_combos = len(results_df)
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN (30 DÍAS REALES DE yFINANCE)")
    print(f"  Total combinaciones: {total_combos}")
    print(f"  Cumplen objetivos: {passed_count}/{total_combos}")
    if total_combos > 0:
        print(f"  Mejor rendimiento: {results_df['Monthly Return %'].max():.2f}% mensual")
        print(f"  Peor rendimiento: {results_df['Monthly Return %'].min():.2f}% mensual")
    print(f"  ⚠️  Datos: 30 días solo = proyección estimada a mes")
    print(f"{'='*80}\n")
else:
    print(f"\n❌ Sin resultados válidos para graficar")
