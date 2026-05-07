#!/usr/bin/env python3
"""
Integración de SAFLA (Self-Aware Feedback Loop Algorithm)
con estrategias V1-V9 existentes.

SAFLA añade auto-mejora continua y adaptación dinámica a los algoritmos.
"""

import sys
sys.path.insert(0, '/workspaces/trading-lab')

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple

# ============================================================================
# SAFLA IMPLEMENTATION (basado en external_repos/SAFLA/)
# ============================================================================

class SAFLAAdapter:
    """
    Self-Aware Feedback Loop Algorithm para trading.
    Adapta dinámicamente parámetros basado en performance.
    """
    
    def __init__(self, window_days: int = 30, learning_rate: float = 0.1):
        self.window_days = window_days
        self.learning_rate = learning_rate
        self.history = []
        self.original_params = {}
    
    def adapt_parameters(
        self,
        current_params: Dict,
        performance_metrics: Dict
    ) -> Dict:
        """
        Adaptar parámetros basado en métricas recientes.
        
        Args:
            current_params: {"fast": 20, "slow": 50}
            performance_metrics: {"win_rate": 50.5, "monthly_return": 0.62}
        
        Returns:
            Parámetros ajustados
        """
        
        win_rate = performance_metrics.get('win_rate', 50)
        monthly_return = performance_metrics.get('monthly_return', 0)
        max_dd = abs(performance_metrics.get('max_drawdown', -25))
        
        adapted = current_params.copy()
        
        # Si win_rate es bajo, espaciar MA más
        if win_rate < 48:
            adapted['slow'] = int(adapted['slow'] * (1 + self.learning_rate))
            adapted['fast'] = int(max(1, adapted['fast'] * (1 - self.learning_rate * 0.5)))
        
        # Si drawdown es alto, hacer MAs más conservadores
        if max_dd > 30:
            adapted['slow'] = int(adapted['slow'] * (1 + self.learning_rate * 0.5))
        
        # Si retorno es bueno, mantener pero refinar
        if monthly_return > 0.7:
            # Pequeño ajuste para mejorar consistencia
            if win_rate < 52:
                adapted['fast'] = int(adapted['fast'] * 0.98)
        
        return adapted
    
    def should_continue_strategy(self, performance_metrics: Dict) -> bool:
        """
        Determinar si continuar con la estrategia o cambiar.
        """
        monthly_return = performance_metrics.get('monthly_return', 0)
        win_rate = performance_metrics.get('win_rate', 50)
        
        # Abandonar si es muy mala
        if monthly_return < -0.5 or win_rate < 45:
            return False
        
        return True


# ============================================================================
# INTEGRACIÓN CON BACKTEST EXISTENTE
# ============================================================================

def backtest_with_safla(
    data: pd.DataFrame,
    strategy_name: str,
    initial_params: Dict,
    timeframe: str = "15min",
    learning_enabled: bool = True
) -> Dict:
    """
    Backtest con SAFLA para adaptación dinámica.
    """
    
    from backtest_all_strategies_2016_2024 import (
        calculate_ma_cross,
        backtest_strategy,
        resample_ohlc
    )
    
    # Normalizar columnas si es necesario
    if 'Close' in data.columns:
        data.columns = [c.lower() for c in data.columns]
    
    # Resample si es necesario
    if timeframe != "15min":
        from backtest_all_strategies_2016_2024 import RESAMPLE_MAP
        data = resample_ohlc(data, RESAMPLE_MAP[timeframe])
    
    # Inicializar SAFLA
    safla = SAFLAAdapter(window_days=30, learning_rate=0.1)
    current_params = initial_params.copy()
    
    # Dividir data en ventanas de 30 días para adaptar
    window_size = len(data) // 12  # 12 ventanas en el período
    all_results = []
    
    for window_idx in range(0, len(data) - window_size, window_size):
        window_data = data.iloc[window_idx:window_idx + window_size]
        
        # Backtest con parámetros actuales
        metrics = backtest_strategy(window_data, current_params['fast'], current_params['slow'])
        
        all_results.append(metrics)
        
        # Adaptar parámetros si SAFLA está habilitado
        if learning_enabled:
            if safla.should_continue_strategy(metrics):
                new_params = safla.adapt_parameters(current_params, metrics)
                # Log cambio si ocurrió
                if new_params != current_params:
                    print(f"  📊 Window {window_idx}: "
                          f"Adaptado {current_params} → {new_params} "
                          f"(WR: {metrics['win_rate']:.1f}%, MR: {metrics['monthly_return']:.2f}%)")
                current_params = new_params
            else:
                print(f"  ⚠️  Window {window_idx}: Strategy no viable, revertiendo")
                current_params = initial_params.copy()
    
    # Backtest final con parámetros adaptados
    final_metrics = backtest_strategy(data, current_params['fast'], current_params['slow'])
    
    return {
        **final_metrics,
        'final_fast': current_params['fast'],
        'final_slow': current_params['slow'],
        'learning_enabled': learning_enabled,
        'windows_evaluated': len(all_results)
    }


