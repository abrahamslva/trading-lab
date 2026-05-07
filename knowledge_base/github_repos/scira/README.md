# Scira — Motor de Búsqueda IA Minimalista (Alternativa a Perplexity)

**Repositorio:** https://github.com/zaidmukaddam/scira  
**Licencia:** AGPL-3.0  
**Estrellas:** ~11,600 | **Forks:** ~1,500 | **Contributors:** 20  
**Lenguajes:** TypeScript 98.6%  
**Demo en vivo:** https://scira.ai/  
**Descripción:** "Research at the speed of thought"

---

## ¿Qué es Scira?

Scira (antes MiniPerplx) es un motor de búsqueda IA de **código abierto** minimalista que usa modelos de lenguaje avanzados para buscar en la web y responder preguntas con fuentes verificadas. Es una alternativa open-source directa a Perplexity AI.

### Características Diferenciadoras
- **17 modos de búsqueda** especializados
- **28+ herramientas** integradas
- Soporte para **40+ LLMs** de los principales proveedores
- Stack 100% moderno (Next.js, Vercel AI SDK)
- Gratis y deployable en tu propia infraestructura

---

## Modos de Búsqueda (17)

| Modo | Descripción |
|------|-------------|
| **Web** | Búsqueda web general con fuentes |
| **Chat** | Conversación con IA pura |
| **X (Twitter)** | Búsqueda en tiempo real en X/Twitter |
| **Stocks** | Datos financieros y análisis bursátil |
| **Code** | Búsqueda y generación de código |
| **Academic** | Búsqueda en papers académicos y arXiv |
| **Extreme** | Búsqueda en profundidad con múltiples fuentes |
| **Reddit** | Búsqueda en hilos de Reddit |
| **GitHub** | Búsqueda en repositorios de código |
| **Crypto** | Datos de criptomonedas en tiempo real |
| **Prediction** | Mercados de predicción |
| **YouTube** | Búsqueda y análisis de videos |
| **Spotify** | Búsqueda de música |
| **Connectors** | Integración con servicios externos |
| **Memory** | Memoria persistente entre sesiones |
| **Voice** | Entrada y salida de voz |
| **XQL** | Queries estructuradas para X/Twitter |

---

## Herramientas Integradas (28+)

| Herramienta | Descripción |
|-------------|-------------|
| `search` | Búsqueda web vía Exa AI o Tavily |
| `stock_data` | Precios y datos financieros (Yahoo Finance) |
| `weather` | Clima actual y pronóstico |
| `maps` | Búsqueda de lugares y direcciones |
| `movies_tv` | Datos de películas/series (TMDB) |
| `code_execution` | Ejecuta código Python en sandbox |
| `translation` | Traducción multilenguaje |
| `crypto_data` | Precios cripto (CoinGecko) |
| `academic_search` | Papers de arXiv |
| `youtube_search` | Videos de YouTube |
| `reddit_search` | Posts y comentarios de Reddit |
| `github_search` | Repositorios y código |
| `prediction_markets` | Datos de Polymarket |

---

## LLMs Soportados (40+)

### xAI / Grok
- Grok 3, Grok 3 Fast, Grok 4

### OpenAI
- GPT-4.1, GPT-5, o3, o4-mini, o4

### Anthropic
- Claude Sonnet 4.5, Claude 4.6, Claude 3.7

### Google
- Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 3

### Meta / Open Source
- DeepSeek R1, V3
- Mistral Large, Codestral
- Cohere Command R+
- Qwen 3, QwQ
- ByteDance Seed
- MoonShot Kimi K2
- Y 20+ modelos más

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Framework | Next.js 14+ |
| AI SDK | Vercel AI SDK |
| Búsqueda web | Exa AI + Tavily + Firecrawl |
| Cache/Rate limit | Upstash Redis |
| Datos financieros | Yahoo Finance, CoinGecko |
| Datos entretenimiento | TMDB |
| Música | Spotify API |
| Deploy | Vercel (recomendado) |
| Auth | Clerk |
| DB | Neon PostgreSQL |

---

## Instalación

### Prerequisitos
- Node.js 18+
- pnpm
- Cuentas en: OpenAI/Anthropic/xAI (al menos una), Exa AI o Tavily

### Desarrollo local
```bash
# Clonar repositorio
git clone https://github.com/zaidmukaddam/scira.git
cd scira

# Instalar dependencias
pnpm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus API keys

# Iniciar servidor de desarrollo
pnpm dev
```

Acceder en: http://localhost:3000

### Deploy en Vercel (un clic)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/zaidmukaddam/scira)

### Docker Compose
```bash
docker compose up -d
```

---

## Variables de Entorno Clave

```env
# LLM Providers (al menos uno requerido)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=...
GOOGLE_GENERATIVE_AI_API_KEY=...

# Búsqueda (requerido)
EXA_API_KEY=...           # https://exa.ai
TAVILY_API_KEY=...        # https://tavily.com
FIRECRAWL_API_KEY=...     # https://firecrawl.dev (opcional)

# Cache
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...

# Autenticación
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...
CLERK_SECRET_KEY=...

# Base de datos
DATABASE_URL=postgresql://...

# Datos
TMDB_API_KEY=...          # Para películas/series
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

---

## Uso para Trading e Investigación Financiera

Scira es especialmente útil para:

### Modo Stocks — Análisis Financiero
- Búsqueda de datos en tiempo real de acciones, ETFs, índices
- Análisis de estados financieros con IA
- Noticias y sentimiento del mercado

### Modo Academic — Research Cuantitativo
- Búsqueda en papers de q-fin (quantitative finance)
- Análisis de estrategias publicadas
- Literatura sobre trading algorítmico

### Modo Extreme — Due Diligence
- Análisis profundo con múltiples fuentes
- Útil para análisis fundamental de activos
- Recopilación de información macro

### Ejemplo de uso en Stocks Mode
```
Query: "XAUUSD technical analysis and gold price forecast"
→ Retorna: precio actual, gráficos, noticias recientes, análisis técnico,
  consenso de analistas, con fuentes verificadas
```

---

## Estructura del Proyecto

```
scira/
├── app/                     # Next.js App Router
│   ├── (chat)/              # Chat interface
│   ├── api/                 # API routes
│   └── layout.tsx           # Root layout
├── components/              # React components
│   ├── search-results/      # Resultados de búsqueda
│   ├── stock-chart/         # Gráficos financieros
│   └── weather-widget/      # Widget clima
├── lib/
│   ├── tools/               # Herramientas de IA (28+)
│   └── models.ts            # Configuración de LLMs
├── public/                  # Assets estáticos
└── docker-compose.yml       # Config Docker
```

---

## Comparativa con Perplexity

| Característica | Scira | Perplexity |
|----------------|-------|-----------|
| Código abierto | ✅ AGPL-3.0 | ❌ Propietario |
| Self-hosted | ✅ Sí | ❌ No |
| LLMs soportados | 40+ | ~10 |
| Modos búsqueda | 17 | ~5 |
| Gratuito | ✅ Self-host | ⚠️ Limitado |
| Datos financieros | ✅ Modo Stocks | ✅ Pro |
| Code execution | ✅ Sí | ✅ Pro |

---

*Última actualización: 2026-05-05 | Extraído de: https://github.com/zaidmukaddam/scira*
