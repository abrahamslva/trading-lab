# 🚀 DESCARGA RÁPIDA desde MT5 (Windows) — 15-30 minutos

## Instrucciones Paso a Paso

### PASO 1: Preparar tu PC Windows (2 min)

Abre **PowerShell o CMD** y navega a la carpeta del repo:

```powershell
cd C:\ruta\al\repo\trading-lab

# Verifica que estés en la carpeta correcta (debe ver un archivo README.md)
dir README.md
```

### PASO 2: Instalar dependencias Python (2 min)

Ejecuta en la misma terminal:

```powershell
pip install MetaTrader5 pandas pyarrow
```

**Nota**: Si ya los tienes instalados, es instantáneo.

### PASO 3: Preparar MT5 para descarga (5 min)

Antes de ejecutar el script, **abre MT5 en tu PC**:

1. **Abre MetaTrader 5**
2. **Asegúrate de estar logueado** (ves tu número de cuenta)
3. **Haz que MT5 descargue más historia** (opcional pero importante):
   - Abre el gráfico **XAUUSD M15**
   - Usa las flechas para ir lo más atrás posible en tiempo
   - MT5 descargará automáticamente historia del servidor conforme vayas hacia atrás
   - Espera 2-3 minutos a que MT5 descargue toda la historia disponible
   - **NO cierres MT5** (lo necesitamos abierto para el script)

**⚠️ Importante**: El script accede a MT5 mientras esté abierto. Mantén MT5 abierto durante todo el proceso.

### PASO 4: Ejecutar el script (10-20 min)

En la misma PowerShell/CMD donde estás en `trading-lab/`:

```powershell
python mt5/export_history.py
```

**Qué verás**:
```
============================================================
  MT5 → Parquet Exporter | XAUUSD M15
============================================================
✓ MT5 conectado | Cuenta: 123456 | Broker: ICMarkets-MT5
  Balance: 10000.00 USD
✓ Símbolo: XAUUSD | Dígitos: 2 | Spread: 15 puntos

  Descargando 20 chunks × 6 meses (2016 → 2026)...
  Chunks pendientes: 20/20

  [1/20] 5% | 2016-01-01→2016-07-01 | 12,456 barras | total 12,456 | 0.6 MB
  [2/20] 10% | 2016-07-01→2017-01-01 | 12,200 barras | total 24,656 | 1.2 MB
  [3/20] 15% | 2017-01-01→2017-07-01 | 13,100 barras | total 37,756 | 1.8 MB
  ...
  [20/20] 100% | 2025-07-01→2026-05-06 | 14,800 barras | total 259,000 | 12.5 MB

============================================================
✓ EXPORTACIÓN COMPLETA
  259,000 barras M15
  2016-01-04 00:00:00+00:00 → 2026-05-06 21:00:00+00:00
  12.5 MB  →  data/dukascopy/XAUUSD_15min_mt5.parquet
============================================================

Próximo paso: subir el parquet al Codespace.
  Opción A — GitHub CLI:
    gh codespace cp data/dukascopy/XAUUSD_15min_mt5.parquet \
      remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
```

**Eso es todo** — el archivo `XAUUSD_15min_mt5.parquet` está listo en tu PC.

---

## PASO 5: Subir el archivo a Codespace (5 min)

Tienes **3 opciones**. Elige una:

### ✅ OPCIÓN A: GitHub CLI (Más fácil)

Sigue en la misma terminal PowerShell/CMD:

```powershell
gh codespace cp data/dukascopy/XAUUSD_15min_mt5.parquet `
  remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
```

**Verás**:
```
Copying 'data/dukascopy/XAUUSD_15min_mt5.parquet' to remote codespace...
✓ Copying file succeeded
```

**Listo** — El archivo está en Codespace. Ve al PASO 6.

---

### ✅ OPCIÓN B: VS Code Drag & Drop (Visual)

1. En VS Code, abre el Codespace (**Remote Explorer** → tu codespace)
2. En el panel izquierdo, navega a: `data/dukascopy/`
3. En Windows Explorer, ve a: `C:\ruta\al\repo\trading-lab\data\dukascopy\`
4. **Arrastra** `XAUUSD_15min_mt5.parquet` desde Windows Explorer al panel izquierdo de VS Code
5. Espera a que suba (barra de progreso)

**Listo** — El archivo está en Codespace. Ve al PASO 6.

---

### ✅ OPCIÓN C: scp (Si tienes SSH configurado)

```powershell
# (Requiere GitHub CLI + SSH configurado)
scp data/dukascopy/XAUUSD_15min_mt5.parquet `
  <tu-codespace-ssh>:/workspaces/trading-lab/data/dukascopy/
```

**Listo** — El archivo está en Codespace. Ve al PASO 6.

---

## PASO 6: Verificar en Codespace

