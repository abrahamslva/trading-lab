# Agent Zero — Framework de Agentes IA con Acceso Total al Sistema

**Repositorio:** https://github.com/agent0ai/agent-zero  
**Repositorio original:** https://github.com/frdel/agent-zero  
**Licencia:** Custom (uso personal/educativo libre)  
**Estrellas:** ~17,600 | **Forks:** ~3,600 | **Contributors:** 46  
**Lenguajes:** Python 54.8%, JavaScript 22.1%, HTML 19.9%  
**Última versión:** v1.13  
**Docs:** https://github.com/agent0ai/agent-zero/blob/main/docs

---

## ¿Qué es Agent Zero?

Agent Zero es un **framework de agentes IA dinámico y orgánico** que proporciona acceso completo al sistema Linux. A diferencia de frameworks estáticos, Agent Zero no es un conjunto de herramientas predefinidas — es un agente que **crea sus propias herramientas y subagentes** según sea necesario.

### Filosofía de Diseño
- **No prescriptivo**: No sigue flujos de trabajo rígidos
- **Persistente**: Mantiene memoria entre sesiones
- **Automodificable**: Puede crear y guardar sus propias herramientas
- **Multi-agente jerárquico**: Delega tareas a subagentes especializados

---

## Características Principales

### Acceso al Sistema
- **Shell completa Linux**: Ejecuta cualquier comando bash, Python, etc.
- **Sistema de archivos**: Lee, escribe, modifica cualquier archivo
- **Instalación de software**: Puede instalar paquetes y herramientas
- **Acceso a red**: HTTP requests, SSH, APIs

### Nuevas en v1.13
- **Playwright con extensiones**: Navegador automatizado con soporte de extensiones Chrome
- **LibreOffice integrado**: Writer (docs), Calc (hojas de cálculo), Impress (presentaciones)
- **Universal Canvas**: Visualizaciones, código interactivo, diagramas
- **Time Travel**: Snapshots de estado — vuelve a cualquier punto de la conversación
- **MCP (Model Context Protocol)**: Integración con herramientas externas
- **A2A (Agent-to-Agent)**: Comunicación entre agentes de diferentes sistemas
- **CLI Connector** (`a0`): Conecta Agent Zero a tu terminal local

### Capacidades Core
- **Multi-agente**: Crea agentes subordinados para tareas complejas
- **Memoria persistente**: Vectorstore para aprendizaje a largo plazo
- **Código dinámico**: Escribe y ejecuta código en tiempo real
- **Web browsing**: Navega e interactúa con cualquier sitio
- **Multi-modelo**: Soporta OpenAI, Anthropic, Google, Groq, y más

---

## Instalación

### Método 1: Script automático (macOS/Linux)
```bash
curl -fsSL https://bash.agent-zero.ai | bash
```

### Método 2: Docker (Recomendado)
```bash
# Imagen oficial (incluye todo: Python, Node, herramientas)
docker run -p 80:80 -v a0_usr:/a0/usr agent0ai/agent-zero

# Con variables de entorno
docker run -p 80:80 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -v a0_usr:/a0/usr \
  agent0ai/agent-zero
```

### Método 3: Manual
```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
pip install -r requirements.txt
cp .env.example .env  # Editar con tus API keys
python run_ui.py      # Inicia interfaz web en localhost:80
```

### CLI Connector (a0)
```bash
# Instalar CLI
curl -LsSf https://cli.agent-zero.ai/install.sh | sh

# Usar
a0                    # Inicia sesión interactiva
a0 "analiza este código: ..."
a0 --attach <session-id>  # Conectar a sesión existente
```

---

## Configuración

### Variables de Entorno (`.env`)
```env
# LLM Principal
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Memoria (opcional — usa local si no se configura)
PINECONE_API_KEY=...   # Vector DB en la nube

# Búsqueda web
PERPLEXITY_API_KEY=... # Para búsquedas web enriquecidas
TAVILY_API_KEY=...
```

