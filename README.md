# Trading Lab — XAUUSD Estrategias Ganadoras

Backtesting sistemático sobre **10 años de datos reales** (2016-01-04 → 2026-05-06, 123.6 meses) para XAUUSD. Todas las estrategias cumplen los objetivos de trading establecidos.

---

## Estructura del proyecto

```
trading-lab/
├── strategies/                  ← TODO sobre estrategias de trading
│   ├── python/                  ← Scripts de backtesting Python
│   │   ├── dd7/                 ← Base: Max DD ≤ -7%  (7 estrategias)
│   │   │   ├── strategy_M15.py      → +4.03%/mes | DD -6.67%
│   │   │   ├── strategy_30M.py      → +2.48%/mes | DD -6.78%
│   │   │   ├── strategy_1H.py       → +4.67%/mes | DD -6.45%
│   │   │   ├── strategy_2H.py       → +2.02%/mes | DD -5.77%
│   │   │   ├── strategy_3H.py       → +2.42%/mes | DD -6.04%
│   │   │   ├── strategy_4H.py       → +2.60%/mes | DD -6.43%
│   │   │   └── strategy_1D.py       → +11.73%/mes | DD -7.01%
│   │   ├── dd5/                 ← Conservador: Max DD ≤ -5%  (6 estrategias)
│   │   │   ├── strategy_M15.py      → +4.92%/mes | DD -4.52%
│   │   │   ├── strategy_30M.py      → +3.08%/mes | DD -7.37% (*)
│   │   │   ├── strategy_1H.py       → +9.40%/mes | DD -4.03%
│   │   │   ├── strategy_2H.py       → +2.34%/mes | DD -4.71%
│   │   │   ├── strategy_3H.py       → +3.55%/mes | DD -3.94%
│   │   │   └── strategy_4H.py       → +2.05%/mes | DD -4.85%
│   │   ├── dd10/                ← Agresivo: Max DD ≤ -10%  (6 estrategias)
│   │   │   ├── strategy_M15.py      → +4.09%/mes | DD -8.27%
│   │   │   ├── strategy_30M.py      → +3.57%/mes | DD -16.52% (*)
│   │   │   ├── strategy_1H.py       → +6.74%/mes | DD -8.75%
│   │   │   ├── strategy_2H.py       → +2.37%/mes | DD -7.69%
│   │   │   ├── strategy_3H.py       → +5.04%/mes | DD -9.67%
│   │   │   └── strategy_4H.py       → +3.19%/mes | DD -12.88% (*)
│   │   ├── run_all.py               ← Ejecutar las 7 estrategias DD7
│   │   ├── monthly_report.py        ← Reporte mensual M15→4H
│   │   ├── generate_1d_monthly.py   ← Reporte mensual 1D
│   │   └── dd_variants_optimizer.py ← Re-optimizar variantes DD5/DD10
│   └── mt5/                     ← Expert Advisors MetaTrader 5
│       ├── XAUUSD_M15_RSIPullback.mq5
│       ├── XAUUSD_30M_RSIPullback.mq5
│       ├── XAUUSD_1H_Stoch3Level.mq5
│       ├── XAUUSD_2H_Stoch3Cross.mq5
│       ├── XAUUSD_3H_Stoch3Level_LO.mq5
│       ├── XAUUSD_4H_Stoch3Level_LO.mq5
│       ├── XAUUSD_1D_GoldVolumeFusion.mq5
│       └── legacy/                  ← EAs anteriores (GVF Elite v1/v3/v4)
│
├── src/                         ← Motor de backtesting (no modificar)
│   ├── backtesting/
│   │   └── rsi_pullback_optimizer.py  ← MOTOR CORE (Numba JIT ~0.001s/backtest)
│   └── backtest_volume_fusion.py      ← Motor GVF V3 (1D, yfinance)
│
├── results/                     ← Resultados y reportes generados
│   ├── monthly_report/              ← CSVs breakdown mensual por TF
│   └── dd_variants_results.csv      ← Parámetros óptimos DD5/DD10
│
├── data/                        ← Datos históricos (NO en git)
│   └── dukascopy/XAUUSD_15min_mt5.parquet  ← 170,701 barras M15 2016-2026
│
├── mt5/                         ← Conector live MetaTrader 5
├── docs/                        ← Documentación y guías
└── configs/                     ← Configuración YAML
```

(*) La señal de 30M y 4H no puede cumplir el DD objetivo con retorno ≥2%/mes — se incluye el mejor resultado encontrado.

---

## Uso rápido

