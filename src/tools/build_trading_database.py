#!/usr/bin/env python3
"""
Base de datos curada de repos de trading, algoritmos y data engineering
Lista manualmente seleccionada de los mejores repos disponibles en GitHub
"""

import json
from pathlib import Path
from subprocess import run, PIPE

# Base de datos curada de repos importante para trading
TRADING_REPOS_DATABASE = {
    "backtesting_frameworks": [
        {
            "name": "zipline",
            "owner": "quantopian",
            "url": "https://github.com/quantopian/zipline",
            "stars": 19729,
            "description": "Framework backtesting profesional Python",
            "priority": 1,
            "tags": ["backtesting", "quantitative", "framework"]
        },
        {
            "name": "backtrader",
            "owner": "mementum",
            "url": "https://github.com/mementum/backtrader",
            "stars": 15000,
            "description": "Trading backtest + paper trading",
            "priority": 1,
            "tags": ["backtesting", "trading", "framework"]
        },
        {
            "name": "backtesting",
            "owner": "kernc",
            "url": "https://github.com/kernc/backtesting.py",
            "stars": 6500,
            "description": "Backtesting ligero y simple",
            "priority": 2,
            "tags": ["backtesting", "simple"]
        },
        {
            "name": "vectorbt",
            "owner": "polaurity",
            "url": "https://github.com/polaurity/vectorbt",
            "stars": 5000,
            "description": "Backtesting vectorizado ultra-rápido",
            "priority": 2,
            "tags": ["backtesting", "performance"]
        }
    ],
    
    "trading_algorithms": [
        {
            "name": "quant-trading",
            "owner": "je-suis-tm",
            "url": "https://github.com/je-suis-tm/quant-trading",
            "stars": 9792,
            "description": "Repositorio completo de estrategias cuantitativas",
            "priority": 1,
            "tags": ["algorithms", "strategies", "quant"]
        },
        {
            "name": "rqalpha",
            "owner": "ricequant",
            "url": "https://github.com/ricequant/rqalpha",
            "stars": 6351,
            "description": "Open source quantitative trading framework (China)",
            "priority": 1,
            "tags": ["framework", "algorithms", "quant"]
        },
        {
            "name": "AQTrading",
            "owner": "ccxt",
            "url": "https://github.com/ccxt/ccxt",
            "stars": 30000,
            "description": "Trading exchange API unificada (cripto principalmente)",
            "priority": 1,
            "tags": ["exchange", "crypto", "api"]
        }
    ],
    
    "data_collection": [
        {
            "name": "yfinance",
            "owner": "ranaroussi",
            "url": "https://github.com/ranaroussi/yfinance",
            "stars": 15000,
            "description": "Descargador de datos Yahoo Finance",
            "priority": 1,
            "tags": ["data", "financial", "stock"]
        },
        {
            "name": "pandas-datareader",
            "owner": "pydata",
            "url": "https://github.com/pydata/pandas-datareader",
            "stars": 3000,
            "description": "Lectura de datos financieros múltiples fuentes",
            "priority": 2,
            "tags": ["data", "pandas", "financial"]
        },
        {
            "name": "tvDatafeed",
            "owner": "rongardF",
            "url": "https://github.com/rongardF/tvDatafeed",
            "stars": 2000,
            "description": "Datos de TradingView sin API",
            "priority": 2,
            "tags": ["data", "tradingview", "scraping"]
        }
    ],
    
    "machine_learning": [
        {
            "name": "machine-learning-for-trading",
            "owner": "stefan-jansen",
            "url": "https://github.com/stefan-jansen/machine-learning-for-trading",
            "stars": 8000,
            "description": "ML aplicado a trading con código educativo",
            "priority": 1,
            "tags": ["ml", "deep-learning", "trading"]
        },
        {
            "name": "stock-prediction-lstm",
            "owner": "kaushikjadhav01",
            "url": "https://github.com/kaushikjadhav01/Stock-Price-Prediction-LSTM-Deep-Learning",
            "stars": 3500,
            "description": "Predicción de precios con LSTM",
            "priority": 2,
            "tags": ["ml", "lstm", "prediction"]
        }
    ],
    
    "trading_bots": [
        {
            "name": "freqtrade",
            "owner": "freqtrade",
            "url": "https://github.com/freqtrade/freqtrade",
            "stars": 28000,
            "description": "Bot trading automatizado profesional",
            "priority": 1,
            "tags": ["bot", "trading", "automation"]
        },
        {
            "name": "Gekko",
            "owner": "askmike",
            "url": "https://github.com/askmike/gekko",
            "stars": 12000,
            "description": "Bot cripto trading Node.js",
            "priority": 2,
            "tags": ["bot", "crypto", "nodejs"]
        }
    ],
    
    "technical_analysis": [
        {
            "name": "ta-lib",
            "owner": "mrjbq7",
            "url": "https://github.com/mrjbq7/ta-lib",
            "stars": 10000,
            "description": "Análisis técnico indicators (Python wrapper)",
            "priority": 1,
            "tags": ["technical-analysis", "indicators"]
        },
        {
            "name": "pandas-ta",
            "owner": "twopirllc",
            "url": "https://github.com/twopirllc/pandas-ta",
            "stars": 5000,
            "description": "Indicators técnicos con pandas",
            "priority": 1,
            "tags": ["technical-analysis", "pandas"]
        }
    ],
    
    "broker_apis": [
        {
            "name": "alpaca-trade-api-python",
            "owner": "alpacahq",
            "url": "https://github.com/alpacahq/alpaca-trade-api-python",
            "stars": 3000,
            "description": "API oficial Alpaca (stock brokerage)",
            "priority": 2,
            "tags": ["broker", "api", "stock"]
        },
        {
            "name": "python-binance",
            "owner": "sammchardy",
            "url": "https://github.com/sammchardy/python-binance",
            "stars": 6000,
            "description": "Wrapper oficial Binance API",
            "priority": 1,
            "tags": ["exchange", "crypto", "binance"]
        }
    ],
    
    "visualization": [
        {
            "name": "plotly",
            "owner": "plotly",
            "url": "https://github.com/plotly/plotly.py",
            "stars": 15000,
            "description": "Visualización interactiva de datos",
            "priority": 2,
            "tags": ["visualization", "interactive"]
        },
        {
            "name": "mplfinance",
            "owner": "matplotlib",
            "url": "https://github.com/matplotlib/mplfinance",
            "stars": 3500,
            "description": "Gráficos financieros con matplotlib",
            "priority": 2,
            "tags": ["visualization", "charts"]
        }
    ],
    
    "optimization": [
        {
            "name": "optuna",
            "owner": "optuna",
            "url": "https://github.com/optuna/optuna",
            "stars": 10000,
            "description": "Optimización Bayesiana de hiperparámetros",
            "priority": 1,
            "tags": ["optimization", "hyperparameter-tuning"]
        },
        {
            "name": "hyperopt",
            "owner": "hyperopt",
            "url": "https://github.com/hyperopt/hyperopt",
            "stars": 7000,
            "description": "Optimización distribuida de hiperparámetros",
            "priority": 2,
            "tags": ["optimization", "parallel"]
        }
    ]
}

