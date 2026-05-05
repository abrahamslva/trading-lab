# GitHub Repos — Resumen de Repositorios Referenciados

Información extraída de repositorios GitHub externos para referencia permanente.

---

## Repositorios Indexados

| # | Repositorio | Descripción | Relevancia | Fecha extracción |
|---|-------------|-------------|------------|-----------------|
| 1 | [TauricResearch/TradingAgents](trading_agents/README.md) | Framework multi-agente LLM para trading financiero | ⭐⭐⭐ Alta | 2026-05-05 |
| 2 | [public-apis/public-apis](public_apis/README.md) | Lista colectiva de APIs públicas gratuitas | ⭐⭐⭐ Alta | 2026-05-05 |

---

## TradingAgents — Resumen Rápido

- **URL:** https://github.com/TauricResearch/TradingAgents
- **Stars:** ~69,200 | **Version:** v0.2.4
- **Instalación:** `pip install tradingagents` (desde el repo clonado)
- **Uso para XAUUSD:**
```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
ta = TradingAgentsGraph(config=DEFAULT_CONFIG.copy())
_, decision = ta.propagate("XAUUSD", "2026-01-15")
```
- **Detalle completo:** [trading_agents/README.md](trading_agents/README.md)

---

## Public APIs — Resumen Rápido

- **URL:** https://github.com/public-apis/public-apis
- **Stars:** ~432,000 | **APIs indexadas:** 1,000+
- **APIs clave para trading:**
  - Precio oro: Alpha Vantage, Twelve Data, Finnhub, Yahoo Finance
  - Macro: FRED (Federal Reserve)
  - Noticias: MarketAux, Currents, NewsData
  - Divisas: Frankfurter (gratuita), Fixer, ExchangeRate-API
  - Cripto: CoinGecko, CoinMarketCap
- **Detalle completo:** [public_apis/README.md](public_apis/README.md)

---

## Cómo Agregar Nuevos Repositorios

1. Crea una carpeta con el nombre del repo: `mkdir github_repos/nombre_repo`
2. Extrae información relevante (README, código clave, estructura)
3. Guarda en `github_repos/nombre_repo/README.md`
4. Actualiza la tabla de este archivo

---

*Última actualización: 2026-05-05*
