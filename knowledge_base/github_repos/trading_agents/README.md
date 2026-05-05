# TradingAgents — Multi-Agents LLM Financial Trading Framework

**Repositorio:** https://github.com/TauricResearch/TradingAgents  
**Licencia:** Apache-2.0  
**Estrellas:** ~69,200 | **Forks:** ~13,300  
**Última versión:** v0.2.4 (2026-04)  
**Paper:** https://arxiv.org/abs/2412.20138

---

## ¿Qué es?

TradingAgents es un framework multi-agente de trading financiero impulsado por LLMs (Large Language Models). Replica la estructura de una firma de trading real con agentes especializados que colaboran para tomar decisiones de inversión.

---

## Arquitectura del Framework

### Equipo de Analistas
| Agente | Función |
|--------|---------|
| **Fundamentals Analyst** | Evalúa métricas financieras, identifica valores intrínsecos y señales de alerta |
| **Sentiment Analyst** | Analiza redes sociales y sentimiento público mediante algoritmos de scoring |
| **News Analyst** | Monitorea noticias globales e indicadores macroeconómicos |
| **Technical Analyst** | Usa indicadores técnicos (MACD, RSI) para detectar patrones de precio |

### Equipo de Investigadores
- Investigadores **bullish** y **bearish** que debaten las ideas del equipo analista
- Debates estructurados para balancear ganancias potenciales vs. riesgos

### Agente Trader
- Sintetiza reportes de analistas e investigadores
- Determina el timing y magnitud de las operaciones

### Gestión de Riesgo y Portfolio Manager
- Evalúa continuamente el riesgo del portfolio (volatilidad, liquidez, etc.)
- Portfolio Manager aprueba/rechaza propuestas de transacción
- Si se aprueba, la orden se envía al exchange simulado

---

## Instalación

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents

conda create -n tradingagents python=3.13
conda activate tradingagents
pip install .
```

### Con Docker
```bash
cp .env.example .env   # Agrega tus API keys
docker compose run --rm tradingagents
```

---

## APIs Requeridas

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export DEEPSEEK_API_KEY=...        # DeepSeek
export DASHSCOPE_API_KEY=...       # Qwen (Alibaba DashScope)
export ZHIPU_API_KEY=...           # GLM (Zhipu)
export OPENROUTER_API_KEY=...      # OpenRouter
export ALPHA_VANTAGE_API_KEY=...   # Alpha Vantage (para datos de mercado)
```

---

## Uso como CLI

```bash
tradingagents             # comando instalado
python -m cli.main        # alternativa desde el código fuente

# Con checkpoint (resume tras crash)
tradingagents analyze --checkpoint

# Limpiar checkpoints antes de correr
tradingagents analyze --clear-checkpoints
```

---

## Uso como Paquete Python

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

### Configuración avanzada
```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"         # openai, google, anthropic, xai, deepseek, qwen, glm, openrouter, ollama, azure
config["deep_think_llm"] = "gpt-5.4"      # Modelo para razonamiento complejo
config["quick_think_llm"] = "gpt-5.4-mini" # Modelo para tareas rápidas
config["max_debate_rounds"] = 2
config["checkpoint_enabled"] = True        # Activar recuperación por checkpoint

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("XAUUSD", "2026-01-15")
```

---

## Persistencia y Recuperación

### Decision Log
- Siempre activo: cada run agrega su decisión a `~/.tradingagents/memory/trading_memory.md`
- En el próximo run del mismo ticker, el sistema busca el retorno realizado, genera una reflexión e inyecta las últimas decisiones al prompt del Portfolio Manager
- Override con: `TRADINGAGENTS_MEMORY_LOG_PATH`

### Checkpoint Resume
- Opt-in con `--checkpoint`
- LangGraph guarda el estado después de cada nodo
- Los crashes/interrupciones se recuperan desde el último paso exitoso
- Checkpoints SQLite en: `~/.tradingagents/cache/checkpoints/<TICKER>.db`
- Override con: `TRADINGAGENTS_CACHE_DIR`

---

## Proveedores LLM Soportados

| Proveedor | Modelos | Tipo |
|-----------|---------|------|
| OpenAI | GPT-5.4, GPT-5.4-mini | Cloud |
| Google | Gemini 3.1 | Cloud |
| Anthropic | Claude 4.6 | Cloud |
| xAI | Grok 4.x | Cloud |
| DeepSeek | DeepSeek V4 (thinking-mode) | Cloud |
| Qwen (Alibaba) | DashScope | Cloud |
| GLM (Zhipu) | - | Cloud |
| OpenRouter | Múltiples | Agregador |
| Ollama | Modelos locales | Local |
| Azure OpenAI | Enterprise | Enterprise |
| AWS Bedrock | Enterprise | Enterprise |

---

## Estructura del Repositorio

```
TradingAgents/
├── tradingagents/          # Paquete principal
├── cli/                    # Interfaz de línea de comandos
├── scripts/                # Scripts auxiliares
├── tests/                  # Pruebas
├── assets/                 # Imágenes/recursos
├── main.py                 # Punto de entrada
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .env.enterprise.example
└── CHANGELOG.md
```

---

## Historial de Versiones

| Versión | Fecha | Cambios principales |
|---------|-------|---------------------|
| v0.2.4 | 2026-04 | Agentes con structured-output, LangGraph checkpoint resume, decision log persistente, soporte DeepSeek/Qwen/GLM/Azure, Docker, fix UTF-8 Windows |
| v0.2.3 | 2026-03 | Soporte multi-idioma, modelos GPT-5.4, catálogo unificado de modelos, fidelidad de fechas en backtesting, soporte proxy |
| v0.2.2 | 2026-03 | GPT-5.4/Gemini 3.1/Claude 4.6, escala de rating de 5 niveles, OpenAI Responses API, control de esfuerzo Anthropic |
| v0.2.0 | 2026-02 | Soporte multi-proveedor LLM (GPT-5.x, Gemini 3.x, Claude 4.x, Grok 4.x) |

---

## Cita (Paper)

```bibtex
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
    title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
    author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
    year={2025},
    eprint={2412.20138},
    archivePrefix={arXiv},
    primaryClass={q-fin.TR},
    url={https://arxiv.org/abs/2412.20138}, 
}
```

---

## Relevancia para Trading de Oro (XAUUSD)

TradingAgents puede usarse para analizar XAUUSD de la siguiente forma:

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
ta = TradingAgentsGraph(debug=True, config=config)

# Analizar XAUUSD en una fecha específica
_, decision = ta.propagate("XAUUSD", "2026-01-15")
```

Los agentes analizarán:
- Datos fundamentales del oro (inflación, DXY, tasas de interés)
- Sentimiento en redes sociales sobre el oro
- Noticias macro que afectan al oro
- Indicadores técnicos (RSI, MACD, medias móviles)

---

*Extraído de GitHub: https://github.com/TauricResearch/TradingAgents — 2026-05-05*
