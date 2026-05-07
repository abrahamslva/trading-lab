# big-AGI — Workspace de IA Multi-Modelo para Expertos

**Repositorio:** https://github.com/enricoros/big-AGI  
**Licencia:** MIT  
**Estrellas:** ~7,000 | **Forks:** ~1,600 | **Contributors:** 55  
**Lenguajes:** TypeScript 81.6%, JavaScript 17.7%  
**Última versión:** v2.0.4  
**Hosted:** https://big-agi.com/ (gratuito + Pro $10.99/mes)

---

## ¿Qué es big-AGI?

big-AGI es un **workspace de IA multi-modelo de código abierto** diseñado para ingenieros, fundadores e investigadores. Su característica más destacada es **Beam & Merge**, que permite ejecutar la misma consulta en múltiples LLMs simultáneamente para reducir alucinaciones y obtener respuestas más confiables.

---

## Característica Clave: Beam & Merge

El sistema Beam es una técnica de **reducción de alucinaciones multi-modelo**:

1. **Beam**: Envía la misma pregunta a N modelos diferentes en paralelo
2. **Merge**: Un modelo "árbitro" analiza todas las respuestas y genera una síntesis final

```
Tu pregunta
     ↓
┌──────────┬──────────┬──────────┐
│ GPT-4    │ Claude   │ Gemini   │
│ Respuesta│ Respuesta│ Respuesta│
└──────────┴──────────┴──────────┘
          ↓ Merge (LLM árbitro)
    Respuesta final sintetizada
    con mayor precisión
```

Ideal para:
- Análisis financiero que requiere alta precisión
- Validación de estrategias de trading
- Research con múltiples perspectivas
- Preguntas donde un solo modelo puede equivocarse

---

## Proveedores y Modelos Soportados (500+ modelos)

| Proveedor | Modelos |
|-----------|---------|
| OpenAI | GPT-4o, o1, o3, GPT-4.1, GPT-5 |
| Anthropic | Claude 3.5/4.x Sonnet, Opus, Haiku |
| Google | Gemini 2.5 Pro/Flash, Gemini 3 |
| AWS Bedrock | Claude, Llama, Titan |
| Azure OpenAI | GPT-4, GPT-4o |
| DeepSeek | R1, V3, Coder |
| Mistral | Large, Codestral, NeMo |
| Groq | Llama 3.3, Mixtral |
| xAI | Grok 3/4 |
| Alibaba | Qwen 3 |
| Ollama | Cualquier modelo local |
| LocalAI | Modelos locales |
| LM Studio | Modelos locales |
| OpenRouter | 200+ modelos vía proxy |
| Perplexity | pplx-7b/70b |

---

## Funcionalidades

### Chat y Conversación
- **Personas**: Crea asistentes especializados con instrucciones de sistema
- **Branches**: Ramifica conversaciones para explorar diferentes enfoques
- **Bifurcación**: Continúa desde cualquier punto de la conversación
- **Markdown**: Renderizado completo con tablas, código, math (KaTeX)

### Beam Multi-Modelo
- Ejecuta hasta 8 modelos en paralelo
- Compara respuestas visualmente
- Merge automático o manual
- Útil para: análisis, código, research

### Generación de Imágenes
- DALL-E 3 (OpenAI)
- Stability AI
- Generación por descripción en chat

### Búsqueda Web con Citas
- Integración con Brave Search
- Resultados con fuentes verificadas
- Citas inline en respuestas

### Síntesis de Voz
- ElevenLabs: voz ultra-realista
- Browser TTS: síntesis nativa
- Lectura de respuestas en tiempo real

### Otros
- **Call**: Conversación por voz con IA
- **Draw**: Generación de imágenes
- **News**: Feed de noticias procesado por IA
- **Personas**: Asistentes con personalidades específicas

---

## Instalación

### Docker (Recomendado)
```bash
docker run -d -p 3000:3000 \
  -e OPENAI_API_KEY=sk-... \
  ghcr.io/enricoros/big-agi:latest
```

### Vercel (Deploy propio)
```bash
# Un clic:
# https://vercel.com/new/clone?repository-url=https://github.com/enricoros/big-AGI
```

### Desarrollo local
```bash
git clone https://github.com/enricoros/big-AGI.git
cd big-AGI
npm install
cp .env.example .env.local  # Configura API keys
npm run dev
```

---

## Variables de Entorno

```env
# Proveedores LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_GENERATIVE_AI_API_KEY=...
GROQ_API_KEY=...

# AWS Bedrock
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Búsqueda web
BRAVE_SEARCH_API_KEY=...

# Síntesis de voz
ELEVENLABS_API_KEY=...
```

---

## Uso para Trading e Investigación Financiera

### Beam para Análisis de Mercado
```
Configuración: 4 modelos en paralelo
- GPT-4o, Claude Sonnet, Gemini Pro, DeepSeek V3

Prompt: "Análisis técnico de XAUUSD en H1. 
Contexto macro: [pegar datos de FRED]. 
¿Tendencia para las próximas 4 horas?"

Resultado: 4 análisis diferentes + síntesis unificada
→ Mayor confianza en la señal resultante
```

### Creación de Estrategias con Múltiples Modelos
```
Beam con GPT-4 + Claude + Gemini:
"Diseña una estrategia de scalping para XAUUSD en M15 
usando ATR y Volume Profile. Incluye reglas de entrada/salida 
y gestión de riesgo. Código Python."

→ Compara 3 implementaciones diferentes
→ Selecciona la mejor o merge de las 3
```

### Personas Especializadas
Crea una persona "Gold Trading Expert" con system prompt:
```
Eres un trader experto en commodities con 20 años de experiencia 
en XAUUSD. Analizas el mercado combinando análisis técnico, 
macro fundamentals y análisis de volumen. Siempre incluyes:
- Contexto del mercado actual
- Niveles clave de S/R
- Señal de trading con stop y take profit
- Risk/Reward mínimo 1:2
```

---

## Estructura del Proyecto

```
big-AGI/
├── src/
│   ├── apps/
│   │   ├── chat/           # App principal de chat
│   │   ├── beam/           # Beam & Merge
│   │   ├── draw/           # Generación de imágenes
│   │   └── news/           # Feed de noticias IA
│   ├── modules/
│   │   ├── llms/           # Integración de LLMs
│   │   └── aifn/           # Funciones de IA
│   └── common/             # Componentes compartidos
├── public/                 # Assets
└── next.config.js          # Configuración Next.js
```

---

## Diferencias con Otras Interfaces

| Característica | big-AGI | ChatGPT Plus | Perplexity | OpenRouter |
|----------------|---------|--------------|-----------|-----------|
| Multi-modelo simultáneo | ✅ Beam | ❌ | ❌ | ⚠️ |
| Open source | ✅ MIT | ❌ | ❌ | ❌ |
| Self-hosted | ✅ | ❌ | ❌ | ❌ |
| 500+ modelos | ✅ | ❌ ~10 | ❌ ~5 | ✅ |
| Voz (ElevenLabs) | ✅ | ✅ | ❌ | ❌ |
| Web search | ✅ | ✅ | ✅ | ❌ |

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/enricoros/big-AGI*
