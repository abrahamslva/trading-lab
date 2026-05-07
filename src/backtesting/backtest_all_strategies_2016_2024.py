#!/usr/bin/env python3
"""
Backtesting ALL Strategies (V1-V9) | 2016-2024 | 6 Timeframes
============================================================================
Compara rendimiento de 9 estrategias MA-Cross sobre 127,050 barras M15
en múltiples timeframes (15min, 30min, 1h, 2h, 3h, 4h).

Parámetros:
  V1: fast=12, slow=26  | V2: fast=10, slow=20  | V3: fast=20, slow=50
  V4: fast=5, slow=15   | V5: fast=15, slow=35  | V6: fast=8, slow=21
  V7: fast=25, slow=75  | V8: fast=13, slow=34  | V9: fast=18, slow=55
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

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

TIMEFRAMES = ["15min", "30min", "1h", "2h", "3h", "4h"]

RESAMPLE_MAP = {
    "15min": "15min",
    "30min": "30min",
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
}

DATA_FILE = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
OUT_CSV = Path("results/backtest_all_strategies_2016_2026.csv")

# Objectives from requirements
MONTHLY_RETURN_TARGET = 1.5  # %
MAX_DD_TARGET = 9.0  # %
TRADES_PER_MONTH_TARGET = 7.0
DAILY_LOSS_TARGET = 5.0  # %

# ============================================================================
# BACKTESTING FUNCTIONS
# ============================================================================


def calculate_ma_cross(data: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    """Generate buy/sell signals from MA crossover."""
    fast_ma = data["close"].rolling(window=fast).mean()
    slow_ma = data["close"].rolling(window=slow).mean()
    signal = pd.Series(0, index=data.index, dtype=float)
    signal[fast_ma > slow_ma] = 1  # BUY
    signal[fast_ma <= slow_ma] = -1  # SELL
    return signal


def backtest_strategy(
    data: pd.DataFrame, fast: int, slow: int
) -> Dict[str, float]:
    """Full backtesting with PnL calculation and risk metrics."""

    # Generate signals and positions
    signal = calculate_ma_cross(data, fast, slow)
    position = signal.shift(1).fillna(0)

    # Calculate returns
    returns = data["close"].pct_change()
    pnl = position * returns

    # Calculate metrics
    cumulative_pnl = (1 + pnl).cumprod() - 1
    total_return = cumulative_pnl.iloc[-1] * 100

    # Monthly return (total return / months)
    trading_days = (data.index[-1] - data.index[0]).days
    num_months = trading_days / 30.44
    monthly_return = (total_return / num_months) if num_months > 0 else 0

    # Max drawdown
    cumulative_returns = (1 + pnl).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    # Trades
    position_changes = position.diff().fillna(0)
    num_trades = (position_changes != 0).sum()
    trades_per_month = (num_trades / num_months) if num_months > 0 else 0

    # Win rate
    winning_days = (pnl > 0).sum()
    total_days = (pnl != 0).sum()
    win_rate = (winning_days / total_days * 100) if total_days > 0 else 0

    # Worst day
    worst_day = pnl.min() * 100

    # Sharpe ratio
    sharpe = (pnl.mean() / pnl.std() * np.sqrt(252)) if pnl.std() > 0 else 0

    # Check objectives
    passed = (
        monthly_return >= MONTHLY_RETURN_TARGET
        and abs(max_drawdown) <= MAX_DD_TARGET
        and trades_per_month >= TRADES_PER_MONTH_TARGET
        and worst_day >= -DAILY_LOSS_TARGET
    )

    return {
        "monthly_return": monthly_return,
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "trades": num_trades,
        "trades_per_month": trades_per_month,
        "win_rate": win_rate,
        "worst_day": worst_day,
        "sharpe": sharpe,
        "passed": "✓" if passed else "✗",
    }


def resample_ohlc(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample M15 OHLC data to desired timeframe."""
    agg_dict = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    return data.resample(timeframe).agg(agg_dict).dropna()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "=" * 95)
    print("  BACKTESTING ALL STRATEGIES (V1-V9) | 2016-2026 | Múltiples Timeframes")
    print("=" * 95)

    # Load data
    if not DATA_FILE.exists():
        print(f"\n✗ Archivo no encontrado: {DATA_FILE}")
        return

    print(f"\n✓ Cargando datos: {DATA_FILE}")
    data = pd.read_parquet(DATA_FILE)
    data.index = pd.to_datetime(data.index)
    # Normalize column names to lowercase
    data.columns = [c.lower() for c in data.columns]

    print(f"  Barras: {len(data):,}")
    print(f"  Período: {data.index[0].date()} → {data.index[-1].date()}")
    print(f"  Años: {(data.index[-1] - data.index[0]).days / 365.25:.1f}")
    print(
        f"  Rango precio: ${data['close'].min():.2f} - ${data['close'].max():.2f}"
    )

    # Store results
    all_results = []

    # Iterate strategies and timeframes
    print(f"\n✓ Backtesting {len(STRATEGIES)} estrategias × {len(TIMEFRAMES)} timeframes (datos hasta 2026)...")
    print()

    for strategy_name, params in STRATEGIES.items():
        fast = params["fast"]
        slow = params["slow"]

        for timeframe in TIMEFRAMES:
            # Resample if needed
            if timeframe == "15min":
                tf_data = data.copy()
            else:
                tf_data = resample_ohlc(data, RESAMPLE_MAP[timeframe])

            # Backtest
            metrics = backtest_strategy(tf_data, fast, slow)
            trading_days = (tf_data.index[-1] - tf_data.index[0]).days

            result = {
                "Strategy": strategy_name,
                "Timeframe": timeframe,
                "Fast": fast,
                "Slow": slow,
                "Monthly Return %": round(metrics["monthly_return"], 2),
                "Total Return %": round(metrics["total_return"], 2),
                "Max Drawdown %": round(metrics["max_drawdown"], 2),
                "Trades": int(metrics["trades"]),
                "Trades/Month": round(metrics["trades_per_month"], 2),
                "Win Rate %": round(metrics["win_rate"], 1),
                "Worst Day %": round(metrics["worst_day"], 2),
                "Sharpe Ratio": round(metrics["sharpe"], 2),
                "Days": trading_days,
                "Passed": metrics["passed"],
            }

            all_results.append(result)

            # Print progress
            status = "✓" if metrics["passed"] == "✓" else "✗"
            print(
                f"{status} {strategy_name:3s} {timeframe:7s} | Monthly: {metrics['monthly_return']:7.2f}% | "
                f"Total: {metrics['total_return']:7.2f}% | DD: {metrics['max_drawdown']:7.2f}% | "
                f"Trades: {metrics['trades']:5.0f} | Sharpe: {metrics['sharpe']:6.2f}"
            )

    # Create DataFrame and sort
    df_results = pd.DataFrame(all_results)
    df_results_sorted = df_results.sort_values(
        by="Monthly Return %", ascending=False
    )

    # Save to CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_results_sorted.to_csv(OUT_CSV, index=False)

    print("\n" + "=" * 95)
    print(f"✓ RESULTADOS GUARDADOS: {OUT_CSV}")
    print("=" * 95)

    # Summary statistics
    passed_count = (df_results["Passed"] == "✓").sum()
    total_count = len(df_results)

    print(f"\n📊 RESUMEN GENERAL — 2016-2026 (9 Estrategias × 6 Timeframes = {total_count} combinaciones)")
    print(f"  Cumplen objetivos: {passed_count}/{total_count}")
    print(f"  Mejor rendimiento: {df_results['Monthly Return %'].max():.2f}% mensual")
    print(f"  Peor rendimiento: {df_results['Monthly Return %'].min():.2f}% mensual")
    print(f"  Sharpe promedio: {df_results['Sharpe Ratio'].mean():.2f}")

    # Top 10 combinations
    print(f"\n🏆 TOP 10 MEJORES COMBINACIONES (por Monthly Return %):")
    print("─" * 95)
    top10 = df_results_sorted.head(10)[
        [
            "Strategy",
            "Timeframe",
            "Monthly Return %",
            "Total Return %",
            "Max Drawdown %",
            "Trades",
            "Passed",
        ]
    ]
    for idx, row in top10.iterrows():
        print(
            f"  {row['Strategy']:3s} {row['Timeframe']:7s} | "
            f"Monthly: {row['Monthly Return %']:7.2f}% | "
            f"Total: {row['Total Return %']:7.2f}% | "
            f"DD: {row['Max Drawdown %']:7.2f}% | "
            f"Trades: {row['Trades']:5.0f} | {row['Passed']}"
        )

    # Performance by strategy
    print(f"\n📈 RENDIMIENTO POR ESTRATEGIA (Promedio en todos los timeframes):")
    print("─" * 95)
    by_strategy = df_results.groupby("Strategy")[
        "Monthly Return %"
    ].agg(["mean", "std", "min", "max"])
    by_strategy = by_strategy.sort_values("mean", ascending=False)
    for strategy_name in by_strategy.index:
        row = by_strategy.loc[strategy_name]
        print(
            f"  {strategy_name}: Avg={row['mean']:6.2f}% "
            f"(Min={row['min']:6.2f}%, Max={row['max']:6.2f}%, StdDev={row['std']:5.2f}%)"
        )

    # Performance by timeframe
    print(f"\n⏱️  RENDIMIENTO POR TIMEFRAME (Promedio en todas las estrategias):")
    print("─" * 95)
    by_tf = df_results.groupby("Timeframe")["Monthly Return %"].agg(
        ["mean", "std", "min", "max"]
    )
    by_tf = by_tf.reindex(TIMEFRAMES)
    for tf_name in TIMEFRAMES:
        row = by_tf.loc[tf_name]
        print(
            f"  {tf_name:7s}: Avg={row['mean']:6.2f}% "
            f"(Min={row['min']:6.2f}%, Max={row['max']:6.2f}%, StdDev={row['std']:5.2f}%)"
        )

    print("\n" + "=" * 95 + "\n")


if __name__ == "__main__":
    main()
