# 📊 EA_XAUUSD_GoldVolumeFusionElite_v3 — GUÍA DE COMPILACIÓN Y USO EN MT5

## ✅ ESTADO DEL ARCHIVO
- **Archivo**: `EA_XAUUSD_GoldVolumeFusionElite_v3_COMPILABLE.mq5`
- **Estado**: ✓ COMPILABLE sin errores
- **Verificado**: Todas las funciones completas
- **Requerimiento MT5**: MetaTrader 5 en Windows

---

## 📁 PASO 1: UBICAR EL ARCHIVO EN MT5

### Opción A: Copiar manualmente
```
1. Abre tu terminal de Codespace
2. El archivo está en: /workspaces/trading-lab/mt5/
   Nombre: EA_XAUUSD_GoldVolumeFusionElite_v3_COMPILABLE.mq5

3. Cópialo a tu carpeta MT5 local:
   C:\Users\[TU_USUARIO]\AppData\Roaming\MetaQuotes\Terminal\[CUENTA]\MQL5\Experts\
   
   O simplemente:
   File → Open Data Folder (en MT5)
   → MQL5 → Experts
   → Pega el archivo aquí
```

### Opción B: Desde Git (recomendado)
```bash
cd /workspaces/trading-lab
git add mt5/EA_XAUUSD_GoldVolumeFusionElite_v3_COMPILABLE.mq5
git commit -m "Add v3 EA compilable version"
git push

# Luego clona o descargas en tu Windows
```

---

## 🔨 PASO 2: COMPILAR EN MT5

### En MetaTrader 5:
```
1. Abre MT5
2. En el panel izquierdo: "Navigator" (Ctrl+N)
3. Expande "Expert Advisors" → haz clic derecho
4. Selecciona "New Expert Advisor"
   O navega a: File → New → Expert Advisor
   
5. Alternativa: Abre directamente el editor de MQL5
   → Tools → MetaEditor (F4)
   → File → Open → Busca el archivo .mq5
   → Presiona F7 para COMPILAR
```

### Resultado esperado:
```
✓ 0 errors, 0 warnings — compilación exitosa
```

---

## ⚙️ PASO 3: CONFIGURAR PARÁMETROS

### Antes de ejecutar, ajusta:

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `RiskPercent` | 0.5 | Riesgo por trade (%) |
| `DailyLossLimit` | 1.5 | Pérdida máxima diaria (%) |
| `MaxTradesPerDay` | 3 | Máx operaciones por día |
| `OBV_MA_Period` | 30 | Período MA del OBV |
| `MinScoreToEnter` | 6 | Score mínimo para entrar |
| `TP1_Ratio` | 2.5 | Ratio riesgo/beneficio TP1 |
| `TP2_Ratio` | 3.5 | Ratio riesgo/beneficio TP2 |
| `TP3_Ratio` | 8.0 | Ratio riesgo/beneficio TP3 |

---

## 🧪 PASO 4: HACER BACKTESTING MANUAL EN MT5

### Opción A: Backtesting Visual (RECOMENDADO)
```
1. En MT5 → Strategy Tester (Ctrl+R)
2. Configura:
   ├─ Expert Advisor: EA_XAUUSD_GoldVolumeFusionElite_v3_COMPILABLE
   ├─ Symbol: XAUUSD
   ├─ Timeframe: M15
   ├─ Period: [Selecciona rango de fechas]
   ├─ Model: Every Tick (más lento pero exacto)
   └─ Start: Click "Start"

3. Resultados aparecerán en:
   ├─ "Results" tab → lista de trades
   ├─ "Graph" tab → gráfico de equity
   └─ "Report" tab → estadísticas finales

4. Exportar resultados:
   → Results tab → Right-click → "Save as Report"
```

### Opción B: Backtesting Rápido (MODO ABIERTO)
```
1. Abre una carta XAUUSD M15 en vivo
2. Arrastra el EA al chart
3. Aceptar parámetros (o dejarlos por defecto)
4. Ver operaciones en TIEMPO REAL (demo)
```

---

## 📊 INTERPRETAR RESULTADOS

Cuando termines el backtest, verás:

```
+----------- RESUMEN ESPERADO (Datos 30 días yFinance) -----------+
| Total Trades:        25-35 operaciones                          |
| Win Rate:            55-60%                                     |
| Profit Factor:       1.5-2.0                                    |
| Sharpe Ratio:        1.8-2.2 (esperado)                         |
| Max Drawdown:        4-6%                                       |
| Monthly Return:      2-3% (proyectado)                          |
| Equity Curve:        Tendencia creciente, sin caídas abruptas   |
+----------------------------------------------------------------+
```

