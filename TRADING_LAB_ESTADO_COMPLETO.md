# TRADING LAB — Estado Completo del Proyecto
**Última actualización:** 2026-05-07  
**Repo:** https://github.com/abrahamslva/trading-lab  
**Branch:** main  
**Workspace:** /workspaces/trading-lab  
**Desktop doc:** /home/codespace/Desktop/TRADING_LAB_ESTADO_COMPLETO.md

> ⚠️ Este documento se mantiene sincronizado con el repositorio y el workspace.
> Toda modificación se aplica en los 3 lugares simultáneamente.

---

## 📊 Estado de Datos XAUUSD M15

### Archivos de Datos Disponibles

| Archivo | Barras | Rango | Tamaño | Estado |
|---------|--------|-------|--------|--------|
| `data/dukascopy/XAUUSD_15min_mt5.parquet` | **170,701** | **2016-01-04 → 2026-05-06** | **7.1 MB** | ✅ **COMPLETO — 10.3 años** |
| `data/dukascopy/XAUUSD_15min_yfinance.parquet` | 2,598 | 2016-01-04 → 2026-05-05 | 0.1 MB | ✅ Referencia diaria |
| `data/dukascopy/XAUUSD_15min_yfinance_real.parquet` | 1,998 | 2026-04-06 → 2026-05-06 | 0.1 MB | ✅ Más reciente |

### Extensión Trimestral Descargada (2024-07 → 2026-05) — ✅ MERGEADA en mt5.parquet

| Archivo | Barras | Rango |
|---------|--------|-------|
| `tmp_quarters/XAUUSD_15min_2024-07-01_2024-10-01.parquet` | 6,052 | Q3 2024 |
| `tmp_quarters/XAUUSD_15min_2024-10-01_2025-01-01.parquet` | 5,905 | Q4 2024 |
| `tmp_quarters/XAUUSD_15min_2025-01-01_2025-04-01.parquet` | 5,784 | Q1 2025 |
| `tmp_quarters/XAUUSD_15min_2025-04-01_2025-07-01.parquet` | 5,868 | Q2 2025 |
| `tmp_quarters/XAUUSD_15min_2025-07-01_2025-10-01.parquet` | 6,046 | Q3 2025 |
| `tmp_quarters/XAUUSD_15min_2025-10-01_2026-01-01.parquet` | 5,940 | Q4 2025 |
| `tmp_quarters/XAUUSD_15min_2026-01-01_2026-04-01.parquet` | 5,756 | Q1 2026 |
| `tmp_quarters/XAUUSD_15min_2026-04-01_2026-05-07.parquet` | 2,300 | Apr-May 2026 |

### Resumen Total de Datos

```
✅ DESCARGA COMPLETADA — 2026-05-07 (42.6 min total)

ARCHIVO FINAL: data/dukascopy/XAUUSD_15min_mt5.parquet
TOTAL: 170,701 barras M15
RANGO: 2016-01-04 → 2026-05-06
TAMAÑO: 7.1 MB
COBERTURA: 10.3 años completos
BACKUP: XAUUSD_15min_mt5.parquet.bak

Descarga por chunks:
  Q3 2024: 6,052 barras (328s) | Q4 2024: 5,905 barras (404s)
  Q1 2025: 5,784 barras (317s) | Q2 2025: 5,868 barras (322s)
  Q3 2025: 6,046 barras (341s) | Q4 2025: 5,940 barras (332s)
  Q1 2026: 5,756 barras (384s) | Apr-May 2026: 2,300 barras (129s)
  TOTAL NUEVO: 43,651 barras agregadas
```

### Log de Descarga
- Descarga inicial detectó **82.1% completado** (127,050 barras hasta 2024-06-28)
- Se descargaron **4 chunks de 6 meses** para extender hasta 2025-12-31
- Dato más reciente disponible vía yfinance_real: 2026-05-06

---

## 🗂️ Estructura del Workspace

