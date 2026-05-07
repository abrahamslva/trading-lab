# browser-use — Automatización de Navegador con IA

**Repositorio:** https://github.com/browser-use/browser-use  
**Licencia:** MIT  
**Estrellas:** ~92,500 | **Forks:** ~10,500 | **Contributors:** 317  
**Lenguajes:** Python 97.9%  
**Última versión:** 0.12.6  
**Cloud:** https://cloud.browser-use.com/  
**Descripción:** "Make websites accessible for AI agents"

---

## ¿Qué es browser-use?

browser-use es una **librería Python de código abierto** que permite a los agentes de IA controlar un navegador web real (Chromium via Playwright) para realizar cualquier tarea en la web. Con ~93k estrellas, es la biblioteca de automatización de navegador con IA más popular del mundo.

### Benchmark
- **78% de precisión** en BU-Ultra (el benchmark más difícil de automatización web)
- SOTA (State of the Art) en tareas de navegación web
- Supera a soluciones comerciales en múltiples benchmarks

---

## Características Principales

- **Control total del navegador**: Clics, formularios, scroll, navegación
- **Extracción de datos**: Scraping inteligente con instrucciones en lenguaje natural
- **Descarga de archivos**: Descarga y procesa archivos automáticamente
- **Multi-tab**: Maneja múltiples pestañas simultáneamente
- **Formularios complejos**: Rellena formularios con lógica condicional
- **2FA/CAPTCHA**: Soporte para autenticación de dos factores (Cloud)
- **Modo headless/headed**: Con o sin interfaz gráfica

---

## Instalación

### Prerrequisito: uv (gestor de paquetes Python)
```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Instalación básica
```bash
uv init my_project
cd my_project
uv add browser-use
uv sync

# Instalar navegador
uv run playwright install chromium
```

### pip (alternativa)
```bash
pip install browser-use
playwright install chromium
```

---

## Uso Básico

### Agente simple
```python
import asyncio
from langchain_openai import ChatOpenAI
from browser_use import Agent

async def main():
    agent = Agent(
        task="Go to google.com and search for 'Gold price today', then extract the current price",
        llm=ChatOpenAI(model="gpt-4o"),
    )
    result = await agent.run()
    print(result)

asyncio.run(main())
```

### Con Browser personalizado
```python
from browser_use import Agent, Browser, BrowserConfig

browser = Browser(
    config=BrowserConfig(
        headless=False,           # Ver el navegador
        disable_security=False,   # Mantener seguridad
        extra_chromium_args=["--window-size=1920,1080"],
    )
)

agent = Agent(
    task="Analyze the chart on TradingView for XAUUSD and report key levels",
    llm=ChatOpenAI(model="gpt-4o"),
    browser=browser,
)
result = await agent.run()
```

### Con herramientas personalizadas
```python
from langchain_core.tools import tool
from browser_use import Agent

@tool
def save_to_database(data: str) -> str:
    """Save extracted data to the database"""
    # Tu lógica aquí
    return "Saved successfully"

agent = Agent(
    task="Extract all price data from the page and save it to the database",
    llm=ChatOpenAI(model="gpt-4o"),
    tools=[save_to_database],
)
```

---

## CLI

```bash
# Navegar a una URL
browser-use open https://www.tradingview.com

# Hacer clic en elemento número N
browser-use click 3

# Tomar screenshot
browser-use screenshot

# Ejecutar tarea en lenguaje natural
browser-use run "Search for XAUUSD analysis on TradingView"
```

---

## Templates Iniciales

```bash
# Template básico
uvx browser-use init --template default

# Con herramientas personalizadas
uvx browser-use init --template tools

# Avanzado con múltiples agentes
uvx browser-use init --template advanced
```

---

## Modelos LLM Soportados

```python
# OpenAI
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o")

# Anthropic
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

# Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# DeepSeek
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    base_url="https://api.deepseek.com/v1",
    model="deepseek-chat",
    api_key="..."
)