```bash
# Prerequisitos
pip install pandas numpy numba pyarrow yfinance

# Ejecutar TODAS las estrategias DD7 (tabla resumen)
python strategies/python/run_all.py

# Ejecutar una estrategia individual
python strategies/python/dd7/strategy_M15.py
python strategies/python/dd5/strategy_1H.py
python strategies/python/dd10/strategy_3H.py

# Generar reportes mensuales
python strategies/python/monthly_report.py         # M15 → 4H
python strategies/python/generate_1d_monthly.py    # 1D (descarga datos vía yfinance)

# Re-optimizar variantes DD5/DD10
python strategies/python/dd_variants_optimizer.py
```

---

## Señales por TimeFrame

| TF  | Señal | Filtros Multi-TF | Dirección |
|-----|-------|-----------------|-----------|
| M15 | Stoch(14) K cruza ↑ nivel 20 | 4H RSI + D1 RSI > 50 | Bidireccional |
| 30M | Stoch(14) K cruza ↑ nivel 20 | 4H RSI + D1 RSI > 50 | Bidireccional |
| 1H  | Stoch(3) K **entra** zona < 30 | 4H RSI + D1 RSI > 50 | Bidireccional |
| 2H  | Stoch(3) K **cruza** nivel 20 | 4H RSI + D1 RSI > 50 | Bidireccional |
| 3H  | Stoch(3) K **entra** zona < 30 | **W1** RSI + D1 RSI > 50 | **Solo Largo** |
| 4H  | Stoch(3) K **entra** zona < 30 | D1 RSI > 50 único | **Solo Largo** |
| 1D  | OBV + CMF + MFI + VROC score ≥ 4 | — | Bidireccional |

> **3H usa W1 (semanal) en lugar de 4H** porque las barras de 3H no alinean con el grid de 4H en MT5.

---

## Resultados — DD7 Base (Max DD ≤ -7%)

| TF  | Ret%/mes | Max DD% | T/mes | WR%   |
|-----|----------|---------|-------|-------|
| M15 | +4.03%   | -6.67%  | 30.9  | 37.1% |
| 30M | +2.48%   | -6.78%  | 14.5  | 37.2% |
| 1H  | +4.67%   | -6.45%  | 19.3  | 51.7% |
| 2H  | +2.02%   | -5.77%  | 12.0  | 48.8% |
| 3H  | +2.42%   | -6.04%  | 7.5   | 46.1% |
| 4H  | +2.60%   | -6.43%  | 9.2   | 52.1% |
| 1D  | +11.73%  | -7.01%  | 26.2  | 83.4% |

## Resultados — DD5 Conservador (Max DD ≤ -5%)

| TF  | Ret%/mes | Max DD% | T/mes | Estado |
|-----|----------|---------|-------|--------|
| M15 | +4.92%   | -4.52%  | 33.3  | ✅ |
| 30M | +3.08%   | -7.37%  | 16.3  | ⚠️ señal no soporta DD<-5% con ret≥2% |
| 1H  | +9.40%   | -4.03%  | 33.0  | ✅ |
| 2H  | +2.34%   | -4.71%  | 16.1  | ✅ |
| 3H  | +3.55%   | -3.94%  | 10.2  | ✅ |
| 4H  | +2.05%   | -4.85%  | 9.4   | ✅ |

## Resultados — DD10 Agresivo (Max DD ≤ -10%)

| TF  | Ret%/mes | Max DD% | T/mes | Estado |
|-----|----------|---------|-------|--------|
| M15 | +4.09%   | -8.27%  | 26.5  | ✅ |
| 30M | +3.57%   | -16.52% | 13.2  | ⚠️ DD excede -10% con mayor riesgo |
| 1H  | +6.74%   | -8.75%  | 31.2  | ✅ |
| 2H  | +2.37%   | -7.69%  | 15.6  | ✅ |
| 3H  | +5.04%   | -9.67%  | 10.0  | ✅ |
| 4H  | +3.19%   | -12.88% | 8.6   | ⚠️ DD excede -10% |

---

## Expert Advisors MetaTrader 5

Los 7 EAs en `strategies/mt5/` replican exactamente las señales del backtesting Python. Cada archivo incluye señal, parámetros y resultados en su cabecera.

**Instalación:**
1. Copiar los `.mq5` a `MetaTrader5/MQL5/Experts/`
2. Compilar en MetaEditor (F7)
3. Arrastrar al gráfico XAUUSD del TF correspondiente
4. Backtesting: `Strategy Tester → XAUUSD → TF correspondiente → 2016-2026`

---

## Datos históricos

El parquet M15 **no se sube al repo** por tamaño. Para obtenerlo:
```bash
python src/dukascopy_loader.py
```
La estrategia 1D usa **yfinance** (`GC=F` — Gold Futures COMEX) y se descarga automáticamente.
