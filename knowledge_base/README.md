# Trading Lab — Knowledge Base

Base de datos centralizada del workspace `trading-lab`. Contiene información de referencia, datos de mercado, estrategias y recursos de repositorios externos.

---

## Estructura

```
knowledge_base/
├── gold_xauusd/              # Datos e información sobre XAUUSD (Oro)
│   ├── data/                 # Datos históricos OHLCV, CSV, etc.
│   ├── strategies/           # Estrategias creadas para el oro
│   ├── indicators/           # Indicadores técnicos aplicados al oro
│   └── news/                 # Noticias y análisis fundamentales
│
├── github_repos/             # Información extraída de repositorios GitHub
│   ├── public_apis/          # github.com/public-apis/public-apis
│   └── trading_agents/       # github.com/TauricResearch/TradingAgents
│
├── market_analysis/          # Análisis de mercado generales
└── apis_reference/           # Referencia de APIs útiles para trading
```

---

## Cómo agregar datos

### Datos XAUUSD
- Copia archivos de datos históricos en `gold_xauusd/data/`
- Copia estrategias en `gold_xauusd/strategies/`
- Usa el script `src/dukascopy_loader.py` para datos de Dukascopy
- Usa el script `src/data_pipeline.py` para procesamiento

### Repositorios GitHub
- La información ya está extraída y guardada en `github_repos/`
- Para actualizar, re-ejecuta el fetch de Copilot con las URLs

---

## Archivos de datos XAUUSD pendientes

El archivo `Base de datos XAUUSD.zip` fue adjuntado en la conversación pero no pudo ser accedido directamente desde el sistema de archivos del contenedor.

**Para agregar los datos:**
1. Copia el archivo ZIP al workspace: `cp /ruta/en/tu/PC/Base\ de\ datos\ XAUUSD.zip /workspaces/trading-lab/knowledge_base/gold_xauusd/`
2. Extrae: `cd /workspaces/trading-lab/knowledge_base/gold_xauusd && unzip Base\ de\ datos\ XAUUSD.zip`

---

## Fuentes de datos activas

| Fuente | Tipo | Notas |
|--------|------|-------|
| Dukascopy | Histórico tick/OHLCV | `src/dukascopy_loader.py` |
| MetaTrader 5 | Tiempo real + histórico | `mt5/mt5_connector.py` |
| Alpha Vantage | API REST | Requiere API key |
| Yahoo Finance | API REST | Gratuita (límites) |
| FRED (Federal Reserve) | Económico macro | Gratuita |

---

*Última actualización: 2026-05-05*