# Ollama (local)
from langchain_ollama import ChatOllama
llm = ChatOllama(model="llama3.3")
```

---

## Configuración Avanzada

```python
from browser_use import Agent, Browser, BrowserConfig, Controller

# Controller: controla qué acciones puede tomar el agente
controller = Controller()

@controller.action("Save extracted price data")
def save_price(price: float, symbol: str) -> str:
    print(f"Saving {symbol}: {price}")
    return f"Saved {symbol}={price}"

# Browser con proxy y cookies persistentes
browser = Browser(
    config=BrowserConfig(
        headless=True,
        proxy={"server": "http://proxy:8080"},
        user_data_dir="~/.browser_use_profile",  # Cookies persistentes
    )
)

agent = Agent(
    task="Monitor gold price every minute for 1 hour",
    llm=ChatOpenAI(model="gpt-4o"),
    browser=browser,
    controller=controller,
    max_steps=200,
)
```

---

## Cloud (cloud.browser-use.com)

La versión cloud ofrece capacidades adicionales:
- **Stealth browsers**: Evita detección anti-bot
- **Proxy rotation**: IPs diferentes automáticamente
- **CAPTCHA solving**: Resuelve CAPTCHAs automáticamente
- **Session management**: Sesiones persistentes en la nube
- **Escalado**: Sin gestión de infraestructura

```python
# Uso con Cloud
from browser_use.cloud import CloudBrowser

browser = CloudBrowser(api_key="bu_...")
agent = Agent(task="...", llm=llm, browser=browser)
```

---

## Aplicaciones para Trading

### Scraping de Datos de Mercado
```python
agent = Agent(
    task="""
    1. Go to https://www.investing.com/commodities/gold
    2. Extract: current price, daily change, 52-week high/low
    3. Go to Economic Calendar
    4. Extract events for next 3 days that affect Gold
    5. Return all data as JSON
    """,
    llm=ChatOpenAI(model="gpt-4o"),
)
```

### Monitoreo de Noticias
```python
agent = Agent(
    task="""
    Search Google News for "gold XAUUSD" news from last 24 hours.
    Classify each news item as Bullish/Bearish/Neutral for gold.
    Return top 5 most impactful news with classification.
    """,
    llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
)
```

### Automatización MT5 Web
```python
agent = Agent(
    task="""
    1. Open MetaTrader5 web terminal
    2. Login with credentials
    3. Check XAUUSD H1 chart
    4. Take screenshot of current market structure
    5. Return screenshot path
    """,
    llm=ChatOpenAI(model="gpt-4o"),
    browser=Browser(config=BrowserConfig(headless=False)),
)
```

---

## Estructura del Proyecto

```
browser-use/
├── browser_use/
│   ├── agent/              # Lógica del agente
│   │   ├── agent.py        # Clase principal Agent
│   │   └── views.py        # Estructuras de datos
│   ├── browser/            # Control del navegador
│   │   ├── browser.py      # Clase Browser
│   │   └── context.py      # Contexto del browser
│   ├── controller/         # Control de acciones
│   │   └── service.py      # Acciones disponibles
│   └── dom/                # Procesamiento del DOM
├── examples/               # Ejemplos de uso
│   ├── simple.py
│   ├── multi_tab.py
│   └── custom_tools.py
└── tests/                  # Tests
```

---

## Comparativa

| Característica | browser-use | Selenium | Playwright | Puppeteer |
|----------------|------------|---------|-----------|----------|
| Lenguaje natural | ✅ IA | ❌ Código | ❌ Código | ❌ Código |
| Auto-adaptación | ✅ Sí | ❌ Frágil | ❌ Frágil | ❌ Frágil |
| Sin selectores CSS | ✅ Sí | ❌ Requiere | ❌ Requiere | ❌ Requiere |
| Multi-modelo | ✅ 10+ LLMs | N/A | N/A | N/A |
| Curva aprendizaje | 🟢 Baja | 🔴 Alta | 🟡 Media | 🟡 Media |
| Performance | 🟡 Media | 🔴 Lenta | 🟢 Rápida | 🟢 Rápida |

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/browser-use/browser-use*