### Configuración de modelos (`initialize.py`)
```python
# Usar Claude para chat, GPT-4 para embeddings
from models import get_anthropic_chat, get_openai_embedding

chat_model = get_anthropic_chat(model_name="claude-opus-4-5")
embedding_model = get_openai_embedding(model_name="text-embedding-3-small")
```

---

## Arquitectura Multi-Agente

```
Usuario
   └── Agent 0 (Agente principal)
          ├── Agent 1 (Research specialist)
          │      └── Agent 2 (Data analyst)
          ├── Agent 3 (Code executor)
          └── Agent 4 (Web scraper)
```

Los agentes se comunican mediante mensajes estructurados. El agente principal puede crear subagentes especializados y esperan sus resultados.

---

## Herramientas Built-in

| Herramienta | Descripción |
|-------------|-------------|
| `code_execution` | Ejecuta Python, bash, Node.js |
| `browser` | Playwright: navega e interactúa con sitios |
| `file_system` | Lee/escribe/lista archivos |
| `memory` | Almacena y recupera información |
| `search_web` | Búsqueda en internet |
| `create_agent` | Crea y delega a subagentes |
| `libreoffice` | Trabaja con documentos/hojas |
| `mcp_tools` | Herramientas MCP externas |

---

## Aplicación para Trading

Agent Zero puede automatizar tareas complejas de trading:

### Análisis Automático de Mercado
```
Prompt: "Analiza el mercado de oro (XAUUSD). 
Busca noticias recientes, descarga datos históricos de MT5, 
calcula RSI y MACD en Python, y dame una señal de trading con justificación."
```

Agent Zero:
1. Abre Playwright y busca noticias de oro
2. Ejecuta Python para descargar datos históricos
3. Calcula indicadores técnicos
4. Genera reporte con señal

### Backtesting Automatizado
```
Prompt: "Optimiza los parámetros de la estrategia MACD_Ribbon 
para XAUUSD en los últimos 6 meses. Prueba 100 combinaciones 
y dame los mejores resultados en una hoja de cálculo."
```

### Gestión de Archivos MQ5
```
Prompt: "Lee el archivo MACD_Ribbon_1H.mq5, 
identifica los parámetros optimizables y 
crea 3 variantes para diferentes perfiles de riesgo."
```

---

## Time Travel (Puntos de Control)

```
# En la interfaz web:
1. Conversa normalmente con Agent Zero
2. En cualquier punto, clic en "Save Snapshot"
3. Si algo sale mal, clic en "Restore" para volver
4. Útil para experimentos: prueba una cosa, si falla, vuelve atrás
```

---

## Estructura del Repositorio

```
agent-zero/
├── agent.py              # Clase principal del agente
├── run_ui.py             # Servidor web
├── initialize.py         # Configuración de modelos
├── models.py             # Providers de LLMs
├── python/
│   ├── helpers/          # Utilidades
│   └── tools/            # Herramientas del agente
├── webui/                # Interfaz web (HTML/JS)
├── docs/                 # Documentación
│   ├── installation.md
│   ├── usage.md
│   └── tools.md
└── .env.example          # Template de configuración
```

---

## Comparativa

| Característica | Agent Zero | AutoGPT | LangChain |
|----------------|-----------|---------|-----------|
| Acceso sistema completo | ✅ Linux total | ⚠️ Limitado | ⚠️ Plugins |
| Multi-agente dinámico | ✅ Auto-crea | ✅ Platform | ✅ Multi-agent |
| Time Travel | ✅ Snapshots | ❌ | ❌ |
| Memoria persistente | ✅ Vectorstore | ✅ | ✅ |
| No requiere Docker | ✅ Sí | ❌ Platform | ✅ Sí |
| LibreOffice integrado | ✅ Sí | ❌ | ❌ |

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/agent0ai/agent-zero*
