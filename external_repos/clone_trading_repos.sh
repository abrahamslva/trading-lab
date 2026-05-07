#!/bin/bash
# Script para clonar base de datos completa de trading repos
set -e

cd external_repos

# BACKTESTING FRAMEWORKS
git clone --depth 1 https://github.com/quantopian/zipline zipline 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/mementum/backtrader backtrader 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/kernc/backtesting.py backtesting 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/polaurity/vectorbt vectorbt 2>&1 | tail -2 || echo "Ya existe"

# TRADING ALGORITHMS
git clone --depth 1 https://github.com/je-suis-tm/quant-trading quant-trading 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/ricequant/rqalpha rqalpha 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/ccxt/ccxt AQTrading 2>&1 | tail -2 || echo "Ya existe"

# DATA COLLECTION
git clone --depth 1 https://github.com/ranaroussi/yfinance yfinance 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/pydata/pandas-datareader pandas-datareader 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/rongardF/tvDatafeed tvDatafeed 2>&1 | tail -2 || echo "Ya existe"

# MACHINE LEARNING
git clone --depth 1 https://github.com/stefan-jansen/machine-learning-for-trading machine-learning-for-trading 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/kaushikjadhav01/Stock-Price-Prediction-LSTM-Deep-Learning stock-prediction-lstm 2>&1 | tail -2 || echo "Ya existe"

# TRADING BOTS
git clone --depth 1 https://github.com/freqtrade/freqtrade freqtrade 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/askmike/gekko Gekko 2>&1 | tail -2 || echo "Ya existe"

# TECHNICAL ANALYSIS
git clone --depth 1 https://github.com/mrjbq7/ta-lib ta-lib 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/twopirllc/pandas-ta pandas-ta 2>&1 | tail -2 || echo "Ya existe"

# BROKER APIS
git clone --depth 1 https://github.com/alpacahq/alpaca-trade-api-python alpaca-trade-api-python 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/sammchardy/python-binance python-binance 2>&1 | tail -2 || echo "Ya existe"

# VISUALIZATION
git clone --depth 1 https://github.com/plotly/plotly.py plotly 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/matplotlib/mplfinance mplfinance 2>&1 | tail -2 || echo "Ya existe"

# OPTIMIZATION
git clone --depth 1 https://github.com/optuna/optuna optuna 2>&1 | tail -2 || echo "Ya existe"
git clone --depth 1 https://github.com/hyperopt/hyperopt hyperopt 2>&1 | tail -2 || echo "Ya existe"
