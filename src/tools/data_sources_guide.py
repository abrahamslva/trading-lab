#!/usr/bin/env python3
"""
Guía completa de fuentes de datos disponibles en trading-lab
Después de integrar 38 repositorios
"""

DATA_SOURCES = {
    "stock_data": {
        "yfinance": {
            "url": "https://github.com/ranaroussi/yfinance",
            "type": "API wrapper",
            "data": ["stocks", "forex", "crypto", "futures"],
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "1d"],
            "history": "10 years back",
            "cost": "FREE",
            "usage": """
            import yfinance as yf
            data = yf.download("AAPL", start="2016-01-01", end="2024-05-06")
            """,
            "pros": ["Simple", "Popular", "Histórico largo"],
            "cons": ["Rate limits", "XAUUSD limitado"]
        },
        
        "tvDatafeed": {
            "url": "https://github.com/rongardF/tvDatafeed",
            "type": "TradingView scraper",
            "data": ["stocks", "forex", "crypto", "indices"],
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "history": "10+ years",
            "cost": "FREE",
            "usage": """
            from tvDatafeed import Datafeed
            df = Datafeed().get_hist("XAUUSD", "1h")
            """,
            "pros": ["M15 XAUUSD disponible", "Sin API", "Datos profesionales"],
            "cons": ["Más lento", "Scraping (puede bloquearse)"]
        },
        
        "pandas-datareader": {
            "url": "https://github.com/pydata/pandas-datareader",
            "type": "Data reader unificado",
            "data": ["stocks", "forex", "crypto", "económicos"],
            "timeframes": ["1d"],
            "history": "10+ years",
            "cost": "FREE (algunas APIs requieren key)",
            "usage": """
            import pandas_datareader as pdr
            data = pdr.get_data_yahoo("GOOG", "2016-01-01")
            """,
            "pros": ["Múltiples fuentes", "Flexible", "DataFrames pandas"],
            "cons": ["Principalmente diarios", "Algunas fuentes discontinuadas"]
        }
    },
    
    "crypto_data": {
        "CCXT": {
            "url": "https://github.com/ccxt/ccxt",
            "type": "Unified exchange API",
            "data": ["crypto OHLCV", "ticker", "orderbook"],
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "history": "Variable (1 mes a 2+ años por exchange)",
            "cost": "FREE (algunos exchanges requieren API key)",
            "exchanges": ["Binance", "Coinbase", "Kraken", "Bybit", "OKX", "Huobi"],
            "usage": """
            import ccxt
            binance = ccxt.binance()
            ohlcv = binance.fetch_ohlcv('BTC/USDT', '1h')
            """,
            "pros": ["Múltiples exchanges", "Uniforme", "Datos en vivo"],
            "cons": ["Rate limits", "API keys requeridas", "Datos históricos limitados"]
        },
        
        "python-binance": {
            "url": "https://github.com/sammchardy/python-binance",
            "type": "Binance official wrapper",
            "data": ["OHLCV", "ticker", "balance", "trades"],
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"],
            "history": "1000 candles máximo por request",
            "cost": "FREE",
            "usage": """
            from binance.client import Client
            client = Client(api_key, api_secret)
            klines = client.get_klines(symbol='BTCUSDT', interval='1h')
            """,
            "pros": ["Oficial Binance", "Más rápido que CCXT", "Completo"],
            "cons": ["Solo Binance", "API key requerida"]
        }
    },
    
    "forex_data": {
        "yfinance_forex": {
            "url": "https://github.com/ranaroussi/yfinance",
            "type": "Yahoo Finance",
            "pairs": ["EURUSD", "GBPUSD", "XAUUSD", "etc."],
            "timeframes": ["1h", "4h", "1d"],
            "history": "10+ years",
            "cost": "FREE",
            "usage": """
            import yfinance as yf
            eurusd = yf.download("EURUSD=X", start="2016-01-01")
            """,
            "pros": ["Simple", "Largo historial"],
            "cons": ["M15 limitado", "Updates lentos"]
        },
        
        "tvDatafeed_forex": {
            "url": "https://github.com/rongardF/tvDatafeed",
            "type": "TradingView",
            "pairs": ["XAUUSD", "EURUSD", "GBPUSD", "etc."],
            "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "history": "10+ years",
            "cost": "FREE",
            "usage": """
            from tvDatafeed import Datafeed
            xau = Datafeed().get_hist("XAUUSD", "15m", 1000)
            """,
            "pros": ["M15 XAUUSD", "Profesional", "Histórico completo"],
            "cons": ["Scraping", "Posibles bloqueos"]
        }
    },
    
    "contextual_data": {
        "FACT": {
            "url": "external_repos/FACT",
            "type": "Fast Augmented Context Tools",
            "data": ["Historical patterns", "Context retrieval"],
            "usage": """
            from external_repos.FACT import ContextRetriever
            retriever = ContextRetriever()
            similar_patterns = retriever.search(current_state, k=10)
            """,
            "pros": ["Contexto histórico", "Pattern matching", "Integrado"],
            "cons": ["Requiere datos previos indexados"]
        }
    },
    
    "alternative_sources": {
        "public-apis": {
            "url": "https://github.com/public-apis/public-apis",
            "type": "Listado exhaustivo APIs",
            "data": ["100+ APIs financieras y de datos"],
            "usage": """
            # Buscar en: https://github.com/public-apis/public-apis
            # Categorías: Finance, Cryptocurrency, Data
            """,
            "pros": ["Descubrir nuevas fuentes", "Gratis", "Alternativas"],
            "cons": ["Requiere investigación"]
        },
        
        "Scrapling": {
            "url": "external_repos/Scrapling",
            "type": "Web scraper universal",
            "data": ["Cualquier dato web"],
            "usage": """
            from external_repos.Scrapling import Scraper
            scraper = Scraper()
            data = scraper.scrape("https://investing.com/xau-usd-chart")
            """,
            "pros": ["Flexible", "Cualquier fuente", "Sin límites"],
            "cons": ["Legal/ético", "Mantenimiento", "Cambios HTML"]
        }
    }
}

