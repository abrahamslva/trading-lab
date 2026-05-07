#!/usr/bin/env python3
"""
Catálogo completo de 38 repositorios de trading + IA + data engineering
Análisis automático y indexación por categoría
"""

import json
import os
from pathlib import Path
from collections import defaultdict

def analyze_repos():
    """Analizar todos los repos clonados en external_repos"""
    
    repos = {}
    external_repos_path = Path("external_repos")
    
    # Listar todos los directorios
    for repo_dir in sorted(external_repos_path.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name in ['clone_repos.sh', 'clone_additional.sh', 'clone_trading_repos.sh']:
            continue
        
        repo_name = repo_dir.name
        
        # Calcular tamaño
        size_kb = 0
        try:
            for dirpath, dirnames, filenames in os.walk(repo_dir):
                for filename in filenames:
                    size_kb += os.path.getsize(os.path.join(dirpath, filename)) / 1024
        except:
            pass
        
        # Leer README si existe
        readme_text = ""
        readme_paths = [
            repo_dir / "README.md",
            repo_dir / "README.txt",
            repo_dir / "readme.md"
        ]
        
        for readme_path in readme_paths:
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        readme_text = f.read()[:500]  # Primeras 500 caracteres
                    break
                except:
                    pass
        
        repos[repo_name] = {
            "size_mb": round(size_kb / 1024, 1),
            "path": str(repo_dir),
            "readme_snippet": readme_text[:200] if readme_text else "No README found",
            "file_count": len(list(repo_dir.rglob("*"))),
        }
    
    return repos

def categorize_repos(repos):
    """Categorizar repos automáticamente"""
    
    categories = {
        "backtesting_frameworks": {
            "keywords": ["backtest", "zipline", "backtrader"],
            "repos": []
        },
        "trading_algorithms": {
            "keywords": ["quant", "algorithm", "trading", "rqalpha"],
            "repos": []
        },
        "trading_bots": {
            "keywords": ["bot", "freqtrade", "gekko", "automation"],
            "repos": []
        },
        "data_collection": {
            "keywords": ["data", "yfinance", "feed", "scraper", "public-apis"],
            "repos": []
        },
        "machine_learning": {
            "keywords": ["ml", "learning", "neural", "lstm", "deep"],
            "repos": []
        },
        "technical_analysis": {
            "keywords": ["indicator", "ta-lib", "pandas-ta"],
            "repos": []
        },
        "ai_agents": {
            "keywords": ["agent", "agentic", "ruflo", "agency"],
            "repos": []
        },
        "broker_apis": {
            "keywords": ["broker", "api", "binance", "alpaca"],
            "repos": []
        },
        "visualization": {
            "keywords": ["plot", "visual", "chart", "mplfinance"],
            "repos": []
        },
        "optimization": {
            "keywords": ["optuna", "hyperopt", "optimization"],
            "repos": []
        },
        "data_tools": {
            "keywords": ["fact", "guardrail", "context", "superstream"],
            "repos": []
        },
        "other": {
            "keywords": [],
            "repos": []
        }
    }
    
    # Categorizar cada repo
    categorized = defaultdict(list)
    
    for repo_name, repo_info in repos.items():
        name_lower = repo_name.lower()
        readme_lower = repo_info["readme_snippet"].lower()
        combined = name_lower + " " + readme_lower
        
        assigned = False
        for category, details in categories.items():
            if category == "other":
                continue
            
            for keyword in details["keywords"]:
                if keyword.lower() in combined:
                    categorized[category].append(repo_name)
                    assigned = True
                    break
            
            if assigned:
                break
        
        if not assigned:
            categorized["other"].append(repo_name)
    
    return dict(categorized)

def generate_catalog():
    """Generar catálogo completo"""
    
    print("\n" + "="*100)
    print("📊 CATÁLOGO COMPLETO - 38 REPOSITORIOS DE TRADING + IA + DATA ENGINEERING".center(100))
    print("="*100 + "\n")
    
    # Analizar repos
    repos = analyze_repos()
    print(f"✅ Analizados {len(repos)} repositorios\n")
    
    # Categorizar
    categories = categorize_repos(repos)
    
    # Generar catálogo
    catalog = {
        "metadata": {
            "total_repos": len(repos),
            "categories": len([c for c in categories if categories[c]]),
            "total_size_mb": sum(r["size_mb"] for r in repos.values())
        },
        "repositories": {}
    }
    
    # Mostrar por categoría
    for category, repo_list in sorted(categories.items()):
        if not repo_list:
            continue
        
        size_category = sum(repos[r]["size_mb"] for r in repo_list)
        print(f"\n📁 {category.replace('_', ' ').upper()}")
        print(f"   📊 {len(repo_list)} repos | 💾 {size_category:.1f} MB")
        print("   " + "-" * 80)
        
        for repo_name in sorted(repo_list):
            size_mb = repos[repo_name]["size_mb"]
            print(f"   ✓ {repo_name:<40} {size_mb:>8.1f} MB")
            
            catalog["repositories"][repo_name] = {
                "category": category,
                "size_mb": size_mb,
                "files": repos[repo_name]["file_count"]
            }
    
    print("\n" + "="*100)
    print(f"\n📊 ESTADÍSTICAS FINALES:")
    print(f"   Total repositorios: {len(repos)}")
    print(f"   Total categorías: {len([c for c in categories if categories[c]])}")
    print(f"   Tamaño total: {catalog['metadata']['total_size_mb']:.1f} MB")
    print("\n")
    
    # Guardar catálogo
    catalog_path = Path("data/catalogs/complete_catalog_38_repos.json")
    catalog_path.parent.mkdir(exist_ok=True)
    
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2)
    
    print(f"✅ Catálogo guardado: {catalog_path}")
    
    return catalog

if __name__ == "__main__":
    generate_catalog()