```
/workspaces/trading-lab/
├── README.md
├── setup.sh
├── .devcontainer/
│   └── devcontainer.json
├── configs/
│   ├── backtest.yaml
│   ├── data.yaml
│   ├── mt5.yaml
│   └── objectives.yaml
├── data/
│   ├── catalogs/              ← 5 JSON/TXT con bases de datos de repos
│   ├── dukascopy/             ← Datos XAUUSD M15 (parquets)
│   │   ├── XAUUSD_15min_mt5.parquet        (127k barras, 5.2MB)
│   │   ├── XAUUSD_15min_yfinance.parquet   (2,598 barras)
│   │   ├── XAUUSD_15min_yfinance_real.parquet (1,998 barras)
│   │   └── tmp_quarters/      ← 6 parquets Q3-2024 → Q4-2025
│   ├── lean-data/
│   └── logs/                  ← download.log, backtest.log, etc.
├── docs/
│   ├── catalogs/              ← CATALOGO_MAESTRO_38_REPOS.md, guías
│   ├── guides/                ← MT5, backtesting, comandos rápidos
│   └── sessions/              ← Resúmenes de sesiones de trabajo
├── external_repos/            ← 45+ repos clonados con --depth 1
├── knowledge_base/
│   ├── apis_reference/        ← trading_apis.md
│   ├── github_repos/          ← 9 READMEs documentados
│   └── gold_xauusd/           ← Análisis, estrategias, EAs MQ5
├── mt5/
│   ├── GoldEA.mq5
│   ├── mt5_connector.py
│   ├── signal_writer.py
│   ├── export/                ← Scripts de exportación MT5
│   ├── setup/                 ← Scripts PowerShell/BAT instalación
│   └── bridge/
├── notebooks/
├── results/                   ← CSVs y JSONs de backtests
├── src/
│   ├── backtest_full.py
│   ├── backtest_volume_fusion.py
│   ├── data_pipeline.py
│   ├── download_data.py
│   ├── dukascopy_loader.py
│   ├── optimize.py
│   ├── run_backtest.py
│   ├── backtesting/           ← 5 scripts de backtesting
│   ├── integration/           ← SAFLA, Guardrail integration
│   ├── strategies/            ← ma_cross.py
│   └── tools/                 ← monitor, update_historical, catalogs
└── strategies/
    ├── lean/                  ← GoldAlgorithm.py, config.json
    ├── mt5/                   ← GoldEA v1, v3, v4 (.mq5)
    └── python/                ← gold_volume_fusion_v1_original.py
```

---

## 📦 Repositorios Externos Clonados (external_repos/)

### AI / Agentes
| Repo | Descripción | Stars |
|------|-------------|-------|
| AutoGPT | Plataforma de agentes IA autónomos | ~184k |
| agent-zero | Framework agentes con acceso Linux total | ~17.6k |
| big-AGI | Workspace multi-modelo, Beam & Merge | ~7k |
| browser-use | Automatización de navegador con IA | ~92.5k |
| skyvern | LLM + visión computacional para web | ~21.5k |
| Jobs_Applier_AI_Agent_AIHawk | Automatización formularios (ARCHIVADO) | ~29.8k |
| scira | Motor de búsqueda IA con stocks/crypto | ~11.6k |
| agency-agents | Orquestación de agentes | - |
| agentic-flow | AI model switching | ~682 |
| hello_world_agent | Agente de ejemplo | ~99 |
| GenAI-Superstream | Agentic data engineering | ~57 |

### Trading / Backtesting
| Repo | Descripción |
|------|-------------|
| freqtrade | Bot de trading open source (cripto) |
| backtrader | Framework de backtesting Python |
| backtesting | Librería backtesting Python |
| zipline | Motor de backtesting de Quantopian |
| rqalpha | Motor de backtesting chino |
| AQTrading | Algoritmos de trading cuantitativo |
| quant-trading | Estrategias de trading cuantitativo |
| machine-learning-for-trading | ML aplicado a trading |
| tvDatafeed | Datos de TradingView |
| python-binance | SDK Binance para Python |
| alpaca-trade-api-python | SDK Alpaca Markets |

