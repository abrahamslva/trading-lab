# Skyvern — Automatización de Flujos Web con LLMs y Visión Computacional

**Repositorio:** https://github.com/Skyvern-AI/skyvern  
**Licencia:** AGPL-3.0  
**Estrellas:** ~21,500 | **Forks:** ~2,000 | **Contributors:** 98  
**Lenguajes:** Python 73%, TypeScript 22.7%  
**Última versión:** v1.0.32  
**Docs:** https://www.skyvern.com/docs  
**Benchmark:** 64.4% en WebBench (SOTA en tareas WRITE)

---

## ¿Qué es Skyvern?

Skyvern es una herramienta para **automatizar flujos de trabajo basados en navegador** usando LLMs y visión computacional. A diferencia de las soluciones tradicionales de scraping/automatización, Skyvern **no usa selectores CSS ni XPath** — en cambio, analiza la página visualmente como lo haría un humano.

### Diferenciador Clave
- **Extensión de Playwright con IA**: Añade métodos `act()`, `extract()`, `validate()` y `prompt()` directamente en Playwright
- **Resistente a cambios**: Si el sitio cambia su HTML, Skyvern sigue funcionando
- **Compatible con MCP**: Integra con Claude Desktop y otros clientes MCP
- **Integración nativa**: Zapier, Make, N8N

---

## Instalación

### pip (más simple)
```bash
pip install skyvern
skyvern quickstart  # Configuración interactiva inicial
```

### Docker Compose (recomendado para producción)
```bash
git clone https://github.com/Skyvern-AI/skyvern.git
cd skyvern
cp .env.example .env  # Editar con tus API keys
docker compose up -d

# Acceder en:
# API: http://localhost:8000
# UI: http://localhost:8080
```

### Desarrollo local
```bash
git clone https://github.com/Skyvern-AI/skyvern.git
cd skyvern
poetry install
playwright install chromium

cp .env.example .env
# Editar .env con: LLM_KEY, DATABASE_STRING, etc.

poetry run python -m skyvern.forge.app  # Backend
cd skyvern-frontend && npm install && npm run dev  # Frontend
```

---

## SDK Python — API Principal

### Los 4 métodos fundamentales

```python
from skyvern import Skyvern

client = Skyvern(api_key="sk-...")

async def example():
    async with await client.browser.new_page() as page:
        await page.goto("https://example.com")
        
        # 1. act() — Realiza una acción en lenguaje natural
        await page.act("Click on the login button")
        await page.act("Fill in the username field with 'user@email.com'")
        await page.act("Submit the form")
        
        # 2. extract() — Extrae datos con esquema
        from pydantic import BaseModel
        
        class StockData(BaseModel):
            symbol: str
            price: float
            change: float
            volume: int
        
        data = await page.extract(
            "Extract the stock data from the table",
            schema=StockData
        )
        print(data)  # StockData(symbol='XAUUSD', price=2350.5, ...)
        
        # 3. validate() — Verifica una condición
        is_logged_in = await page.validate(
            "Is the user successfully logged in?"
        )
        
        # 4. prompt() — Consulta abierta sobre la página
        analysis = await page.prompt(
            "Analyze the current chart and identify support/resistance levels"
        )
```

---

## Compatibilidad con Playwright

Skyvern extiende Playwright directamente:

```python
from playwright.async_api import async_playwright
from skyvern.integrations.playwright import SkyvernPlaywright

async with async_playwright() as p:
    browser = await SkyvernPlaywright(p).chromium.launch()
    page = await browser.new_page()
    
    # Playwright normal
    await page.goto("https://tradingview.com")
    
    # Skyvern extensions
    await page.act("Search for XAUUSD")
    data = await page.extract("Get the current price and indicators")
    
    # Playwright normal continúa
    screenshot = await page.screenshot(path="chart.png")
```

---

## Variables de Entorno

```env
# LLM (selecciona uno o más)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
AWS_ACCESS_KEY_ID=...       # Para Bedrock
AWS_SECRET_ACCESS_KEY=...
OLLAMA_SERVER=http://localhost:11434  # Para Ollama local

# Base de datos
DATABASE_STRING=postgresql://skyvern:skyvern@localhost/skyvern

# Configuración
LLM_KEY=OPENAI_GPT4O         # Modelo a usar
SKYVERN_API_KEY=sk-skyvern-... # Para API REST
```

---

## LLMs Soportados

| Proveedor | Modelos |
|-----------|---------|
| OpenAI | GPT-5, GPT-4o, GPT-4.1 |
| Anthropic | Claude 4.7, Claude 3.5 |
| Google | Gemini 3.1 Pro, Gemini 2.5 |
| AWS Bedrock | Claude, Llama, Nova |
| Ollama | Cualquier modelo local |
| OpenRouter | 200+ modelos |

