# Estrategias de Trading — XAUUSD

Directorio de estrategias desarrolladas y documentadas para el trading de oro.

---

## Estrategias en este Proyecto

### 1. MA Cross (Cruce de Medias Móviles)
- **Archivo:** `src/strategies/ma_cross.py`
- **Tipo:** Tendencia — seguimiento
- **Descripción:** Estrategia clásica de cruce de dos medias móviles (rápida y lenta)
- **Parámetros:** Configurables en `configs/backtest.yaml`

---

## Plantilla para Documentar Estrategias

Cuando cargues las estrategias del ZIP, documenta cada una con esta estructura:

```markdown
## Nombre de la Estrategia

- **Tipo:** Tendencia / Reversión a la media / Breakout / Scalping / Swing
- **Timeframe:** M5 / M15 / H1 / H4 / D1
- **Indicadores:** Lista de indicadores usados
- **Señal de entrada:** Descripción de la condición de entrada
- **Señal de salida:** Stop loss, take profit, trailing stop
- **Gestión de riesgo:** % de capital por operación
- **Resultados backtest:** Winrate, RR, drawdown máximo
- **Periodo de prueba:** Rango de fechas testeado
- **Notas:** Observaciones adicionales
```

---

## Estrategias a Cargar (desde el ZIP)

Una vez que se cargue el archivo `Base de datos XAUUSD.zip`, agregar aquí el índice de estrategias encontradas.

---

*Última actualización: 2026-05-05*
