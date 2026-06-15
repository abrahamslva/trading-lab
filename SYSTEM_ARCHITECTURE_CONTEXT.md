# SYSTEM_ARCHITECTURE_CONTEXT

## 1. Visión general del proyecto
Trading Bot Nivel 5 (multimodal institucional) orientado a operación autónoma en **oro (XAUUSD/GC)** y **bitcoin (BTC spot/perpetual)**. El sistema integra señales de mercado, on-chain, macroeconomía, noticias y sentimiento para construir decisiones de trading con trazabilidad, control de riesgo y capacidad de reentrenamiento continuo.

### Objetivos de negocio
- Maximizar retorno ajustado al riesgo (Sharpe/Sortino) con límites estrictos de drawdown.
- Mantener operación robusta en condiciones normales y eventos de alta volatilidad.
- Garantizar auditabilidad completa para cumplimiento y análisis post-trade.

### Objetivos técnicos
- Arquitectura modular y desacoplada con procesamiento near real-time.
- Versionado de datos, features, modelos y decisiones.
- MLOps + observabilidad integral para operación 24/7.

---

## 2. Arquitectura técnica estratificada (7 capas)

### Capa 1 — Fuentes de datos (Data Sources)
- Market data: OHLCV, order book, funding rates, open interest.
- On-chain: flujos a exchanges, actividad de whales, MVRV, fees.
- Macro: CPI, NFP, tasas, yields, DXY, VIX, calendario económico.
- Noticias/sentimiento: RSS premium, comunicados oficiales, redes sociales.

### Capa 2 — Ingesta y normalización (Ingestion)
- Conectores batch/streaming con validación de esquemas.
- Estandarización temporal (UTC), deduplicación, imputación y quality checks.
- Persistencia en data lake y cola de eventos.

### Capa 3 — Feature Store multimodal
- Features técnicas, microestructura, macro, NLP y on-chain.
- Feature registry con versionado, lineage y políticas de freshness.
- Reutilización offline/online para entrenamiento e inferencia consistentes.

### Capa 4 — Modelado predictivo
- Ensemble multimodelo: series temporales, clasificación direccional, volatilidad.
- Calibración probabilística y detección de drift.
- Model serving con fallback por criticidad.

### Capa 5 — Motor de decisión y riesgo
- Fusión de señales con score de convicción.
- Position sizing, límites de exposición, VaR, drawdown guards.
- Políticas de bloqueo por eventos extremos o baja calidad de datos.

### Capa 6 — Ejecución inteligente
- Smart Order Routing (SOR) multi-exchange/broker.
- Algoritmos TWAP/VWAP/POV, control de slippage y latencia.
- Estado de órdenes, reconciliación y manejo de fallos.

### Capa 7 — Observabilidad, gobierno y operaciones
- Monitoreo técnico y de negocio, alerting y runbooks.
- Auditoría end-to-end (data/model/decision/order).
- CI/CD, canary release, rollback y planes de continuidad.

---

## 3. Componentes principales (8) y responsabilidades

1. **Data Connector Hub**
   - Administra conectores a exchanges, proveedores macro y feeds NLP.
   - Gestiona retry/backoff, límites de API y contingencias.

2. **Data Quality & Normalization Engine**
   - Reglas de completitud, validez, rango y consistencia temporal.
   - Calcula score de calidad y bloquea datos defectuosos.

3. **Multimodal Feature Store**
   - Publica features versionadas para entrenamiento/inferencia.
   - Garantiza parity offline-online.

4. **Research & Training Workbench**
   - Backtesting, walk-forward, optimización de hiperparámetros.
   - Registro de experimentos y artefactos de modelos.

5. **Prediction Serving Layer**
   - Inferencia en tiempo real con SLA definidos.
   - Gestión de modelos activos, champion/challenger y fallback.

6. **Decision & Risk Engine**
   - Agrega señales en un marco de decisión probabilístico.
   - Define tamaño de posición, hedging y kill-switch.

7. **Execution Management System (EMS)**
   - Envío, split y enrutamiento de órdenes.
   - Verificación pre-trade y reconciliación post-trade.

