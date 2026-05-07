# AutoGPT — Plataforma de Construcción y Despliegue de Agentes IA

**Repositorio:** https://github.com/Significant-Gravitas/AutoGPT  
**Licencia:** MIT (AutoGPT Classic) + Polyform Shield 1.0.0 (AutoGPT Platform)  
**Estrellas:** ~184,000 | **Forks:** ~46,200 | **Contributors:** 808  
**Lenguajes:** Python 69%, TypeScript 29%  
**Última versión:** autogpt-platform-beta-v0.6.58  
**Docs:** https://docs.agpt.co/

---

## ¿Qué es AutoGPT?

AutoGPT es una plataforma para **construir, desplegar y gestionar agentes de IA** de forma visual y programática. Es uno de los proyectos de agentes IA más populares del mundo, con dos componentes principales:

1. **AutoGPT Platform** (producción): Plataforma basada en Docker con interfaz de bajo código para construir flujos de trabajo de agentes. Licencia Polyform Shield (no comercial sin permiso).
2. **AutoGPT Classic** (legado): El agente GPT-4 autónomo original que impulsó el boom de los agentes IA. Licencia MIT.

---

## Componentes Principales

### AutoGPT Platform (Recomendado)
- **Agent Builder**: Interfaz visual de bajo código para construir agentes
- **Workflow Management**: Conecta bloques (acciones) para crear pipelines
- **Marketplace**: Descarga y comparte agentes pre-construidos
- **Monitoring**: Supervisa ejecuciones de agentes en tiempo real
- **Forge**: Toolkit para desarrolladores con primitivas de agentes
- **agbenchmark**: Suite de evaluación estandarizada para benchmarking de agentes

### AutoGPT Classic
El agente GPT-4 autónomo original. Se le da un objetivo en lenguaje natural y lo descompone en subtareas ejecutándolas con herramientas (web, código, archivos).

---

## Instalación

### AutoGPT Platform (Docker)
```bash
# Instalar con script automático
curl -fsSL https://setup.agpt.co/install.sh -o install.sh && bash install.sh

# O clonar manualmente
git clone https://github.com/Significant-Gravitas/AutoGPT.git
cd AutoGPT/autogpt_platform
cp .env.example .env
docker compose up -d
```

Acceder en: http://localhost:3000

### AutoGPT Classic
```bash
git clone https://github.com/Significant-Gravitas/AutoGPT.git
cd AutoGPT/classic/original_autogpt
pip install poetry
poetry install
cp .env.template .env  # Editar con tu OPENAI_API_KEY
python -m autogpt
```

---

## Uso Básico (Platform)

1. Abre el Agent Builder en http://localhost:3000
2. Arrastra y conecta bloques (input, LLM, web search, output)
3. Configura cada bloque con parámetros
4. Ejecuta y monitorea en tiempo real

### Forge SDK (para desarrolladores)
```python
from forge.agent import ForgeAgent
from forge.sdk import Workspace, TaskInput

class MyTradingAgent(ForgeAgent):
    async def execute_step(self, task_id: str, step_input: TaskInput):
        # Lógica personalizada del agente
        result = await self.abilities.run_ability(
            task_id,
            "web_search",
            query="Gold price news today"
        )
        return result
```

### agbenchmark (Evaluación)
```bash
cd autogpt_platform/backend
agbenchmark run --maintain  # Ejecutar suite de benchmark
agbenchmark run --category="coding"  # Solo categoría específica
```

---

## Bloques Disponibles (Platform)

| Categoría | Bloques |
|-----------|---------|
| LLM | LLM Block, AI Text Generator, Structured Output |
| Búsqueda | Web Search, Google Search, Wikipedia |
| Código | Code Execution, Python Script, Bash |
| Archivos | File Read/Write, CSV Parser |
| APIs | HTTP Request, REST API, Webhook |
| Email | Email Send, Email Reader |
| Datos | JSON Parser, Data Transform, Calculator |
| Control | If/Else, Loop, Wait, Error Handler |

---

## Variables de Entorno Clave

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

---

## Aplicación para Trading

AutoGPT puede usarse para construir agentes de trading que:
- **Monitoreen noticias** financieras en tiempo real
- **Analicen sentimiento** del mercado con LLMs
- **Ejecuten estrategias** mediante herramientas de código
- **Gestionen portfolios** con datos de APIs financieras
- **Generen reportes** automáticos de posiciones

### Ejemplo: Agente de Análisis de Oro
```python
# Flujo típico en AutoGPT Platform:
# 1. WebSearch: "Gold price analysis today"
# 2. LLM Block: Analiza noticias para señal Bull/Bear
# 3. HTTP Request: Obtiene precio actual de XAUUSD (Alpha Vantage)
# 4. Code Block: Calcula señal técnica (RSI, MA)
# 5. Email Block: Envía alerta si hay señal
```

---

## Estructura del Repositorio

```
AutoGPT/
├── autogpt_platform/          # Plataforma principal
│   ├── frontend/              # Next.js - interfaz web
│   ├── backend/               # FastAPI - lógica del servidor
│   ├── autogpt_libs/          # Librerías compartidas
│   └── docker-compose.yml     # Configuración Docker
├── classic/
│   ├── original_autogpt/      # Agente original (legado)
│   └── forge/                 # SDK para developers
├── benchmark/
│   └── agbenchmark/           # Suite de benchmarking
└── docs/                      # Documentación
```

---

## Diferencias con Otros Frameworks

| Característica | AutoGPT Platform | LangChain | CrewAI |
|----------------|-----------------|-----------|--------|
| UI Visual | ✅ Sí | ❌ No | ❌ No |
| Low-code | ✅ Sí | ❌ No | ❌ No |
| Marketplace | ✅ Sí | ❌ No | ❌ No |
| Multi-agente | ✅ Sí | ✅ Sí | ✅ Sí |
| Deploy propio | ✅ Docker | ✅ Sí | ✅ Sí |
| Licencia libre | ❌ Polyform | ✅ MIT | ✅ MIT |

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/Significant-Gravitas/AutoGPT*