### ML / Data Science
| Repo | Descripción |
|------|-------------|
| yfinance | Yahoo Finance data downloader |
| pandas-datareader | Readers de datos financieros |
| mplfinance | Gráficos financieros con matplotlib |
| plotly | Gráficos interactivos |
| hyperopt | Optimización bayesiana |
| optuna | Framework de optimización |
| ta-lib | Análisis técnico (C library bindings) |
| scrapling | Web scraping avanzado |
| public-apis | Directorio de APIs públicas |

### ruvnet (Herramientas IA)
| Repo | Descripción |
|------|-------------|
| ruflo | Orquestación de agentes IA |
| SAFLA | Feedback loop adaptativo para trading |
| guardrail | Data analysis + AI |
| FACT | Context augmentation tools |
| Bot-Generator-Bot | Generador de trading bots |
| QuDAG | AI + protocolo cuántico |
| RuVector | Librería de redes neuronales |
| SynthLang | Lenguaje eficiente para prompts |
| dspy.ts | Declarative AI en JS |
| voicebot | Bot de voz para trading |
| rUv-dev | Herramientas de dev IA |
| ruvbot | Asistente de trading |

### Otros
| Repo | Descripción |
|------|-------------|
| atlas-gic | Atlas GIC integration |
| Gekko | Bot de trading BTC (legacy) |

---

## 📚 Knowledge Base — Repositorios Documentados

| # | Repo | Descripción | Stars | README |
|---|------|-------------|-------|--------|
| 1 | TauricResearch/TradingAgents | Framework multi-agente LLM trading | ~69.2k | [ver](knowledge_base/github_repos/trading_agents/README.md) |
| 2 | public-apis/public-apis | 1,000+ APIs públicas en 51 categorías | ~432k | [ver](knowledge_base/github_repos/public_apis/README.md) |
| 3 | Significant-Gravitas/AutoGPT | Plataforma agentes IA autónomos | ~184k | [ver](knowledge_base/github_repos/autogpt/README.md) |
| 4 | zaidmukaddam/scira | Motor búsqueda IA + stocks/crypto | ~11.6k | [ver](knowledge_base/github_repos/scira/README.md) |
| 5 | agent0ai/agent-zero | Framework agentes con acceso Linux | ~17.6k | [ver](knowledge_base/github_repos/agent_zero/README.md) |
| 6 | enricoros/big-AGI | Workspace multi-modelo Beam & Merge | ~7k | [ver](knowledge_base/github_repos/big_agi/README.md) |
| 7 | browser-use/browser-use | Automatización navegador con IA | ~92.5k | [ver](knowledge_base/github_repos/browser_use/README.md) |
| 8 | Skyvern-AI/skyvern | LLM + visión web automation | ~21.5k | [ver](knowledge_base/github_repos/skyvern/README.md) |
| 9 | feder-cr/Jobs_Applier_AI_Agent | Formularios con IA (ARCHIVADO) | ~29.8k | [ver](knowledge_base/github_repos/jobs_applier_ai_agent/README.md) |

---

## 🔑 APIs Documentadas (knowledge_base/apis_reference/)

**Archivo:** `knowledge_base/apis_reference/trading_apis.md`  
**Archivo completo:** `knowledge_base/github_repos/public_apis/README.md` (1,000+ APIs, 51 categorías)

### APIs Clave para XAUUSD Trading

