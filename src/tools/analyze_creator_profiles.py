#!/usr/bin/env python3
"""
Análisis de perfiles de creadores - Descubrir más repos de trading/IA
Busca los creadores de los repos más importantes y documenta sus otros repos
"""

CREATOR_PROFILES = {
    "quantopian": {
        "repos": ["zipline"],
        "profile_url": "https://github.com/quantopian",
        "description": "Empresa de trading algorítmico",
        "notable_repos": ["zipline", "empyrical"],
        "focus": ["backtesting", "research"]
    },
    
    "mementum": {
        "repos": ["backtrader"],
        "profile_url": "https://github.com/mementum",
        "description": "Creador de backtrader",
        "notable_repos": ["backtrader"],
        "focus": ["backtesting"]
    },
    
    "je-suis-tm": {
        "repos": ["quant-trading"],
        "profile_url": "https://github.com/je-suis-tm",
        "description": "Repositorio activo de estrategias cuantitativas",
        "notable_repos": ["quant-trading", "Machine-Learning-Loans-Advances"],
        "focus": ["strategies", "machine-learning"]
    },
    
    "ricequant": {
        "repos": ["rqalpha"],
        "profile_url": "https://github.com/ricequant",
        "description": "Plataforma trading chino",
        "notable_repos": ["rqalpha", "rq-data"],
        "focus": ["backtesting", "research"]
    },
    
    "ccxt": {
        "repos": ["AQTrading"],  # Listado como CCXT
        "profile_url": "https://github.com/ccxt",
        "description": "Unified exchange API gigante",
        "notable_repos": ["ccxt", "ccxt.wiki"],
        "focus": ["exchange", "crypto"]
    },
    
    "ranaroussi": {
        "repos": ["yfinance"],
        "profile_url": "https://github.com/ranaroussi",
        "description": "Creador de yfinance",
        "notable_repos": ["yfinance", "pandas-datareader-fork"],
        "focus": ["data-collection"]
    },
    
    "stefan-jansen": {
        "repos": ["machine-learning-for-trading"],
        "profile_url": "https://github.com/stefan-jansen",
        "description": "ML for trading educador",
        "notable_repos": ["machine-learning-for-trading", "ml4trading"],
        "focus": ["machine-learning", "education"]
    },
    
    "freqtrade": {
        "repos": ["freqtrade"],
        "profile_url": "https://github.com/freqtrade",
        "description": "Equipo profesional bot trading",
        "notable_repos": ["freqtrade", "freqtrade-strategies"],
        "focus": ["bot", "automation"]
    },
    
    "askmike": {
        "repos": ["Gekko"],
        "profile_url": "https://github.com/askmike",
        "description": "Creador de Gekko",
        "notable_repos": ["gekko", "gekko-strategies"],
        "focus": ["bot", "crypto"]
    },
    
    "sammchardy": {
        "repos": ["python-binance"],
        "profile_url": "https://github.com/sammchardy",
        "description": "Binance API wrapper creador",
        "notable_repos": ["python-binance", "python-kucoin", "python-bitmex"],
        "focus": ["exchange", "api-wrapper"]
    },
    
    "twopirllc": {
        "repos": ["pandas-ta"],
        "profile_url": "https://github.com/twopirllc",
        "description": "Indicadores técnicos pandas",
        "notable_repos": ["pandas-ta", "pandas-ta-examples"],
        "focus": ["technical-analysis", "indicators"]
    },
    
    "optuna": {
        "repos": ["optuna"],
        "profile_url": "https://github.com/optuna",
        "description": "Framework optimización Bayesiana",
        "notable_repos": ["optuna", "optuna-examples"],
        "focus": ["optimization", "ml"]
    },
    
    "hyperopt": {
        "repos": ["hyperopt"],
        "profile_url": "https://github.com/hyperopt",
        "description": "Optimización distribuida",
        "notable_repos": ["hyperopt", "hyperopt-sklearn"],
        "focus": ["optimization", "ml"]
    },
    
    "plotly": {
        "repos": ["plotly"],
        "profile_url": "https://github.com/plotly",
        "description": "Visualización interactiva",
        "notable_repos": ["plotly.py", "plotly.js", "dash"],
        "focus": ["visualization", "analytics"]
    },
    
    "ruvnet": {
        "repos": ["ruflo", "SAFLA", "guardrail", "FACT"],
        "profile_url": "https://github.com/ruvnet",
        "description": "Creador principal - AI trading agents",
        "notable_repos": [
            "ruflo", "SAFLA", "guardrail", "FACT", "agentic-flow",
            "agency-agents", "QuDAG", "RuVector", "dspy.ts", 
            "ruvbot", "voicebot", "rUv-dev"
        ],
        "focus": ["ai-agents", "trading", "data-engineering"]
    },
    
    "D4Vinci": {
        "repos": ["Scrapling"],
        "profile_url": "https://github.com/D4Vinci",
        "description": "Creador de Scrapling web scraper",
        "notable_repos": ["Scrapling", "Frida-Python", "BadCode"],
        "focus": ["scraping", "security"]
    },
    
    "chrisworsey55": {
        "repos": ["atlas-gic"],
        "profile_url": "https://github.com/chrisworsey55",
        "description": "Atlas - Investor algorithms",
        "notable_repos": ["atlas-gic"],
        "focus": ["algorithms", "investment"]
    },
    
    "msitarzewski": {
        "repos": ["agency-agents"],
        "profile_url": "https://github.com/msitarzewski",
        "description": "Agency agents framework",
        "notable_repos": ["agency-agents"],
        "focus": ["ai-agents"]
    }
}

