#!/usr/bin/env python3
"""
GitHub Trading Research - Buscar y analizar repos de trading algorítmico
Crea una base de datos sólida de herramientas, estrategias y algoritmos
"""

import requests
import json
from datetime import datetime
from pathlib import Path

class GitHubTradingResearch:
    def __init__(self):
        self.github_api = "https://api.github.com/search/repositories"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        self.results = {
            "trading_algorithms": [],
            "trading_strategies": [],
            "backtesting": [],
            "market_data": [],
            "trading_bots": [],
            "ml_trading": [],
            "data_collection": [],
            "api_wrappers": []
        }
    
    def search_repos(self, query, language="python", sort="stars", max_results=30):
        """Buscar repos en GitHub con criterios específicos"""
        search_query = f"{query} language:{language} sort:{sort}"
        
        try:
            response = requests.get(
                self.github_api,
                params={"q": search_query, "per_page": max_results},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("items", [])
            else:
                print(f"❌ Error en búsqueda: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error en conexión: {e}")
            return []
    
    def analyze_repo(self, repo):
        """Analizar un repositorio y extraer info relevante"""
        return {
            "name": repo.get("name", ""),
            "url": repo.get("html_url", ""),
            "owner": repo.get("owner", {}).get("login", ""),
            "description": repo.get("description", ""),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", []),
            "updated": repo.get("updated_at", ""),
            "size_kb": repo.get("size", 0),
            "relevance_score": 0
        }
    
    def run_search_campaign(self):
        """Ejecutar búsqueda completa de trading repos"""
        
        print("\n" + "="*80)
        print("🔍 INVESTIGACIÓN DE TRADING EN GITHUB".center(80))
        print("="*80 + "\n")
        
        # Búsquedas principales
        searches = {
            "trading_algorithms": [
                "trading algorithm",
                "algorithmic trading",
                "quantitative trading",
                "algo trader",
            ],
            "trading_strategies": [
                "trading strategy",
                "stock strategy",
                "forex strategy",
                "crypto trading strategy",
            ],
            "backtesting": [
                "backtesting framework",
                "backtest trading",
                "historical backtest",
                "strategy backtester",
            ],
            "market_data": [
                "market data API",
                "stock data",
                "crypto data",
                "OHLC data",
            ],
            "trading_bots": [
                "trading bot",
                "bot trader",
                "automated trading",
                "trading automation",
            ],
            "ml_trading": [
                "machine learning trading",
                "neural network trading",
                "AI trading",
                "deep learning stock",
            ],
            "data_collection": [
                "web scraper trading",
                "data collection finance",
                "financial data scraper",
                "market scraper",
            ],
            "api_wrappers": [
                "broker API wrapper",
                "trading API client",
                "market data wrapper",
                "exchange API",
            ]
        }
        
        for category, queries in searches.items():
            print(f"\n📚 Buscando: {category.replace('_', ' ').upper()}")
            print("-" * 60)
            
            for query in queries:
                print(f"  🔎 {query}...", end=" ", flush=True)
                repos = self.search_repos(query, max_results=10)
                
                if repos:
                    print(f"✓ {len(repos)} encontrados")
                    for repo in repos:
                        analyzed = self.analyze_repo(repo)
                        analyzed["relevance_score"] = len(repos) - repos.index(repo)
                        
                        # Evitar duplicados
                        if not any(r["url"] == analyzed["url"] for r in self.results[category]):
                            self.results[category].append(analyzed)
                else:
                    print("✗ Sin resultados")
        
        return self.results
    
    def save_to_db(self, filename="trading_repos_database.json"):
        """Guardar resultados en base de datos JSON"""
        output_path = Path("data/catalogs") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        # Organizar por categoría
        organized = {
            "metadata": {
                "date": datetime.now().isoformat(),
                "total_repos": sum(len(v) for v in self.results.values()),
                "categories": list(self.results.keys())
            },
            "repositories": self.results
        }
        
        with open(output_path, "w") as f:
            json.dump(organized, f, indent=2)
        
        print(f"\n✅ Base de datos guardada: {output_path}")
        return output_path
    
    def generate_report(self):
        """Generar reporte de hallazgos"""
        report = []
        report.append("\n" + "="*80)
        report.append("📊 REPORTE DE INVESTIGACIÓN - TRADING REPOS EN GITHUB".center(80))
        report.append("="*80 + "\n")
        
        total_repos = 0
        
        for category, repos in self.results.items():
            total_repos += len(repos)
            top_3 = sorted(repos, key=lambda x: x["stars"], reverse=True)[:3]
            
            report.append(f"\n📁 {category.replace('_', ' ').upper()}")
            report.append(f"   Total: {len(repos)} repositorios")
            
            if top_3:
                report.append("   TOP 3 (por stars):")
                for i, repo in enumerate(top_3, 1):
                    report.append(f"      {i}. {repo['name']} ({repo['owner']})")
                    report.append(f"         ⭐ {repo['stars']} | 📦 {repo['size_kb']}KB")
                    report.append(f"         {repo['url']}")
        
        report.append(f"\n\n📊 TOTAL: {total_repos} repositorios encontrados")
        report.append("\n" + "="*80 + "\n")
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Guardar reporte
        with open("data/catalogs/trading_research_report.txt", "w") as f:
            f.write(report_text)
        
        return report_text
    
    def create_integration_index(self):
        """Crear índice de integración para todos los repos encontrados"""
        index = {
            "integration_plan": [],
            "priority_repos": [],
            "quick_wins": [],
            "long_term_projects": []
        }
        
        # Encontrar repos con >100 stars (prioridad alta)
        all_repos = []
        for category, repos in self.results.items():
            all_repos.extend([(repo, category) for repo in repos])
        
        # Ordenar por stars
        all_repos.sort(key=lambda x: x[0]["stars"], reverse=True)
        
        for repo, category in all_repos[:30]:
            item = {
                "name": repo["name"],
                "category": category,
                "url": repo["url"],
                "stars": repo["stars"],
                "quick_integration": repo["stars"] > 500
            }
            index["integration_plan"].append(item)
            
            if repo["stars"] > 1000:
                index["priority_repos"].append(item)
            elif repo["stars"] > 100:
                index["quick_wins"].append(item)
            else:
                index["long_term_projects"].append(item)
        
        return index

if __name__ == "__main__":
    researcher = GitHubTradingResearch()
    
    # Ejecutar búsqueda
    results = researcher.run_search_campaign()
    
    # Guardar a base de datos
    researcher.save_to_db()
    
    # Generar reporte
    researcher.generate_report()
    
    print("\n✅ Investigación completada")
    print("📄 Archivos generados:")
    print("   - data/catalogs/trading_repos_database.json")
    print("   - data/catalogs/trading_research_report.txt")