En Codespace (terminal Linux), verifica:

```bash
ls -lh /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet

# Deberías ver algo como:
# -rw-r--r-- 1 codespace codespace 12.5M May  6 21:00 XAUUSD_15min_mt5.parquet
```

Si el archivo aparece, **¡ÉXITO!** 🎉

---

## PASO 7: Activar el Backtest Automático

El watcher está esperando 150 MB. Como probablemente tengas ~10-20 MB:

En Codespace, actualiza el umbral temporalmente:

```bash
cd /workspaces/trading-lab

# Cambia el umbral a lo que tengas (ejemplo: 12 MB si descargaste 12.5 MB)
sed -i 's/MIN_SIZE_MB = 150/MIN_SIZE_MB = 12/g' src/run_when_ready.py

# Reinicia el watcher
pkill -f run_when_ready.py
nohup python3 src/run_when_ready.py > data/watcher.log 2>&1 &

# Verifica que se lance automáticamente
tail -f data/watcher.log
# Deberías ver: "✓✓✓ DATOS COMPLETOS: 12.5 MB (100%) — lanzando backtest..."
```

**Automáticamente se lanzará** `src/backtest_full.py` que ejecutará 63 backtests en ~45-60 minutos.

---

## 🎯 Resumen del Tiempo Total

| Paso | Duración | Acción |
|------|----------|--------|
| 1. PowerShell + carpeta | 2 min | Navegar a repo |
| 2. Instalar pip packages | 2 min | `pip install` |
| 3. Preparar MT5 + historia | 5 min | Abrir MT5, descargar historia |
| 4. Ejecutar script MT5 | **10-20 min** | `python mt5/export_history.py` |
| 5. Subir a Codespace | 5 min | `gh codespace cp` o drag-drop |
| **TOTAL DESCARGA** | **~30 min** | ✅ |
| | |  |
| 6. Backtest ejecución | 45-60 min | Automático |
| **TOTAL TODO** | **~90 min** | Desde ahora |

**VS la espera original de 7-10 horas = ¡Ahorras 6-9 horas!**

---

## 🆘 Troubleshooting

### "ERROR: mt5.initialize() falló"
**Problema**: MT5 no está abierto o no está logueado  
**Solución**: 
1. Abre MetaTrader 5
2. Asegúrate de estar logueado (ves tu balance)
3. Ejecuta el script nuevamente

### "ERROR: símbolo XAUUSD no encontrado"
**Problema**: Tu broker llama GOLD en lugar de XAUUSD  
**Solución**:
1. Abre `mt5/export_history.py` en editor
2. Cambia línea: `SYMBOL = "XAUUSD"` → `SYMBOL = "GOLD"`
3. Ejecuta nuevamente

### "ERROR: gh command not found"
**Problema**: GitHub CLI no instalado  
**Solución**: Usa **OPCIÓN B (Drag & Drop)** o instala GitHub CLI:
```powershell
choco install gh  # Si tienes Chocolatey
# O ve a: https://github.com/cli/cli/releases
```

### "ConnectionError al conectar Codespace"
**Problema**: Problema de red  
**Solución**: Usa **OPCIÓN B (VS Code Drag & Drop)** directamente

---

## ✅ Checklist Final

- [ ] PowerShell abierto en `C:\ruta\al\repo\trading-lab\`
- [ ] `pip install MetaTrader5 pandas pyarrow` ✓
- [ ] MT5 abierto y logueado
- [ ] MT5 con historia de XAUUSD M15 descargada (gráfico expandido)
- [ ] Ejecuté `python mt5/export_history.py` ✓
- [ ] Archivo `data/dukascopy/XAUUSD_15min_mt5.parquet` creado (~10-20 MB)
- [ ] Subí el archivo a Codespace (gh/drag-drop/scp) ✓
- [ ] Verifiqué en Codespace con `ls -lh` ✓
- [ ] Actualicé MIN_SIZE_MB en src/run_when_ready.py ✓
- [ ] Reinicié watcher con `nohup python3 src/run_when_ready.py...` ✓
- [ ] Backtest comenzó automáticamente (ver watcher.log) ✓

---

## 🎬 Ahora Qué

Una vez que **el backtest complete** (45-60 min), verás en Codespace:

```
✓ BACKTEST COMPLETED
Results: 63 scenarios tested (9 strategies × 7 timeframes)
Passing: X/63 strategies met all objectives
Best Strategy: [version] [timeframe] Sharpe=[score]
```

Luego puedes:
1. **Analizar resultados** en `results/backtest_full_results.csv`
2. **Compilar EA v4** en MT5 con los mejores parámetros
3. **Implementar JANUS** (blending dinámico via Atlas GIC)

---

**¿Questions?** Pregunta línea por línea cuando llegues.  
**¡Vamos! Debería tomar ~30 minutos.** 🚀
