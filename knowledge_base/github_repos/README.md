# GitHub Repos — Resumen de Repositorios Referenciados

Información extraída de repositorios GitHub externos para referencia permanente.

---

## Repositorios Indexados

| # | Repositorio | Descripción | Relevancia | Fecha extracción |
|---|-------------|-------------|------------|-----------------|
| 1 | [TauricResearch/TradingAgents](trading_agents/README.md) | Framework multi-agente LLM para trading financiero | ⭐⭐⭐ Alta | 2026-05-05 |
| 2 | [public-apis/public-apis](public_apis/README.md) | Lista colectiva de APIs públicas gratuitas (1,000+ APIs) | ⭐⭐⭐ Alta | 2026-05-05 |
| 3 | [Significant-Gravitas/AutoGPT](autogpt/README.md) | Plataforma para construir y desplegar agentes IA autónomos | ⭐⭐⭐ Alta | 2026-05-05 |
| 4 | [zaidmukaddam/scira](scira/README.md) | Motor de búsqueda IA con análisis de stocks/crypto (Perplexity alternativa) | ⭐⭐ Media | 2026-05-05 |
| 5 | [agent0ai/agent-zero](agent_zero/README.md) | Framework de agentes IA dinámico con acceso total a Linux | ⭐⭐⭐ Alta | 2026-05-05 |
| 6 | [enricoros/big-AGI](big_agi/README.md) | Workspace IA multi-modelo con Beam & Merge anti-alucinación | ⭐⭐ Media | 2026-05-05 |
| 7 | [browser-use/browser-use](browser_use/README.md) | Automatización de navegador con IA (92.5k stars, 78% SOTA) | ⭐⭐⭐ Alta | 2026-05-05 |
| 8 | [Skyvern-AI/skyvern](skyvern/README.md) | Automatización web con LLMs y visión computacional | ⭐⭐⭐ Alta | 2026-05-05 |
| 9 | [feder-cr/Jobs_Applier_AI_Agent_AIHawk](jobs_applier_ai_agent/README.md) | Agente IA para formularios web (ARCHIVADO — referencia arquitectura) | ⭐ Referencia | 2026-05-05 |

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

## AutoGPT — Resumen Rápido

- **URL:** https://github.com/Significant-Gravitas/AutoGPT
- **Stars:** ~184,000 | **Licencia:** MIT + Polyform Shield
- **Instalación:** `git clone + docker compose up --build`
- **Uso para trading:** Agent Builder low-code para crear bots de trading con steps visuales
- **Detalle completo:** [autogpt/README.md](autogpt/README.md)

---

## Scira — Resumen Rápido

- **URL:** https://github.com/zaidmukaddam/scira
- **Stars:** ~11,600 | **Licencia:** AGPL-3.0
- **Herramientas clave:** `get_stock_data`, `get_crypto_data`, noticias financieras
- **Deploy:** `npx create-next-app --example "https://github.com/zaidmukaddam/scira"`
- **Detalle completo:** [scira/README.md](scira/README.md)

---

## Agent Zero — Resumen Rápido

- **URL:** https://github.com/agent0ai/agent-zero
- **Stars:** ~17,600 | **Licencia:** No Licence
- **Instalación:** `curl -fsSL https://raw.githubusercontent.com/agent0ai/agent-zero/main/prepare_env.sh | bash`
- **Características:** Acceso completo a Linux, Playwright, LibreOffice, MCP/A2A, Time Travel snapshots
- **Detalle completo:** [agent_zero/README.md](agent_zero/README.md)

---

## big-AGI — Resumen Rápido

- **URL:** https://github.com/enricoros/big-AGI
- **Stars:** ~7,000 | **Licencia:** MIT
- **Feature clave:** Beam & Merge — lanza la misma query a múltiples LLMs simultáneamente para reducir alucinaciones
- **Deploy:** `npx big-agi` o Docker o Vercel
- **Detalle completo:** [big_agi/README.md](big_agi/README.md)

---

## browser-use — Resumen Rápido

- **URL:** https://github.com/browser-use/browser-use
- **Stars:** ~92,500 | **Licencia:** MIT | **SOTA:** 78% BU-Ultra
- **Instalación:** `uv pip install browser-use && playwright install chromium`
- **Uso para trading:** Scraping de TradingView, monitoreo de noticias, automatización MT5 web
- **Detalle completo:** [browser_use/README.md](browser_use/README.md)

---

## Skyvern — Resumen Rápido

- **URL:** https://github.com/Skyvern-AI/skyvern
- **Stars:** ~21,500 | **Licencia:** AGPL-3.0 | **SOTA:** 64.4% WebBench
- **Instalación:** `pip install skyvern` + extensión Playwright
- **Uso para trading:** `await page.act("buscar precio del oro")`, extracción de datos financieros
- **Detalle completo:** [skyvern/README.md](skyvern/README.md)

---

## Jobs Applier AIHawk — Resumen Rápido

- **URL:** https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- **Stars:** ~29,800 | **Licencia:** AGPL-3.0 | ⚠️ ARCHIVADO Apr 2026
- **Relevancia:** Referencia de arquitectura para automatización de formularios con Playwright + LLM
- **Detalle completo:** [jobs_applier_ai_agent/README.md](jobs_applier_ai_agent/README.md)

---

## Cómo Agregar Nuevos Repositorios

1. Crea una carpeta con el nombre del repo: `mkdir github_repos/nombre_repo`
2. Extrae información relevante (README, código clave, estructura)
3. Guarda en `github_repos/nombre_repo/README.md`
4. Actualiza la tabla de este archivo

---

*Última actualización: 2026-05-05*
