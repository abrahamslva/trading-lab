"""
Backtesting V3 2016-2024 en múltiples timeframes
================================================
Datos: 127,050 barras M15 (2016-01-04 → 2024-06-28)
Estrategia: V3 (fast=20, slow=50) MA-Cross
Timeframes: 15min, 30min, 1h, 2h, 3h, 4h
Resultado: CSV ordenado por timeframe y métricas
"""
import warnings
warnings.filterwarnings('ignore')
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Datos
DATA_FILE = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
OUT_CSV = Path("results/backtest_v3_2016_2024_multiframe.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

if not DATA_FILE.exists():
    print(f"ERROR: {DATA_FILE} no existe")
    sys.exit(1)

print("=" * 85)
print("  BACKTESTING V3 2016-2024 | Múltiples Timeframes")
print("=" * 85)

# Cargar datos
df = pd.read_parquet(DATA_FILE)
df.columns = [c.lower() for c in df.columns]

print(f"\n✓ Datos cargados:")
print(f"  Barras: {len(df):,}")
print(f"  Período: {df.index[0].date()} → {df.index[-1].date()}")
print(f"  Años: {(df.index[-1] - df.index[0]).days / 365.25:.1f}")
print(f"  Rango precio: ${df['close'].min():.2f} - ${df['close'].max():.2f}\n")

# V3 Parameters
STRATEGY = {"fast": 20, "slow": 50}

# Timeframes
TIMEFRAMES = ["15min", "30min", "1h", "2h", "3h", "4h"]
RESAMPLE_MAP = {
    "15min": "15min",
    "30min": "30min",
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
}

# Objetivos para referencia
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
    if len(data) < max(fast, slow) + 10:
        return None
    
    data = calculate_ma_cross(data, fast, slow)
    
    # Contar trades reales
    trades = (data["position"] != data["position"].shift()).sum() // 2
    if trades < 2:
        return None
    
    # PnL
    data["returns"] = data["close"].pct_change()
    data["pnl"] = data["position"] * data["returns"]
    data["cumulative_pnl"] = (1 + data["pnl"]).cumprod()
    data["equity"] = initial_cash * data["cumulative_pnl"]
    
    # Retorno total
    total_return = (data["cumulative_pnl"].iloc[-1] - 1) * 100
    
    # Retorno mensual (número de meses en período)
    num_months = (data.index[-1] - data.index[0]).days / 30.44
    if num_months > 0:
        monthly_return = total_return / num_months
    else:
        monthly_return = total_return
    
    # Drawdown
    cummax = data["equity"].cummax()
    drawdown = (data["equity"] - cummax) / cummax * 100
    max_dd = drawdown.min()
    
    # Daily loss
    daily_pnl = data.groupby(data.index.date)["pnl"].sum() * 100
    worst_day = daily_pnl.min()
    
    # Trades por mes
    num_days = (data.index[-1] - data.index[0]).days
    trades_per_month = (trades / num_days) * 30 if num_days > 0 else 0
    
    # Win rate
    winning_trades = (data[data["pnl"] > 0].shape[0])
    total_trades_count = len(data)
    win_rate = (winning_trades / total_trades_count * 100) if total_trades_count > 0 else 0
    
    # Sharpe ratio (annualized)
    daily_returns = data.groupby(data.index.date)["pnl"].sum()
    if len(daily_returns) > 1:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
    else:
        sharpe = 0
    
    return {
        "total_return": total_return,
        "monthly_return": monthly_return,
        "max_drawdown": max_dd,
        "num_trades": trades,
        "trades_per_month": trades_per_month,
        "worst_day": worst_day,
        "win_rate": win_rate,
        "sharpe": sharpe,
        "num_days": num_days,
    }

# BACKTEST: 6 timeframes
results = []
print(f"  Backtesting V3 en 6 timeframes...\n")

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
    
    if len(resampled) < max(STRATEGY["fast"], STRATEGY["slow"]) + 10:
        print(f"✗ {tf:6} | Barras insuficientes ({len(resampled)} < 60)")
        continue
    
    # Backtest
    metrics = backtest_strategy(resampled, STRATEGY["fast"], STRATEGY["slow"])
    
    if metrics is None:
        print(f"✗ {tf:6} | No hay suficientes trades")
        continue
    
    # Evaluar objetivos
    passed = (
        metrics["monthly_return"] >= OBJECTIVES["min_monthly_return"] and
        metrics["max_drawdown"] >= -OBJECTIVES["max_drawdown"] and
        metrics["trades_per_month"] >= OBJECTIVES["min_trades_per_month"] and
        metrics["worst_day"] >= -OBJECTIVES["max_daily_loss"]
    )
    
    result = {
        "Timeframe": tf,
        "Monthly Return %": round(metrics["monthly_return"], 2),
        "Total Return %": round(metrics["total_return"], 2),
        "Max Drawdown %": round(metrics["max_drawdown"], 2),
        "Trades": int(metrics["num_trades"]),
        "Trades/Month": round(metrics["trades_per_month"], 2),
        "Win Rate %": round(metrics["win_rate"], 1),
        "Worst Day %": round(metrics["worst_day"], 2),
        "Sharpe Ratio": round(metrics["sharpe"], 2),
        "Days": int(metrics["num_days"]),
        "Passed": "✓" if passed else "✗",
    }
    results.append(result)
    
    status = "✓" if passed else "✗"
    print(f"{status} {tf:6} | Monthly: {metrics['monthly_return']:7.2f}% | Total: {metrics['total_return']:7.2f}% | "
          f"DD: {metrics['max_drawdown']:6.2f}% | Trades: {metrics['num_trades']:3.0f} | Sharpe: {metrics['sharpe']:5.2f}")

# Crear DataFrame
results_df = pd.DataFrame(results)
results_df = results_df.sort_values("Monthly Return %", ascending=False)

# Guardar
results_df.to_csv(OUT_CSV, index=False)

print(f"\n{'='*85}")
print(f"✓ RESULTADOS GUARDADOS: {OUT_CSV}")
print(f"{'='*85}\n")

# Mostrar tabla completa
print("TABLA COMPLETA DE RESULTADOS:\n")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)
print(results_df.to_string(index=False))

# Resumen
print(f"\n{'='*85}")
print(f"📊 RESUMEN V3 (2016-2024, 8 años)")
print(f"{'='*85}")
print(f"  Timeframes probados: {len(results)}/6")
print(f"  Cumplen objetivos: {(results_df['Passed'] == '✓').sum()}/{len(results_df)}")
print(f"  Mejor rendimiento: {results_df['Monthly Return %'].max():.2f}% mensual ({results_df.iloc[0]['Timeframe']})")
print(f"  Peor rendimiento: {results_df['Monthly Return %'].min():.2f}% mensual ({results_df.iloc[-1]['Timeframe']})")
print(f"  Sharpe promedio: {results_df['Sharpe Ratio'].mean():.2f}")
print(f"  Max DD promedio: {results_df['Max Drawdown %'].mean():.2f}%")
print(f"  Win Rate promedio: {results_df['Win Rate %'].mean():.1f}%")
print(f"{'='*85}\n")

# Recomendación
print("🎯 RECOMENDACIÓN:")
best = results_df.iloc[0]
print(f"  Mejor timeframe: {best['Timeframe']}")
print(f"    - Retorno mensual: {best['Monthly Return %']:.2f}%")
print(f"    - Max drawdown: {best['Max Drawdown %']:.2f}%")
print(f"    - Trades/mes: {best['Trades/Month']:.1f}")
print(f"    - Sharpe: {best['Sharpe Ratio']:.2f}")
print(f"\n")
