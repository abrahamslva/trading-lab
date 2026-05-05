# Gold XAUUSD — Base de Conocimiento

Información central sobre el mercado del oro para referencia de trading algorítmico.

---

## Estructura de esta carpeta

```
gold_xauusd/
├── README.md          # Este archivo
├── data/              # Datos históricos OHLCV, CSV, Parquet
├── strategies/        # Estrategias de trading para XAUUSD
├── indicators/        # Indicadores técnicos y su configuración
└── news/              # Noticias y análisis fundamentales guardados
```

---

## Datos Pendientes de Cargar

El archivo `Base de datos XAUUSD.zip` contiene información histórica y estrategias.
Para cargarlo en esta base de datos:

```bash
# 1. Copia el ZIP al workspace (desde tu computadora)
cp "/ruta/a/Base de datos XAUUSD.zip" /workspaces/trading-lab/knowledge_base/gold_xauusd/

# 2. Extrae el contenido
cd /workspaces/trading-lab/knowledge_base/gold_xauusd/
unzip "Base de datos XAUUSD.zip"

# 3. Organiza los archivos según tipo
# - Datos históricos → data/
# - Estrategias      → strategies/
# - Indicadores      → indicators/
```

---

## Contexto del Mercado de Oro (XAUUSD)

### Características del Activo
- **Símbolo:** XAU/USD (oro spot en USD por troy onza)
- **Símbolo futuros:** GC=F (CME - COMEX)
- **Horario principal:** 24h (Domingo 23:00 UTC — Viernes 22:00 UTC)
- **Spread típico:** 0.2–0.5 pips (brokers ECN)
- **Tick size:** 0.01 USD
- **1 lote:** 100 troy onzas

### Factores Fundamentales que Mueven el Oro
| Factor | Impacto | Dirección |
|--------|---------|-----------|
| Inflación alta | Fuerte | ↑ Oro sube |
| Dólar fuerte (DXY ↑) | Fuerte | ↓ Oro baja |
| Tasas de interés reales ↑ | Fuerte | ↓ Oro baja |
| Riesgo geopolítico | Moderado | ↑ Oro sube (safe haven) |
| Demanda de bancos centrales | Moderado | ↑ Oro sube |
| Rendimientos bonos EEUU ↑ | Moderado | ↓ Oro baja |
| Recesión / crisis | Fuerte | ↑ Oro sube |

### Correlaciones Clave
| Activo | Correlación con XAUUSD |
|--------|------------------------|
| DXY (USD Index) | Negativa (-0.7 a -0.9) |
| Silver (XAGUSD) | Positiva alta (+0.85) |
| S&P 500 (crisis) | Negativa en crisis |
| US10Y (rendimiento) | Negativa (-0.6 a -0.8) |
| EUR/USD | Positiva moderada |
| Bitcoin | Variable |

---

## Indicadores Técnicos Comúnmente Usados en Oro

### Tendencia
- **EMA 200** — Línea de tendencia principal
- **EMA 50 / EMA 20** — Tendencia de mediano/corto plazo
- **MACD (12,26,9)** — Momentum y señales de cruce
- **Ichimoku Cloud** — Sistema completo de tendencia + soporte/resistencia

### Osciladores
- **RSI (14)** — Sobrecompra (>70) / Sobreventa (<30)
- **Stochastic (5,3,3)** — Señales de reversión en rangos
- **CCI (20)** — Divergencias y condiciones extremas

### Volatilidad
- **ATR (14)** — Volatilidad media para sizing y stops
- **Bollinger Bands (20,2)** — Compresión/expansión de rango

### Volumen (si disponible)
- **OBV** — On-Balance Volume
- **Volume Profile** — Zonas de alto interés institucional

---

## Niveles Técnicos Históricos Importantes

Los niveles psicológicos clave (resistencias/soportes redondos) del oro:
- $1,000, $1,500, $1,800, $2,000, $2,500, $3,000, $3,500

---

## Scripts Útiles del Proyecto

| Script | Ubicación | Función |
|--------|-----------|---------|
| Carga de datos Dukascopy | `src/dukascopy_loader.py` | Descarga datos históricos |
| Pipeline de datos | `src/data_pipeline.py` | Procesamiento y limpieza |
| Backtest | `src/run_backtest.py` | Ejecutar backtests |
| Optimización | `src/optimize.py` | Optimización de parámetros |
| Estrategia MA Cross | `src/strategies/ma_cross.py` | Cruce de medias móviles |
| LEAN Validation | `src/run_lean_validation.sh` | Validación con QuantConnect LEAN |
| Gold Algorithm (LEAN) | `lean_project/GoldAlgorithm.py` | Algoritmo para LEAN |
| MT5 Connector | `mt5/mt5_connector.py` | Conexión con MetaTrader 5 |
| Gold EA (MT5) | `mt5/GoldEA.mq5` | Expert Advisor de oro |

---

*Última actualización: 2026-05-05*