| Categoría | API | Auth | URL |
|-----------|-----|------|-----|
| **Precio Oro** | Alpha Vantage | apiKey gratis | alphavantage.co |
| **Precio Oro** | Twelve Data | apiKey gratis | twelvedata.com |
| **Precio Oro** | Finnhub | apiKey gratis | finnhub.io |
| **Precio Oro** | Yahoo Finance (yfinance) | No | pypi: yfinance |
| **Macro EEUU** | FRED Federal Reserve | apiKey gratis | fred.stlouisfed.org |
| **Forex/DXY** | Frankfurter | **Sin auth** | frankfurter.app |
| **Forex/DXY** | Currency-api | **Sin auth** | cdnjs API |
| **Cripto** | CoinGecko | **Sin auth** | coingecko.com/api |
| **Noticias** | MarketAux | apiKey | marketaux.com |
| **Noticias** | Finnhub News | apiKey | finnhub.io |
| **Noticias** | GNews | apiKey | gnews.io |
| **Sentimiento** | WallstreetBets | **Sin auth** | wsb sentiment |
| **Economic Cal.** | Investing.com | scraping | - |

---

## 🤖 Estrategias de Trading Implementadas

### Expert Advisors MT5 (MQL5)

| EA | Timeframe | Archivo | Estado |
|----|-----------|---------|--------|
| GoldVolumeFusionElite v1 | M15 | `strategies/mt5/v1/EA_XAUUSD_GoldVolumeFusionElite_v1.mq5` | ✅ |
| GoldVolumeFusionElite v3 | M15 | `strategies/mt5/v3/EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5` | ✅ |
| GoldVolumeFusionElite v4 | M15 | `strategies/mt5/v4/EA_XAUUSD_GoldVolumeFusionElite_v4_M15.mq5` | ✅ |
| GoldEA | M15 | `strategies/mt5/GoldEA.mq5` | ✅ |
| MACD Ribbon | 1H/2H/4H | `knowledge_base/gold_xauusd/strategies/MACD_Ribbon/` | ✅ |
| VMC B LongOnly | 1H/2H/3H/4H | `knowledge_base/gold_xauusd/strategies/VMC_B_LongOnly/` | ✅ |
| Ruptura Momento | 5M/15M/1H/2H/3H/4H | `knowledge_base/gold_xauusd/strategies/Ruptura_Momento/` | ✅ |
| Asian Breakout | - | `knowledge_base/gold_xauusd/market_analysis/volumen_horario/EA_XAUUSD_Strategy1_AsianBreakout.mq5` | ✅ |
| OB Volume Profile | - | `knowledge_base/gold_xauusd/market_analysis/volumen_horario/EA_XAUUSD_Strategy2_OBVolumeProfile.mq5` | ✅ |
| Macro Swing | - | `knowledge_base/gold_xauusd/market_analysis/volumen_horario/EA_XAUUSD_Strategy3_MacroSwing.mq5` | ✅ |

### Estrategias Python

| Estrategia | Archivo | Descripción |
|------------|---------|-------------|
| GoldVolumeFusion v1 | `strategies/python/gold_volume_fusion_v1_original.py` | Versión original Python |
| MA Cross | `src/strategies/ma_cross.py` | Cruce de medias móviles |
| GoldAlgorithm (Lean) | `strategies/lean/GoldAlgorithm.py` | QuantConnect LEAN |
| Quantum Fusion | `knowledge_base/gold_xauusd/strategies/Quantum_Fusion/` | Sistema multi-versión |
| Cypher | `knowledge_base/gold_xauusd/strategies/Cypher/` | CipherB LongOnly |

---

## 📈 Resultados de Backtesting

| Archivo | Descripción | Última ejecución |
|---------|-------------|-----------------|
| `results/backtest_all_strategies_2016_2024.csv` | Todas las estrategias 2016-2024 | ✅ |
| `results/backtest_full_results.csv` | Backtest completo | ✅ |
| `results/backtest_m15_real_yfinance.csv` | M15 con datos reales yfinance | ✅ |
| `results/backtest_volume_fusion_results.csv` | GoldVolumeFusion específico | ✅ |
| `results/backtest_v3_2016_2024_multiframe.csv` | v3 multiframe 2016-2024 | ✅ |
| `results/best_params_volume_fusion.json` | Mejores params optimizados | ✅ |
| `results/backtest_full_params.json` | Params completos | ✅ |
| `results/REPORTE_FINAL_GoldVolumeFusionElite.md` | Reporte final completo | ✅ |