8. **Monitoring, Audit & Governance Center**
   - Métricas, alertas, paneles operativos y auditoría regulatoria.
   - Gestión de incidentes y análisis post-mortem.

---

## 4. Data pipeline completo
1. **Captura**: eventos de mercado/on-chain/macro/noticias.
2. **Validación inicial**: schema check, timestamps, duplicados.
3. **Normalización**: unidades, zonas horarias, taxonomía de símbolos.
4. **Enriquecimiento**: features técnicas/NLP/on-chain/macro.
5. **Persistencia**:
   - Raw (inmutable)
   - Curated (limpio y estandarizado)
   - Feature tables (consumo ML/RT)
6. **Entrenamiento batch**: datasets etiquetados + evaluación robusta.
7. **Despliegue de modelos**: registro, aprobación, rollout controlado.
8. **Inferencia online**: scoring continuo por activo/horizonte.
9. **Decisión y ejecución**: señal -> riesgo -> orden -> fill.
10. **Feedback loop**: outcomes reales para recalibración/reentrenamiento.

---

## 5. Workflows y procesos

### 5.1 Ciclo diario (operación estándar)
- 00:00 UTC: health-check integral y carga de calendarios.
- Pre-market: recalculo de features y validación de datos.
- Sesión activa: inferencia continua, decisiones y ejecución supervisada.
- Intradía: monitoreo de drift, slippage y límites de riesgo.
- Cierre: conciliación, PnL, reportes y snapshot de estado.

### 5.2 Workflow pre-evento (alto impacto)
- Detección de evento (CPI/FED/NFP, anuncios regulatorios).
- Activación de perfil conservador (menor tamaño, stops más amplios).
- Congelamiento temporal de estrategias sensibles a ruido.
- Reanudación progresiva post-evento según liquidez/volatilidad.

### 5.3 Workflow de reentrenamiento
- Trigger por calendario o degradación de métricas.
- Reentrenamiento con ventana actualizada y selección robusta.
- Validación (out-of-sample, stress, escenarios adversos).
- Promotion champion/challenger con canary y rollback automático.

---

## 6. Métricas de performance

### Trading
- Net return, alpha, Sharpe, Sortino, Calmar.
- Max drawdown, time-under-water, win rate.
- Profit factor, expectancy, turnover.

### Riesgo
- VaR/CVaR intradía y diario.
- Exposición por activo/factor/régimen.
- Concentración y correlación cruzada BTC-XAU.

### Ejecución
- Slippage medio/percentil 95.
- Fill ratio, partial fills, reject rate.
- Latencia señal->orden y orden->fill.

### Modelos
- AUC/F1 (clasificación), MAE/RMSE (regresión).
- Calibration error, feature drift, concept drift.
- Performance decay por régimen.

### Operación
- Uptime, MTTR, incidentes críticos/mes.
- Freshness de datos, retraso por fuente.

---

## 7. Stack tecnológico recomendado

### Lenguajes y runtime
- Python 3.11+ (orquestación, research, ML, riesgo).
- SQL (analytics y validaciones).
- Rust/Go opcional para rutas de baja latencia.

### Datos
- Apache Kafka/Redpanda (streaming).
- DuckDB + Parquet (analytics/backtesting).
- PostgreSQL (metadatos, estado operacional).
- Redis (caché y estado de baja latencia).

### ML/MLOps
- PyTorch/LightGBM/XGBoost.
- MLflow (experimentos y model registry).
- Feast (feature store) opcional.
- Evidently/WhyLabs (drift/monitoring de modelos).

### Orquestación y servicios
- Airflow/Prefect (pipelines batch).
- FastAPI/gRPC (serving).
- Docker + Kubernetes (deploy y escalado).

### Observabilidad
- Prometheus + Grafana.
- OpenTelemetry + Loki/ELK.
- Alertmanager/PagerDuty.

---

## 8. Infraestructura y deployment
- **Ambientes**: dev, staging, prod con aislamiento estricto.
- **Topología**:
  - Cluster de cómputo para entrenamiento batch.
  - Servicios de inferencia autoscalables en K8s.
  - Nodos cercanos a brokers/exchanges para reducir latencia.
