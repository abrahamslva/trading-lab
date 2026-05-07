## 🚀 COMANDO POR COMANDO — COPIA Y PEGA

### EN WINDOWS POWERSHELL/CMD (Tu PC):

```powershell
# 1. Navega a la carpeta
cd C:\ruta\al\repo\trading-lab

# 2. Instala dependencias
pip install MetaTrader5 pandas pyarrow

# 3. Abre MetaTrader5 AHORA y mantenlo abierto
# (No ejecutes nada en terminal hasta que MT5 esté abierto)

# 4. Descarga los datos (AQUÍ ESPERAS 10-20 MIN)
python mt5/export_history.py
```

**Verás algo como**:
```
============================================================
  MT5 → Parquet Exporter | XAUUSD M15
============================================================
✓ MT5 conectado...
✓ Símbolo: XAUUSD...

  Descargando 20 chunks × 6 meses (2016 → 2026)...
  
  [1/20] 5%...
  [2/20] 10%...
  ...
  [20/20] 100% | COMPLETO | 259,000 barras | 12.5 MB
```

### Cuando termine (4 opciones para subir):

#### OPCIÓN 1: GitHub CLI (Más fácil)
```powershell
gh codespace cp data/dukascopy/XAUUSD_15min_mt5.parquet `
  remote:/workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet
```

#### OPCIÓN 2: VS Code Drag-Drop
1. Abre Codespace en VS Code
2. En Explorer lateral: `data/dukascopy/`
3. En Windows: `C:\ruta\al\repo\trading-lab\data\dukascopy\XAUUSD_15min_mt5.parquet`
4. Arrastra el archivo

#### OPCIÓN 3: scp
```powershell
scp data/dukascopy/XAUUSD_15min_mt5.parquet `
  <codespace-ssh>:/workspaces/trading-lab/data/dukascopy/
```

---

### EN CODESPACE (Linux Terminal):

```bash
# 1. Verifica que el archivo está
ls -lh /workspaces/trading-lab/data/dukascopy/XAUUSD_15min_mt5.parquet

# 2. Navega al repo
cd /workspaces/trading-lab

# 3. Actualiza el umbral del watcher (cambia 12 por el tamaño real en MB)
sed -i 's/MIN_SIZE_MB = 150/MIN_SIZE_MB = 12/g' src/run_when_ready.py

# 4. Mata el watcher anterior
pkill -f run_when_ready.py

# 5. Lanza el watcher nuevamente
nohup python3 src/run_when_ready.py > data/watcher.log 2>&1 &

# 6. Mira el log para ver cómo se dispara el backtest
tail -f data/watcher.log

# Deberías ver:
# ✓✓✓ DATOS COMPLETOS: 12.5 MB (100%) — lanzando backtest completo...
# ▶ src/backtest_full.py  (9 iteraciones × 7 TFs = 63 combinaciones)
```

---

## ⏱️ TIEMPO TOTAL

| Fase | Duración |
|------|----------|
| Setup (pip) | 2 min |
| Descarga MT5 | 10-20 min |
| Subir a Codespace | 5 min |
| **Total Descarga** | **~30 min** |
| Backtest ejecución | 45-60 min |
| **TODO JUNTO** | **~90 min** |

---

## 🎯 QUÉ PASA DESPUÉS

Una vez que el backtest complete (verás en terminal):
```
⚗️  BACKTEST EXECUTION PIPELINE
  Status: ✓ COMPLETED
  Results: 63/63 scenarios tested
  Passing: X/63 strategies met all objectives
```

Luego:
1. Revisa `results/backtest_full_results.csv`
2. Identifica mejores estrategias
3. Configura JANUS (blending)
4. Compila EA v4 en MT5
5. Deploy en vivo

---

**¡Adelante! Esto debería tomar máximo 30 minutos.** 🚀