---

## ⚙️ Configuraciones

| Archivo | Contenido |
|---------|-----------|
| `configs/backtest.yaml` | Parámetros de backtesting |
| `configs/data.yaml` | Fuentes y paths de datos |
| `configs/mt5.yaml` | Configuración MT5 |
| `configs/objectives.yaml` | Objetivos de optimización |
| `strategies/mt5/backtest_config.ini` | Config backtest MT5 |

---

## 🛠️ Scripts Principales

### Descarga de Datos
```bash
# Actualizar datos históricos (background)
python3 src/tools/update_historical_data.py

# Descargar yfinance M15 actual
python3 src/tools/download_yfinance_m15_current.py

# Pipeline completo
python3 src/data_pipeline.py
```

### Backtesting
```bash
# Backtest completo
python3 src/backtest_full.py

# Backtest GoldVolumeFusion
python3 src/backtest_volume_fusion.py

# Backtest M15 con yfinance real
python3 src/backtesting/backtest_m15_real_yfinance.py

# Todas las estrategias 2016-2024
python3 src/backtesting/backtest_all_strategies_2016_2024.py
```

### MT5 Setup (Windows)
```powershell
# Instalar EA completo
.\mt5\setup\Instalar_GoldVFE_MT5.ps1

# Setup completo MT5 Windows
.\mt5\setup\Setup_MT5_Windows.ps1

# Exportar historial desde MT5
python3 mt5/export/export_history.py
```

### Monitoreo
```bash
# Monitor en tiempo real
python3 src/tools/monitor_realtime.py

# Monitor y autotest
python3 src/tools/monitor_and_autotest.py
```

### Git
```bash
# Commit rápido
cd /workspaces/trading-lab
git add -A && git commit -m "descripción" && git push origin main
```

---

## 📋 Guías y Documentación

| Documento | Ruta |
|-----------|------|
| Quick Reference general | `docs/guides/QUICK_REFERENCE.md` |
| Guía Backtesting MT5 | `docs/guides/INSTRUCCIONES_BACKTESTING_MT5.md` |
| Fast Download Windows MT5 | `docs/guides/FAST_DOWNLOAD_WINDOWS_MT5.md` |
| Quick Commands MT5 | `docs/guides/QUICK_COMMANDS_WINDOWS_MT5.md` |
| Catálogo 38 Repos | `docs/catalogs/CATALOGO_MAESTRO_38_REPOS.md` |
| Guía Repos Integrados | `docs/catalogs/INTEGRATED_REPOS_GUIDE.md` |
| Atlas GIC Integration | `docs/sessions/ATLAS_GIC_INTEGRATION.md` |
| Data Completeness Update | `docs/sessions/DATA_COMPLETENESS_UPDATE.md` |
| Sesión Final Resumen | `docs/sessions/SESION_FINAL_RESUMEN.md` |
| Resumen Integración Completo | `docs/sessions/RESUMEN_INTEGRACION_COMPLETO.md` |
| Biblia del Oro | `knowledge_base/gold_xauusd/market_analysis/volumen_horario/biblia_oro.txt` |
| Guía Backtesting XAUUSD | `knowledge_base/gold_xauusd/market_analysis/volumen_horario/GUIA_BACKTESTING_XAUUSD.txt` |

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADING LAB SYSTEM                        │
├────────────────┬────────────────┬───────────────────────────┤
│   DATA LAYER   │  STRATEGY LAYER│      EXECUTION LAYER      │
│                │                │                           │
│ • Dukascopy    │ • MA Cross      │ • MT5 EA (MQL5)           │
│   M15 parquet  │ • GoldVolFusion │ • Python backtesting      │
│ • yfinance     │ • MACD Ribbon   │ • QuantConnect LEAN       │
│   (daily/M15)  │ • VMC B Long    │ • MT5 signal_writer.py    │
│ • FRED API     │ • Ruptura Mom.  │                           │
│ • CoinGecko    │ • Quantum Fus.  │  OPTIMIZATION             │
│ • Forex APIs   │ • Cypher        │ • Optuna                  │
│                │ • Asian Break.  │ • Hyperopt                │
├────────────────┴────────────────┴───────────────────────────┤
│                    AI / AGENTS LAYER                         │
│ • TradingAgents (multi-agente LLM)                           │
│ • AutoGPT (plataforma agentes)                               │
│ • Agent Zero (acceso Linux)                                  │
│ • browser-use (automatización web)                           │
│ • Skyvern (visión + LLM)                                     │
│ • SAFLA (feedback loop)                                      │
│ • Guardrail (validación)                                     │
├─────────────────────────────────────────────────────────────┤
│                  KNOWLEDGE BASE                              │
│ • 9 repos documentados │ 51 categorías APIs │ Biblia Oro    │
│ • 45+ repos externos   │ 10+ EAs MT5        │ Análisis XAUUSD│
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Catálogos de Datos