def save_database():
    """Guardar base de datos en JSON"""
    db_path = Path("data/catalogs/trading_curated_database.json")
    db_path.parent.mkdir(exist_ok=True)
    
    with open(db_path, "w") as f:
        json.dump(TRADING_REPOS_DATABASE, f, indent=2)
    
    print(f"✅ Base de datos guardada: {db_path}")
    return db_path

def generate_clone_script():
    """Generar script para clonar todos los repos"""
    script = []
    script.append("#!/bin/bash")
    script.append("# Script para clonar base de datos completa de trading repos")
    script.append("set -e")
    script.append("")
    script.append("cd external_repos")
    script.append("")
    
    for category, repos in TRADING_REPOS_DATABASE.items():
        script.append(f"# {category.replace('_', ' ').upper()}")
        for repo in repos:
            script.append(f'git clone --depth 1 {repo["url"]} {repo["name"]} 2>&1 | tail -2 || echo "Ya existe"')
        script.append("")
    
    script_path = Path("external_repos/clone_trading_repos.sh")
    with open(script_path, "w") as f:
        f.write("\n".join(script))
    
    import os
    os.chmod(script_path, 0o755)
    print(f"✅ Script de clonación guardado: {script_path}")
    return script_path

def generate_priority_index():
    """Generar índice de prioridad"""
    index = {
        "priority_1": [],
        "priority_2": [],
        "summary": {}
    }
    
    for category, repos in TRADING_REPOS_DATABASE.items():
        index["summary"][category] = len(repos)
        
        for repo in repos:
            item = {
                "name": repo["name"],
                "owner": repo["owner"],
                "url": repo["url"],
                "category": category,
                "stars": repo["stars"],
                "description": repo["description"]
            }
            
            if repo["priority"] == 1:
                index["priority_1"].append(item)
            else:
                index["priority_2"].append(item)
    
    # Ordenar por stars
    index["priority_1"].sort(key=lambda x: x["stars"], reverse=True)
    index["priority_2"].sort(key=lambda x: x["stars"], reverse=True)
    
    index_path = Path("data/catalogs/trading_priority_index.json")
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    
    print(f"✅ Índice de prioridad guardado: {index_path}")
    return index_path

def print_summary():
    """Mostrar resumen de la base de datos"""
    print("\n" + "="*80)
    print("📊 BASE DE DATOS CURADA DE TRADING - RESUMEN".center(80))
    print("="*80 + "\n")
    
    total_repos = sum(len(repos) for repos in TRADING_REPOS_DATABASE.values())
    
    for category, repos in TRADING_REPOS_DATABASE.items():
        print(f"\n📁 {category.replace('_', ' ').upper()}")
        print(f"   Total: {len(repos)} repositorios")
        
        # Top 2 por stars
        sorted_repos = sorted(repos, key=lambda x: x["stars"], reverse=True)[:2]
        for i, repo in enumerate(sorted_repos, 1):
            print(f"   {i}. {repo['name']} ({repo['owner']})")
            print(f"      ⭐ {repo['stars']} stars")
            print(f"      {repo['description']}")
    
    print(f"\n\n📊 TOTAL: {total_repos} repositorios catalogados")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print_summary()
    save_database()
    generate_clone_script()
    generate_priority_index()
    
    print("\n✅ Archivos generados:")
    print("   - data/catalogs/trading_curated_database.json (base de datos completa)")
    print("   - data/catalogs/trading_priority_index.json (índice de prioridad)")
    print("   - external_repos/clone_trading_repos.sh (script de clonación)")
