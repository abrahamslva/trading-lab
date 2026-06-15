# IMPLEMENTATION_PROMPT

## Objetivo
Implementar el Trading Bot Nivel 5 (multimodal institucional) en 8 fases y 35 tareas, priorizando robustez operativa, control de riesgo y trazabilidad completa.

---

## Fase 1: Core Infrastructure (Tareas 1-3)
1. Inicializar estructura de servicios (ingesta, features, modelos, ejecución, monitoreo).
2. Configurar CI/CD base (tests, lint, build, quality gates).
3. Definir contratos de datos/eventos y versionado de esquemas.

## Fase 2: Data Ingestion Layer (Tareas 4-7)
4. Implementar conectores de market data (BTC/XAU, OHLCV, order book).
5. Implementar conectores macroeconómicos (FRED, calendario económico, yields).
6. Implementar conectores on-chain y normalización de métricas clave.
7. Implementar pipeline NLP/news/sentimiento con almacenamiento raw y curated.

## Fase 3: Analysis Modules (Tareas 8-13)
8. Construir módulo de calidad de datos (completitud, latencia, consistencia).
9. Construir módulo de features técnicas (momentum, volatilidad, microestructura).
10. Construir módulo de features macro (inflación, tasas, riesgo sistémico).
11. Construir módulo de features on-chain (flujos, whales, actividad de red).
12. Construir módulo NLP (sentimiento, relevancia de eventos, topic tagging).
13. Integrar Feature Store versionado con parity offline-online.

## Fase 4: Prediction Models (Tareas 14-18)
14. Entrenar modelos baseline por horizonte (clasificación/regresión).
15. Entrenar modelo de volatilidad y régimen de mercado.
16. Construir ensemble multimodal con calibración probabilística.
17. Implementar serving online con fallback y control de latencia.
18. Integrar monitoreo de drift (datos, features y performance de modelo).

## Fase 5: Decision Engine (Tareas 19-22)
19. Diseñar agregador de señales con score de convicción.
20. Implementar motor de riesgo (VaR/CVaR, límites de exposición, drawdown guard).
21. Implementar position sizing dinámico y reglas de hedging BTC/XAU.
22. Implementar kill-switch y políticas de bloqueo por baja calidad/eventos extremos.

## Fase 6: Execution Layer (Tareas 23-27)
23. Implementar Smart Order Router multi-venue.
24. Implementar ejecución algorítmica (TWAP/VWAP/POV).
25. Implementar validaciones pre-trade (límites, compliance, liquidez).
26. Implementar reconciliación post-trade y manejo de rechazos/reintentos.
27. Implementar capa de paper trading y shadow mode contra ejecución real.

## Fase 7: Monitoring & Testing (Tareas 28-32)
28. Crear suite de unit tests para features, riesgo y reglas de decisión.
29. Crear pruebas de integración para ingestión->modelo->orden.
30. Ejecutar backtesting walk-forward con costos/slippage realistas.
31. Ejecutar stress tests (gaps, latencia, caídas de proveedores, eventos macro).
32. Implementar dashboards y alertas operativas (SLA/SLO + KPIs de trading).

## Fase 8: Deployment (Tareas 33-35)
33. Desplegar en staging con canary + validación funcional completa.
34. Ejecutar go-live progresivo con límites de capital y revisión diaria.
35. Formalizar runbooks, handover operativo y ciclo de mejora continua.

---

## Instrucciones de trabajo
- Ejecutar cada fase con criterio de “Definition of Done” y evidencias trazables.
- No promover artefactos sin validación automática mínima.
- Mantener versionado de datasets, features, modelos y decisiones.
- Priorizar seguridad (secret management, RBAC, cifrado, auditoría).
- Diseñar para resiliencia: reintentos, degradación elegante y rollback.
- Documentar decisiones de arquitectura y trade-offs por fase.

---

## Validación del proyecto completo
El proyecto se considera validado si cumple simultáneamente:
- **Calidad técnica**: pipelines estables, tests críticos en verde, observabilidad completa.
- **Calidad cuantitativa**: métricas de riesgo/retorno dentro de umbrales definidos.
- **Calidad operativa**: operación continua con incidentes controlados y MTTR aceptable.
- **Calidad de gobierno**: auditoría reproducible de extremo a extremo.
- **Calidad de despliegue**: transición staging->producción sin degradaciones críticas.

---

## Siguiente paso
Iniciar **Fase 1 / Tarea 1** creando el esqueleto de servicios y contratos base, seguido de la configuración de CI/CD y controles de calidad para habilitar el resto del roadmap sin deuda estructural.