def generate_creator_analysis():
    """Generar análisis de perfiles de creadores"""
    
    print("\n" + "="*100)
    print("👥 ANÁLISIS DE PERFILES DE CREADORES - DESCUBRIMIENTO DE REPOS".center(100))
    print("="*100 + "\n")
    
    # Top creadores por importancia
    top_creators = [
        ("ruvnet", "Creador de 12 repos de IA/Trading - PRIORIDAD MÁXIMA"),
        ("quantopian", "Creador de zipline (backtesting profesional)"),
        ("freqtrade", "Equipo bot trading automatizado"),
        ("ccxt", "API unificada de exchanges (30k stars)"),
        ("stefan-jansen", "ML for trading educador"),
        ("ranaroussi", "Creador de yfinance"),
    ]
    
    print("🏆 TOP CREADORES (Por importancia para trading-lab):\n")
    for i, (creator, desc) in enumerate(top_creators, 1):
        profile = CREATOR_PROFILES.get(creator, {})
        repos_count = len(profile.get("notable_repos", []))
        print(f"   {i}. {creator}")
        print(f"      📊 {repos_count} repos importantes")
        print(f"      📌 {desc}")
        print(f"      🔗 {profile.get('profile_url', 'N/A')}")
        print()
    
    # Análisis detallado
    print("\n" + "-"*100)
    print("📊 ANÁLISIS DETALLADO POR CREADOR")
    print("-"*100 + "\n")
    
    for creator, profile in sorted(CREATOR_PROFILES.items()):
        repos = profile.get("notable_repos", [])
        focus = ", ".join(profile.get("focus", []))
        
        print(f"\n👤 {creator.upper()}")
        print(f"   Descripción: {profile.get('description', 'N/A')}")
        print(f"   Repos principales: {len(repos)}")
        print(f"   Enfoque: {focus}")
        print(f"   Profile: {profile.get('profile_url', 'N/A')}")
        
        if len(repos) > 0:
            print(f"   Repos: {', '.join(repos[:5])}")
    
    print("\n" + "="*100)
    print("📈 RECOMENDACIONES DE BÚSQUEDA ADICIONAL".center(100))
    print("="*100 + "\n")
    
    additional_searches = [
        ("ruvnet", "Buscar todos los repos de ruvnet"),
        ("quantopian-research", "Investigaciones de Quantopian"),
        ("freqtrade-strategies", "Estrategias para freqtrade"),
        ("zipline-strategies", "Estrategias para zipline"),
        ("algorithmic-trading", "Repos generales de algorithmic trading"),
        ("quantitative-finance", "Repos de finanzas cuantitativas"),
        ("crypto-trading", "Repos de trading cripto"),
        ("stock-trading", "Repos de trading de stocks"),
    ]
    
    print("\n🔎 BÚSQUEDAS RECOMENDADAS (Para futuras exploraciones):\n")
    for i, (keyword, desc) in enumerate(additional_searches, 1):
        print(f"   {i}. {keyword}")
        print(f"      → {desc}")
    
    print("\n" + "="*100 + "\n")
    
    # Generar JSON de perfiles
    import json
    from pathlib import Path
    
    output_path = Path("data/catalogs/creator_profiles_analysis.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(CREATOR_PROFILES, f, indent=2)
    
    print(f"✅ Análisis guardado: {output_path}\n")

if __name__ == "__main__":
    generate_creator_analysis()