---

## Funcionalidades Avanzadas

### Tasks y Workflows

```python
# Task: Una acción simple
task = await client.run_task(
    url="https://finance.yahoo.com",
    navigation_goal="Search for XAUUSD and extract current price",
    data_extraction_goal="Extract: price, change, change_percent"
)

# Workflow: Múltiples pasos con 12 tipos de bloques
workflow = await client.run_workflow(
    workflow_id="wf_123",
    parameters={"symbol": "XAUUSD"}
)
```

### 12 Tipos de Bloques en Workflows
1. **Navigation** — Navega a una URL
2. **Task** — Ejecuta tarea en la página
3. **Loop** — Itera sobre una lista
4. **Condition** — Bifurcación if/else
5. **Code** — Ejecuta código Python
6. **Wait** — Espera un tiempo o condición
7. **File Parser** — Procesa archivos
8. **Send Email** — Envía correo
9. **HTTP Request** — Llama a una API
10. **TextPrompt** — Solicita input al usuario
11. **Upload File** — Sube archivos
12. **Download File** — Descarga archivos

### Autenticación Avanzada
```python
# 2FA TOTP (Google Authenticator)
task = await client.run_task(
    url="https://exchange.com",
    navigation_goal="Login and check portfolio",
    totp_identifier="my_account",  # Referencia al secreto TOTP
)

# Gestores de contraseñas
# Soporta: Bitwarden, 1Password
# Permite al agente usar credenciales guardadas
```

### Livestreaming
```python
# Ver el navegador en tiempo real
stream_url = await client.get_livestream_url(task_id)
print(f"Watch at: {stream_url}")
```

---

## MCP Integration

```bash
# Configurar Skyvern como herramienta MCP para Claude Desktop
# En ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "skyvern": {
      "command": "skyvern",
      "args": ["mcp"],
      "env": {
        "SKYVERN_API_KEY": "sk-skyvern-..."
      }
    }
  }
}
```

Con esto, Claude Desktop puede usar Skyvern para automatizar tareas web directamente.

---

## Integraciones No-Code

| Plataforma | Uso |
|------------|-----|
| **Zapier** | Triggear Skyvern desde cualquier app Zapier |
| **Make (Integromat)** | Flujos automáticos con Skyvern |
| **N8N** | Node nativo de Skyvern en N8N |

---

## Aplicaciones para Trading

### Extracción de Datos de Brokers
```python
async with await client.browser.new_page() as page:
    await page.goto("https://your-broker.com")
    await page.act("Login with saved credentials")
    
    positions = await page.extract(
        "Extract all open positions",
        schema=PositionsModel
    )
    
    is_profitable = await page.validate(
        "Are all positions currently profitable?"
    )
```

### Monitoreo de Plataformas Financieras
```python
# Extrae datos de TradingView, Investing.com, etc.
task = await client.run_task(
    url="https://www.investing.com/commodities/gold",
    navigation_goal="Load the XAUUSD 1H chart",
    data_extraction_goal="""
        Extract:
        - Current price
        - RSI(14) value
        - MACD signal
        - Key support/resistance levels
        - Today's high/low
    """
)
```

### Automatización de Formularios Financieros
```python
# Rellenar formularios de trading automáticamente
await page.act("Open new order form")
await page.act(f"Enter symbol XAUUSD")
await page.act(f"Enter lot size 0.1")
await page.act(f"Set stop loss at {sl_price}")
await page.act(f"Set take profit at {tp_price}")

confirmed = await page.validate("Is the order form filled correctly?")
if confirmed:
    await page.act("Submit the order")
```

---

## API REST

```bash
# Crear una tarea
curl -X POST https://api.skyvern.com/v1/tasks \
  -H "x-api-key: sk-skyvern-..." \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://finance.yahoo.com",
    "navigation_goal": "Search XAUUSD and get price",
    "data_extraction_goal": "Current price of gold"
  }'

# Obtener resultado
curl https://api.skyvern.com/v1/tasks/{task_id} \
  -H "x-api-key: sk-skyvern-..."
```

---

## Estructura del Repositorio

```
skyvern/
├── skyvern/
│   ├── forge/              # Core del agente
│   │   ├── agent/          # Lógica de agente
│   │   └── sdk/            # SDK Python
│   ├── integrations/       # Integraciones externas
│   │   ├── playwright/     # Extension Playwright
│   │   ├── zapier/         # Zapier
│   │   └── mcp/            # MCP server
│   └── webeye/             # Visión computacional
├── skyvern-frontend/       # UI (React/TypeScript)
├── alembic/                # Migraciones DB
└── docker-compose.yml
```

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/Skyvern-AI/skyvern*
