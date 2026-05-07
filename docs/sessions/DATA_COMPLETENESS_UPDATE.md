# ✅ CONFIGURACIÓN ACTUALIZADA: ESPERAR 100% DE DATOS

## Cambio Realizado

**Ahora el sistema esperará TODOS los datos de 10 años en M15 (150 MB) antes de ejecutar backtesting**

### Antes vs Ahora

| Criterio | Antes | Ahora |
|----------|-------|-------|
| **Umbral Auto-Trigger** | 10 MB (datos parciales) | **150 MB (100% completo)** |
| **Cobertura de Datos** | ~2 años | **10 años completos** |
| **Confiabilidad Backtest** | Media (datos sesgados) | **Alta (todo el rango)** |
| **Backtest Wait Time** | ~1 hora | **~7-10 horas (descarga completa)** |

---

## Timeline Actualizado

```
AHORA:           2.4 MB / 150 MB (1.6%)
                 ✓ Download: RUNNING
                 ✓ Watcher: RUNNING (esperando 150 MB)

PROGRESO:        Chunk 9/21 en descarga
                 Velocidad: ~0.5-1.0 MB cada 10 segundos

⏳ ESPERA:        ~6-8 horas más (descargar 147.6 MB restantes)

CUANDO 150 MB:   ✓ AUTO-TRIGGER: Watcher lanza backtest_full.py
                 ⚗️  Ejecución: 9 estrategias × 7 timeframes = 63 tests
                 ⏱️  Duración: ~45-60 minutos

RESULTADOS:      📊 backtest_full_results.csv
                 🎯 63 combinaciones con 25 métricas cada una
                 ✅ Identificación de mejores estrategias
```

---

## Archivos Modificados

### 1. **src/run_when_ready.py**
```python
# ANTES:
MIN_SIZE_MB = 10  # trigger con datos parciales

# AHORA:
MIN_SIZE_MB = 150  # espera 10 años completos
print("Waiting for COMPLETE dataset (150 MB = 10 years M15)")
```

### 2. **monitor_v2.py**
```python
# Actualizado para mostrar:
- "Waiting for COMPLETE dataset (150 MB = 10 years M15)"
- Porcentaje de completitud dinámico
- MB faltantes vs MB actuales
```

---

## Procesos Activos

### ✓ Download (PID 19106)
- **Status**: RUNNING
- **Chunk**: 9/21
- **Tamaño actual**: 2.4 MB
- **Target**: 150 MB
- **Velocidad**: ~0.5 MB/10 segundos
- **ETA**: ~6-8 horas

### ✓ Watcher (PID 23219) — ACTUALIZADO
- **Status**: RUNNING
- **Watch**: Parquet file reaching 150 MB
- **Action**: Auto-launch `src/backtest_full.py`
- **Log**: `/workspaces/trading-lab/data/watcher.log`

### ✓ Monitor (Live Terminal)
- **Updates**: Every 10 seconds
- **Status**: Shows "INCOMPLETE (147.6 MB remaining, 98.4%)"
- **Control**: Press Ctrl+C to stop

---

## Monitoreo en Tiempo Real

El monitor está corriendo en terminal separada mostrando:

```
📊 DATA DOWNLOAD PIPELINE
   Status: ✓ RUNNING
   File Size: 2.4 MB / 150.0 MB (1.6%)
   Progress: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

🔔 AUTO-TRIGGER WATCHER
   Status: ✓ RUNNING
   Monitor: Waiting for COMPLETE dataset (150 MB = 10 years M15)
   Auto-Trigger: ⏳ INCOMPLETE (147.6 MB remaining, 98.4% more data needed)

⚗️  BACKTEST EXECUTION PIPELINE
   Status: ⏳ PENDING (waiting for complete M15 dataset)
   When: After download reaches 150 MB (147.6 MB remaining)
   Expected Time: ~45-60 minutes to complete after all data is ready
   Output File: results/backtest_full_results.csv
```

---

## Próximos Pasos

1. **Esperar descarga completa** (~6-8 horas desde ahora)
   - Monitor mostrará progreso en tiempo real
   - Download retomará automáticamente si hay interrupciones (checkpoint recovery)

2. **Cuando alcance 150 MB**
   - Watcher detecta automáticamente
   - Auto-lanza: `python src/backtest_full.py`
   - Ejecuta: 63 combinaciones (9 estrategias × 7 timeframes)

3. **Backtest en ejecución** (~45-60 minutos)
   - Monitor mostrará: "Status: 🔄 RUNNING"
   - Log actualizado en tiempo real

4. **Resultados listos**
   - Monitor mostrará: "Status: ✓ COMPLETED"
   - Estrategias passing: X/63
   - Best Strategy: [version] [timeframe] Sharpe=[score]

---

## Ventajas de Esperar 150 MB

✅ **Datos Completos**: 10 años (2016-2026) sin sesgos  
✅ **Estadísticas Confiables**: Suficientes ciclos de mercado  
✅ **Mejor DD Analysis**: Drawdowns máximos históricos reales  
✅ **Win Rate Realista**: Test con múltiples tendencias  
✅ **Sharpe Ratio Preciso**: 10 años de performance real  
✅ **Menos Overfitting**: No optimizado a datos parciales  

---

## Monitoreo Manual

Si no tienes el monitor abierto, puedes verificar estado en cualquier momento:

```bash
# Ver progreso de download
tail -f /workspaces/trading-lab/data/download.log

# Verificar procesos
ps aux | grep -E "download_data|run_when_ready|backtest_full"

# Ver tamaño actual
ls -lh /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet

# Ver estado del watcher
tail -f /workspaces/trading-lab/data/watcher.log
```

---

## Rollback (Si necesitas revertir)

Si necesitas cambiar el umbral nuevamente:

```bash
# Edit src/run_when_ready.py
# Change MIN_SIZE_MB to desired value
# Restart watcher:
pkill -f run_when_ready.py
nohup python3 src/run_when_ready.py > data/watcher.log 2>&1 &
```

---

**Configuración Actualizada**: 2026-05-06 20:24 UTC  
**Estado**: ✅ Watcher esperando 150 MB de datos completos  
**Monitor**: ✅ Corriendo en terminal (actualización cada 10 segundos)