- **Estrategia de despliegue**: blue/green + canary.
- **Resiliencia**: multi-AZ, backup cifrado, DR tests periódicos.
- **Cost governance**: autoscaling, políticas de retención de datos.

---

## 9. Seguridad y auditoría
- Gestión de secretos (Vault/KMS), rotación automática y mínimo privilegio.
- Cifrado en tránsito (TLS 1.2+) y en reposo (AES-256).
- RBAC/ABAC por dominio (datos, modelos, ejecución).
- Registro inmutable de decisiones: input de modelo, score, razón, orden.
- Políticas de cumplimiento: segregación de funciones, aprobación dual en cambios críticos.
- Auditoría continua de accesos, cambios de configuración y operaciones de trading.

---

## 10. Testing y validación
- **Unit tests**: transformaciones, features, reglas de riesgo, enrutamiento.
- **Integration tests**: conectores, colas, inferencia y flujo de órdenes.
- **Backtesting robusto**: walk-forward, costos realistas, slippage dinámico.
- **Stress tests**: gaps, iliquidez, picos de volatilidad, fallos de proveedor.
- **Paper trading**: validación shadow antes de pasar a capital real.
- **Validación continua**: alertas automáticas por degradación de KPIs.

---

## 11. Entregables del proyecto
1. Documento de arquitectura maestra (este documento).
2. Diseño detallado por componente (API/data contracts).
3. Plan de implementación por fases y backlog priorizado.
4. Pipelines de ingesta + feature store operativos.
5. Modelos iniciales + benchmark y reportes de validación.
6. Motor de decisión/riesgo con reglas auditables.
7. Capa de ejecución con paper/live controlado.
8. Observabilidad integral y runbooks de incidentes.
9. Paquete de seguridad/compliance y evidencia de auditoría.

---

## 12. Roadmap de implementación (8 fases, 36 semanas)

| Fase | Semanas | Objetivo principal |
|---|---:|---|
| 1. Core Infrastructure | 1-4 | Fundaciones de plataforma, repos, CI/CD, observabilidad base |
| 2. Data Ingestion Layer | 5-9 | Conectores, calidad de datos, almacenamiento raw/curated |
| 3. Analysis Modules | 10-14 | Features técnicas, macro, NLP y on-chain |
| 4. Prediction Models | 15-19 | Modelos baseline + ensemble + serving inicial |
| 5. Decision Engine | 20-24 | Fusión de señales, reglas de riesgo, sizing y hedging |
| 6. Execution Layer | 25-29 | SOR, ejecución algorítmica, reconciliación y controles |
| 7. Monitoring & Testing | 30-33 | Pruebas integrales, observabilidad avanzada, hardening |
| 8. Deployment & Scale | 34-36 | Go-live gradual, optimización de costos y operación estable |

---

## 13. Referencias y librerías

### Datos y conectividad
- `ccxt` (exchanges crypto)
- `yfinance`, `pandas-datareader`, conectores FRED/ECB
- `websocket-client`, `aiohttp`

### Ingeniería de datos
- `pandas`, `polars`, `pyarrow`, `duckdb`
- `kafka-python` / `confluent-kafka`

### ML y cuantitativo
- `numpy`, `scipy`, `statsmodels`
- `scikit-learn`, `xgboost`, `lightgbm`, `pytorch`
- `optuna` (HPO), `mlflow` (tracking)

### Riesgo y backtesting
- `vectorbt`, `backtrader` (prototipado)
- librerías internas de slippage/costos/escenarios

### MLOps/Observabilidad
- `evidently`, `prometheus-client`, `opentelemetry`
- `fastapi`, `pydantic`, `uvicorn`

---

## 14. Criterios de éxito del Nivel 5
- Operación multimodal con trazabilidad completa por decisión.
- Pipeline reproducible de datos->modelo->ejecución.
- Control de riesgo activo en tiempo real y respuesta a eventos extremos.
- Capacidad de mejora continua por reentrenamiento gobernado.