| Archivo | Descripción |
|---------|-------------|
| `data/catalogs/complete_catalog_38_repos.json` | Catálogo completo de 38 repos |
| `data/catalogs/trading_curated_database.json` | Base de datos curada de repos trading |
| `data/catalogs/trading_repos_database.json` | Database de repos |
| `data/catalogs/trading_priority_index.json` | Índice de prioridad |
| `data/catalogs/creator_profiles_analysis.json` | Análisis de perfiles de creadores |
| `data/catalogs/trading_research_report.txt` | Reporte de investigación |

---

## 🔄 Historial de Cambios Recientes

| Fecha | Cambio |
|-------|--------|
| 2026-05-07 | ✅ Descarga COMPLETA: 170,701 barras M15 (2016-2026), 10.3 años, 7.1MB |
| 2026-05-07 | 43,651 barras nuevas mergeadas (Q3-2024 → May-2026, 42.6 min) |
| 2026-05-07 | Documento de escritorio creado: TRADING_LAB_ESTADO_COMPLETO.md |
| 2026-05-05 | Agregados 7 repos IA: AutoGPT, Scira, Agent Zero, big-AGI, browser-use, Skyvern, AIHawk |
| 2026-05-05 | knowledge_base/public_apis completada con 51 categorías (1,000+ APIs) |
| 2026-05-05 | knowledge_base/github_repos/README.md actualizado a 9 repos |
| 2026-05-05 | external_repos: 45+ repos clonados |
| 2026-05-04 | Estrategias MT5 v1, v3, v4 creadas |
| 2026-05-04 | Backtesting completo 2016-2024 ejecutado |
| 2026-05-04 | Pipeline de datos XAUUSD M15 configurado |

---

## ⚡ Comandos de Acceso Rápido

```bash
# Ir al workspace
cd /workspaces/trading-lab

# Ver estado de datos
python3 -c "
import pandas as pd; from pathlib import Path
df = pd.read_parquet('data/dukascopy/XAUUSD_15min_mt5.parquet')
print(f'{len(df):,} barras | {df.index[0]} → {df.index[-1]}')
"

# Ver este documento
cat /home/codespace/Desktop/TRADING_LAB_ESTADO_COMPLETO.md

# Actualizar este documento y pushear
# (Copilot lo hace automáticamente en cada sesión)

# Estado git
git log --oneline -10

# Último backtest
cat results/REPORTE_FINAL_GoldVolumeFusionElite.md | head -50
```

---

*Documento mantenido automáticamente por GitHub Copilot*  
*Repo: abrahamslva/trading-lab | Branch: main*