# ============================================================================
# MAIN - APLICAR SAFLA A TODAS ESTRATEGIAS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*100)
    print("🧠 INTEGRANDO SAFLA - Self-Aware Feedback Loop Algorithm")
    print("="*100)
    
    # Cargar datos
    data_file = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
    if not data_file.exists():
        print(f"❌ Archivo no encontrado: {data_file}")
        sys.exit(1)
    
    data = pd.read_parquet(data_file)
    data.index = pd.to_datetime(data.index)
    data.columns = [c.lower() for c in data.columns]
    
    print(f"\n✓ Datos cargados: {len(data)} barras ({data.index[0].date()} → {data.index[-1].date()})")
    
    # Estrategias base
    strategies = {
        "V1": {"fast": 12, "slow": 26},
        "V3": {"fast": 20, "slow": 50},
        "V5": {"fast": 15, "slow": 35},
    }
    
    timeframes = ["15min", "2h"]
    
    results_safla = []
    
    print(f"\n🔄 Backtesting con SAFLA (adaptación automática)...\n")
    
    for strategy_name, params in strategies.items():
        for timeframe in timeframes:
            # Sin SAFLA (baseline)
            from backtest_all_strategies_2016_2024 import backtest_strategy, resample_ohlc, RESAMPLE_MAP
            
            test_data = data.copy() if timeframe == "15min" else resample_ohlc(data, RESAMPLE_MAP[timeframe])
            baseline = backtest_strategy(test_data, params['fast'], params['slow'])
            
            # Con SAFLA
            safla_result = backtest_with_safla(
                test_data,
                strategy_name,
                params,
                timeframe=timeframe,
                learning_enabled=True
            )
            
            # Comparar
            improvement = {
                'Strategy': strategy_name,
                'Timeframe': timeframe,
                'Baseline Monthly %': round(baseline['monthly_return'], 2),
                'SAFLA Monthly %': round(safla_result['monthly_return'], 2),
                'Improvement %': round(safla_result['monthly_return'] - baseline['monthly_return'], 3),
                'SAFLA Fast': safla_result['final_fast'],
                'SAFLA Slow': safla_result['final_slow'],
                'Original Fast': params['fast'],
                'Original Slow': params['slow']
            }
            
            results_safla.append(improvement)
            
            symbol = "✓" if improvement['Improvement %'] > 0 else "✗"
            print(f"{symbol} {strategy_name} {timeframe:7s} | "
                  f"Baseline: {baseline['monthly_return']:6.2f}% → "
                  f"SAFLA: {safla_result['monthly_return']:6.2f}% "
                  f"(+{improvement['Improvement %']:5.3f}%)")
    
    # Guardar resultados
    df_results = pd.DataFrame(results_safla)
    output_file = Path("results/backtest_with_safla.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    
    print(f"\n{'='*100}")
    print(f"✓ RESULTADOS GUARDADOS: {output_file}")
    print(f"{'='*100}\n")
    
    print(df_results.to_string(index=False))

