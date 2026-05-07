#!/usr/bin/env python3
"""
Integración de GuardRail - Validación de Riesgo
Valida trades antes de ejecutar basado en objetivos y límites de riesgo.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# GUARDRAIL IMPLEMENTATION
# ============================================================================

class RiskGuardRail:
    """
    Sistema de validación de riesgo antes de ejecutar trades.
    Basado en: external_repos/guardrail/
    """
    
    def __init__(self,
                 max_monthly_dd: float = 9.0,      # % max drawdown
                 max_daily_loss: float = 5.0,      # % max loss por día
                 max_trades_day: int = 3,          # máximo trades por día
                 min_win_rate: float = 45.0,       # % mínimo win rate
                 max_position_size: float = 5.0,   # % máximo del capital
                 risk_reward_ratio: float = 1.5    # RR mínimo
    ):
        self.max_monthly_dd = max_monthly_dd
        self.max_daily_loss = max_daily_loss
        self.max_trades_day = max_trades_day
        self.min_win_rate = min_win_rate
        self.max_position_size = max_position_size
        self.risk_reward_ratio = risk_reward_ratio
        
        self.daily_pnl = {}
        self.daily_trade_count = {}
        self.equity_curve = 1.0
        self.trades_log = []
    
    def validate_trade(self,
                      entry_price: float,
                      stop_loss: float,
                      take_profit: float,
                      position_size: float,
                      current_date: str,
                      current_equity: float = 100.0) -> Tuple[bool, str]:
        """
        Validar si un trade cumple con límites de riesgo.
        
        Returns:
            (is_valid, reason)
        """
        
        # 1. Verificar RR ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return False, "Risk = 0 (SL == Entry)"
        
        rr = reward / risk
        if rr < self.risk_reward_ratio:
            return False, f"RR ratio {rr:.2f} < {self.risk_reward_ratio}"
        
        # 2. Verificar posición size
        if position_size > self.max_position_size:
            return False, f"Position {position_size:.1f}% > {self.max_position_size:.1f}% max"
        
        # 3. Verificar trades por día
        trades_today = self.daily_trade_count.get(current_date, 0)
        if trades_today >= self.max_trades_day:
            return False, f"Ya {trades_today} trades hoy (max: {self.max_trades_day})"
        
        # 4. Verificar max loss del día
        daily_loss = self.daily_pnl.get(current_date, 0)
        max_possible_loss = position_size * (risk / entry_price) * current_equity
        
        if daily_loss + max_possible_loss > self.max_daily_loss:
            return False, f"Daily loss {daily_loss:.2f}% + {max_possible_loss:.2f}% > {self.max_daily_loss}% limit"
        
        return True, "✓ Trade válido"
    
    def record_trade(self,
                    trade_result: float,  # % return
                    current_date: str,
                    entry_price: float,
                    exit_price: float):
        """
        Registrar resultado de trade.
        """
        
        # Actualizar PnL diario
        self.daily_pnl[current_date] = self.daily_pnl.get(current_date, 0) + trade_result
        
        # Actualizar contador de trades
        self.daily_trade_count[current_date] = self.daily_trade_count.get(current_date, 0) + 1
        
        # Actualizar equity
        self.equity_curve *= (1 + trade_result / 100)
        
        # Log
        self.trades_log.append({
            'date': current_date,
            'entry': entry_price,
            'exit': exit_price,
            'pnl_pct': trade_result,
            'equity': self.equity_curve
        })
    
    def get_daily_summary(self) -> pd.DataFrame:
        """
        Resumen de trades por día.
        """
        data = []
        for date in sorted(self.daily_pnl.keys()):
            data.append({
                'Date': date,
                'Daily PnL %': round(self.daily_pnl[date], 2),
                'Trades': self.daily_trade_count.get(date, 0),
                'Equity': round(self.equity_curve, 2)
            })
        
        return pd.DataFrame(data)


# ============================================================================
# ANÁLISIS DE RIESGO EN BACKTESTING
# ============================================================================

def analyze_risk_in_backtest(
    backtest_results: pd.DataFrame,
    guardrail: RiskGuardRail
) -> Dict:
    """
    Analizar riesgo en resultados de backtesting.
    """
    
    # Estrategias que pasarían validación
    valid_strategies = []
    
    for _, row in backtest_results.iterrows():
        monthly_return = row['Monthly Return %']
        max_dd = abs(row['Max Drawdown %'])
        win_rate = row['Win Rate %']
        trades = row['Trades']
        
        # Aplicar criterios de guardrail
        passes_dd = max_dd <= guardrail.max_monthly_dd
        passes_wr = win_rate >= guardrail.min_win_rate
        
        if passes_dd and passes_wr:
            valid_strategies.append({
                'Strategy': row['Strategy'],
                'Timeframe': row['Timeframe'],
                'Monthly Return %': monthly_return,
                'Max DD %': max_dd,
                'Win Rate %': win_rate,
                'RiskScore': (max_dd / guardrail.max_monthly_dd) + (1 - win_rate/100)
            })
    
    return {
        'total_combinations': len(backtest_results),
        'passed_guardrail': len(valid_strategies),
        'pass_rate': len(valid_strategies) / len(backtest_results) * 100,
        'valid_strategies': pd.DataFrame(valid_strategies)
    }


# ============================================================================
# VALIDAR PRÓXIMOS TRADES EN VIVO
# ============================================================================

def create_trade_validator(
    historical_backtest: pd.DataFrame,
    current_strategy: str,
    current_timeframe: str
) -> RiskGuardRail:
    """
    Crear validador basado en performance histórica.
    """
    
    # Encontrar performance histórica de la estrategia
    hist = historical_backtest[
        (historical_backtest['Strategy'] == current_strategy) &
        (historical_backtest['Timeframe'] == current_timeframe)
    ]
    
    if hist.empty:
        # Usar valores por defecto conservadores
        return RiskGuardRail(
            max_monthly_dd=9.0,
            max_daily_loss=5.0,
            max_position_size=2.0,
            min_win_rate=50.0
        )
    
    hist = hist.iloc[0]
    
    # Ajustar límites basado en performance real
    actual_dd = abs(hist['Max Drawdown %'])
    actual_wr = hist['Win Rate %']
    
    return RiskGuardRail(
        max_monthly_dd=min(actual_dd * 1.2, 12.0),  # 20% buffer
        max_daily_loss=5.0,
        max_position_size=2.0,
        min_win_rate=max(actual_wr - 2, 45.0)  # -2% buffer
    )


# ============================================================================
# MAIN - APLICAR GUARDRAIL A RESULTADOS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*120)
    print("🛡️  GUARDRAIL - Risk Validation System")
    print("="*120)
    
    # Cargar resultados de backtesting
    results_file = Path("results/backtest_all_strategies_2016_2024.csv")
    
    if not results_file.exists():
        print(f"❌ Archivo no encontrado: {results_file}")
        print("Ejecuta primero: python3 src/backtest_all_strategies_2016_2024.py")
        import sys
        sys.exit(1)
    
    df_results = pd.read_csv(results_file)
    print(f"\n✓ {len(df_results)} combinaciones cargadas")
    
    # Crear guardrail
    guardrail = RiskGuardRail(
        max_monthly_dd=9.0,      # Objetivo
        max_daily_loss=5.0,      # Objetivo
        max_trades_day=3,
        min_win_rate=50.0,
        max_position_size=2.0,
        risk_reward_ratio=1.5
    )
    
    print(f"\n🔍 Límites de Guardrail:")
    print(f"  Max Monthly DD: {guardrail.max_monthly_dd}%")
    print(f"  Max Daily Loss: {guardrail.max_daily_loss}%")
    print(f"  Min Win Rate: {guardrail.min_win_rate}%")
    print(f"  Min RR Ratio: {guardrail.risk_reward_ratio}")
    
    # Analizar riesgo
    risk_analysis = analyze_risk_in_backtest(df_results, guardrail)
    
    print(f"\n📊 RESULTADOS:")
    print(f"{'='*120}")
    print(f"Total combinaciones: {risk_analysis['total_combinations']}")
    print(f"Pasan validación: {risk_analysis['passed_guardrail']}")
    print(f"Tasa de paso: {risk_analysis['pass_rate']:.1f}%")
    
    if len(risk_analysis['valid_strategies']) > 0:
        print(f"\n✓ ESTRATEGIAS VÁLIDAS SEGÚN GUARDRAIL:")
        print(f"{'-'*120}")
        
        valid_df = risk_analysis['valid_strategies'].sort_values('RiskScore')
        for idx, row in valid_df.head(10).iterrows():
            print(f"  {row['Strategy']:3s} {row['Timeframe']:7s} | "
                  f"Monthly: {row['Monthly Return %']:6.2f}% | "
                  f"Max DD: {row['Max DD %']:6.2f}% | "
                  f"WR: {row['Win Rate %']:5.1f}% | "
                  f"Risk Score: {row['RiskScore']:.2f}")
        
        # Guardar
        valid_df.to_csv("results/guardrail_validated_strategies.csv", index=False)
        print(f"\n✓ Guardado: results/guardrail_validated_strategies.csv")
    else:
        print(f"\n⚠️  NINGUNA estrategia pasa los límites actuales")
        print(f"Necesitarás:")
        print(f"  - Mejorar win rate actual (~50%) a 52%+")
        print(f"  - Reducir drawdown máximo de -34% actual a -9% objetivo")
        print(f"  - O ajustar límites de guardrail según tolerancia de riesgo")
    
    print(f"\n{'='*120}\n")