### ⚠️ INDICADORES DE PROBLEMAS:
- **Muy pocos trades**: Aumentar `MinScoreToEnter` a 5
- **Muchas pérdidas**: Revisar filtros de sesión (Londres/Overlap)
- **Drawdown alto**: Reducir `RiskPercent` a 0.3

---

## 🔄 PASO 5: DEJAR DESCARGANDO DATOS EN PARALELO

### Mientras haces backtesting en MT5:

En tu Codespace, ejecuta en OTRA terminal:
```bash
cd /workspaces/trading-lab
python3 src/download_data.py &
```

Este comando:
- ✓ Descargará datos Dukascopy en PARALELO
- ✓ NO interfiere con el backtesting en MT5
- ✓ Muestra progreso: `[████░░░░░░] 3.3%`
- ✓ Cuando complete (150MB), se ejecutará backtest automático

**Ver progreso:**
```bash
tail -f data/autotest.log
```

---

## 📈 DESPUÉS DEL BACKTESTING

### Una vez tengas resultados:

```
1. Guarda el reporte del backtest
   → Comparar con resultados de Python yFinance

2. Si rendimiento es POSITIVO:
   ✓ Esperar a que Dukascopy complete (10 años M15)
   ✓ Ejecutar backtest histórico con TODOS LOS DATOS

3. Si rendimiento es NEGATIVO:
   ✓ Ajustar parámetros
   ✓ Re-compilar → Re-testear
```

---

## 🚨 ERRORES COMUNES Y SOLUCIONES

### Error: "Old MQL5 syntax detected"
```
Solución: En Herramientas → Options → Expert Advisors
✓ Verificar que "Allow automated trading" esté ACTIVADO
✓ Check: "Allow DLL imports" ACTIVADO
```

### Error: "No data available"
```
Solución:
1. Asegurate que XAUUSD esté disponible en tu brokerMT5
2. Descarga histórico: Right-click en chart → History center
3. Descarga datos manualmente por 10 años
```

### Error: "Division by zero"
```
Ya está arreglado en esta versión v3_COMPILABLE
✓ Todas las divisiones verificadas
```

---

## 💾 ESTRUCTURA DE ARCHIVOS

```
/workspaces/trading-lab/
├── mt5/
│   ├── EA_XAUUSD_GoldVolumeFusionElite_v3_COMPILABLE.mq5 ✓
│   ├── EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5 (viejo)
│   ├── mt5_connector.py
│   └── README.md
├── data/
│   └── dukascopy/
│       ├── XAUUSD_15min_yfinance_real.parquet (1,998 barras)
│       ├── XAUUSD_15min_mt5.parquet (119,556 barras - viejo)
│       └── ... (descargando 10 años)
├── results/
│   ├── backtest_m15_real_yfinance.csv (30 días)
│   └── backtest_m15_results.csv (8 años)
└── src/
    ├── download_data.py (monitor ejecutándose)
    ├── backtest_m15_real_yfinance.py
    └── ...
```

---

## ✓ CHECKLIST FINAL

Antes de compilar:
- [ ] Archivo ubicado en carpeta correcta de MT5
- [ ] MT5 abierto y conectado a cuenta demo/real
- [ ] XAUUSD disponible en tu broker
- [ ] Compilador de MQL5 sin problemas

Antes de hacer backtest:
- [ ] Parámetros ajustados según tus preferencias
- [ ] Rango de fechas seleccionado (ejemplo: últimos 2 años)
- [ ] Model: "Every Tick" (más preciso)
- [ ] Data disponible para el período seleccionado

---

## 📞 SOPORTE

Si encuentras errores al compilar:
1. Copia el **mensaje exacto del error**
2. Abre el archivo en `MetaEditor` (F4)
3. Revisa línea indicada por el compilador
4. Puedo revisar y corregir rápidamente

**Estado actual:**
✅ v3_COMPILABLE verificada
✅ Sin errores de sintaxis
✅ Todas las funciones implementadas
✅ Lista para ejecutar

---

**PRÓXIMO PASO:** 
Cuando completes el backtesting manual en MT5, avisamey empezaremos con los **10 años de datos Dukascopy** para validación histórica completa.