def print_guide():
    print("\n" + "="*100)
    print("📊 GUÍA COMPLETA DE FUENTES DE DATOS - TRADING-LAB".center(100))
    print("="*100 + "\n")
    
    for category, sources in DATA_SOURCES.items():
        print(f"\n🔹 {category.replace('_', ' ').upper()}")
        print("-" * 100)
        
        for source_name, details in sources.items():
            print(f"\n   📌 {source_name}")
            print(f"      URL: {details.get('url', 'N/A')}")
            print(f"      Tipo: {details.get('type', 'N/A')}")
            
            if 'data' in details:
                print(f"      Datos: {', '.join(details['data'])}")
            
            if 'timeframes' in details:
                print(f"      Timeframes: {', '.join(details['timeframes'])}")
            
            if 'history' in details:
                print(f"      Histórico: {details['history']}")
            
            if 'cost' in details:
                print(f"      Costo: {details['cost']}")
            
            if 'exchanges' in details:
                print(f"      Exchanges: {', '.join(details['exchanges'][:5])}")
            
            if 'usage' in details:
                print(f"      Ejemplo:\n{details['usage']}")
            
            if 'pros' in details:
                print(f"      ✅ Pros: {', '.join(details['pros'])}")
            
            if 'cons' in details:
                print(f"      ❌ Contras: {', '.join(details['cons'])}")
    
    print("\n\n" + "="*100)
    print("🎯 RECOMENDACIONES DE USO POR CASO".center(100))
    print("="*100 + "\n")
    
    recommendations = {
        "XAUUSD M15 (Proyecto principal)": [
            "Primaria: tvDatafeed (mejor M15 + histórico)",
            "Secundaria: yfinance (respaldo)",
            "Actualización: CCXT (para crypto exchanges si necesitas)"
        ],
        "Backtesting (10 años)": [
            "Usar: yfinance (simple, largo histórico)",
            "Alternativa: tvDatafeed (más datos)",
            "Combinar con pandas-datareader para validación"
        ],
        "Trading en vivo (Crypto)": [
            "Primaria: python-binance (si es Binance)",
            "Alternativa: CCXT (si múltiples exchanges)",
            "Real-time + historical data"
        ],
        "Trading en vivo (Forex)": [
            "Broker API nativa (MT5, IG, etc)",
            "Respaldo: tvDatafeed",
            "Contexto: FACT para pattern matching"
        ],
        "Context/Pattern Matching": [
            "FACT: Buscar patrones históricos similares",
            "RuVector: Neural memory O(1)",
            "Inputs: Datos históricos OHLCV"
        ]
    }
    
    for use_case, sources in recommendations.items():
        print(f"\n📌 {use_case}")
        for source in sources:
            print(f"   → {source}")
    
    print("\n\n" + "="*100)
    print("💾 TAMAÑOS Y REQUERIMIENTOS".center(100))
    print("="*100 + "\n")
    
    print("""
    M15 XAUUSD 2016-2024 (127,050 candles):
    ├─ Parquet: 5.3 MB
    ├─ CSV: ~20 MB
    └─ En memoria (pandas): ~100 MB
    
    Daily data 10 años (2,600 candles):
    ├─ Parquet: 200 KB
    ├─ CSV: ~800 KB
    └─ En memoria: ~5 MB
    
    Crypto M15 1 año (35,000 candles):
    ├─ Parquet: 1.5 MB
    ├─ CSV: ~5 MB
    └─ En memoria: ~30 MB
    
    Requerimientos mínimos:
    ├─ Memoria: 1-2 GB
    ├─ Almacenamiento: 10 GB
    └─ Internet: 50 Mbps (para descargas)
    """)
    
    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    print_guide()
