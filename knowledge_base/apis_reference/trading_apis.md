# APIs de Referencia para Trading de Oro (XAUUSD)

Guía rápida de APIs gratuitas y de bajo costo relevantes para construir sistemas de trading algorítmico sobre el oro.

---

## APIs de Precio del Oro

### Alpha Vantage
- **URL:** https://www.alphavantage.co/
- **Endpoint XAUUSD:** `https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=XAU&to_symbol=USD&apikey=YOUR_KEY`
- **Auth:** apiKey gratuita (25 req/día en plan free)
- **Datos:** OHLCV diario, semanal, mensual, intraday
- **Uso en este proyecto:** Ver `configs/data.yaml`

### Twelve Data
- **URL:** https://twelvedata.com/
- **Endpoint:** `https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1day&apikey=YOUR_KEY`
- **Auth:** apiKey (800 req/día en plan free)
- **Datos:** Series temporales, indicadores técnicos integrados

### Finnhub
- **URL:** https://finnhub.io/
- **Endpoint:** `https://finnhub.io/api/v1/forex/candle?symbol=OANDA:XAU_USD&resolution=D&from=...&to=...&token=YOUR_KEY`
- **Auth:** apiKey (60 req/minuto en plan free)
- **Datos:** Candles FOREX, noticias, sentimiento

### Yahoo Finance (yfinance)
```python
import yfinance as yf
gold = yf.download("GC=F", start="2020-01-01", end="2024-01-01")  # Futuros de oro
# o
gold = yf.download("XAUUSD=X", start="2020-01-01")  # Spot
```
- **Auth:** Ninguna (sin API key)
- **Límites:** No oficial, puede cambiar

---

## APIs de Datos Macroeconómicos

### FRED (Federal Reserve Economic Data)
- **URL:** https://fred.stlouisfed.org/docs/api/fred/
- **Auth:** apiKey gratuita
- **Series clave para oro:**

| Serie FRED | Descripción |
|------------|-------------|
| `GOLDAMGBD228NLBM` | Precio del oro (AM fixing, USD/troy oz) |
| `GOLDPMGBD228NLBM` | Precio del oro (PM fixing, USD/troy oz) |
| `DFF` | Federal Funds Rate efectiva |
| `T10YIE` | Tasa de inflación implícita a 10 años |
| `DTWEXBGS` | Índice del dólar ponderado por comercio |
| `CPIAUCSL` | Índice de Precios al Consumidor (CPI) |
| `VIXCLS` | Índice VIX de volatilidad |

```python
import requests
url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GOLDAMGBD228NLBM&api_key=YOUR_KEY&file_type=json"
```

---

## APIs de Noticias Financieras

### MarketAux
- **URL:** https://www.marketaux.com/
- **Auth:** apiKey (100 req/día free)
- **Endpoint:** `https://api.marketaux.com/v1/news/all?symbols=XAUUSD&filter_entities=true&api_token=YOUR_KEY`
- **Datos:** Noticias con sentiment score, tickers etiquetados

### Finnhub News
```python
import finnhub
client = finnhub.Client(api_key="YOUR_KEY")
news = client.general_news('forex', min_id=0)
```

---

## APIs de Tipos de Cambio (Contexto DXY)

### Frankfurter (Gratuita, sin key)
```python
import requests
r = requests.get("https://api.frankfurter.app/latest?from=USD&to=EUR,GBP,JPY,CHF")
data = r.json()
```

### ExchangeRate-API
- **URL:** https://www.exchangerate-api.com/
- **Free:** 1,500 req/mes
- **Auth:** apiKey

---

## Configuración Rápida (.env sugerido)

```bash
# Copia esto en /workspaces/trading-lab/.env

# Datos de mercado
ALPHA_VANTAGE_API_KEY=tu_key_aqui
TWELVE_DATA_API_KEY=tu_key_aqui
FINNHUB_API_KEY=tu_key_aqui

# Datos macro
FRED_API_KEY=tu_key_aqui

# Noticias
MARKETAUX_API_KEY=tu_key_aqui

# LLMs (para TradingAgents)
OPENAI_API_KEY=tu_key_aqui
ANTHROPIC_API_KEY=tu_key_aqui
```

---

## Fuentes de Datos Históricas (Sin API)

| Fuente | URL | Formato | Cobertura |
|--------|-----|---------|-----------|
| Dukascopy | https://www.dukascopy.com/swiss/english/marketwatch/historical/ | JnlpBin/CSV | Tick, M1, H1, D1 |
| Stooq | https://stooq.com/ | CSV | Diario |
| Investing.com | https://www.investing.com/ | CSV (manual) | Multi-TF |
| Yahoo Finance | https://finance.yahoo.com/ | CSV/yfinance | Diario+ |
| Quandl/Nasdaq | https://data.nasdaq.com/ | API | Múltiple |

---

*Última actualización: 2026-05-05*
