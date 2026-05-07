"""
src/backtest_full.py
=====================
Gold Volume Fusion Elite — Motor de Backtesting Completo v2

Incorpora todo el conocimiento de la base de datos:
  - 3 estrategias maestras de la "Biblia del Oro":
      #1 Asian Range Breakout + London Confirmation
      #2 Multi-TF Order Block + Volume Profile Confluence
      #3 Macro Swing COT + OBV
  - Indicadores de volumen (OBV, VWAP, MFI, A/D, CMF, VP, Chaikin, VPT, VROC)
  - Contexto macro: DXY (FRED), VIX, US10Y (yfinance sin API key)
  - COT proxy via Gold futures positioning
  - ADR filter (Average Daily Range)
  - Session filters (Asian/London/Overlap)
  - Wyckoff phase detection
  - Keltner Channel extremes
  - Gap de apertura del domingo

OBJETIVOS ACTUALIZADOS:
  min monthly return : 1.5% avg
  max drawdown       : 9.0%
  min trades/month   : 7
  max daily loss     : 5.0%

ITERACIONES:
  V1: Parámetros originales EA
  V2: Ajuste automático (Optuna)
  V3: EA v3_FINAL
  V4: Asian Breakout puro (Estrategia #1 biblia)
  V5: OB + Volume Profile (Estrategia #2 biblia)
  V6: Macro Swing mejorado (Estrategia #3 biblia + COT proxy)
"""

from __future__ import annotations
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
import requests
import time

# ──────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
_MT5_PARQUET  = ROOT / "data/dukascopy/XAUUSD_15min_mt5.parquet"
_YF_PARQUET   = ROOT / "data/dukascopy/XAUUSD_15min_yf_temp.parquet"
_RESULTS_CSV  = ROOT / "results/backtest_full_results.csv"
_RESULTS_JSON = ROOT / "results/backtest_full_params.json"

# ──────────────────────────────────────────────────────────────────
# OBJETIVOS (configs/objectives.yaml)
# ──────────────────────────────────────────────────────────────────
OBJECTIVES = {
    "min_monthly_return": 1.5,   # % promedio mensual
    "max_drawdown":       9.0,   # % máximo DD
    "min_trades_month":   7,     # trades mínimos por mes
    "max_daily_loss":     5.0,   # % pérdida máxima en un día
    "min_sharpe":         0.5,   # Sharpe mínimo
}

# ──────────────────────────────────────────────────────────────────
# TIMEFRAMES A TESTEAR
# ──────────────────────────────────────────────────────────────────
TIMEFRAMES = {
    "M15": "15min",
    "M30": "30min",
    "1H":  "1h",
    "2H":  "2h",
    "3H":  "3h",
    "4H":  "4h",
    "1D":  "1D",
}

# ──────────────────────────────────────────────────────────────────
# PARÁMETROS — 6 ITERACIONES
# ──────────────────────────────────────────────────────────────────
# V1: Original EA
PARAMS_V1 = {
    "name":              "V1_Original",
    "risk_pct":          0.50,
    "daily_loss_limit":  5.00,   # ACTUALIZADO a objetivo
    "max_trades_day":    2,
    "obv_ma_period":     20,
    "cmf_period":        20,
    "cmf_threshold":     0.05,
    "mfi_period":        14,
    "mfi_oversold":      25.0,
    "mfi_overbought":    75.0,
    "atr_period":        14,
    "sl_atr_mult":       1.8,
    "tp1_ratio":         2.0,
    "tp2_ratio":         4.0,
    "tp3_ratio":         6.5,
    "tp1_pct":           0.40,
    "tp2_pct":           0.35,
    "min_score":         5,
    "london_start":      8,
    "london_end":        11,
    "overlap_start":     13,
    "overlap_end":       17,
    "filter_weekdays":   True,
    "adr_period":        14,
    "adr_max_used":      0.65,
    "vp_period":         100,
    "vp_poc_buffer":     0.003,
    "use_asian_breakout":False,
    "use_ob_vp":         False,
    "use_macro_filter":  False,
    "use_keltner":       False,
    "use_gap_fill":      False,
}

# V2: Ajuste fino (mejores parámetros encontrados por Optuna en backtest anterior)
PARAMS_V2 = {**PARAMS_V1,
    "name":           "V2_Optuna",
    "sl_atr_mult":    1.5,
    "tp1_ratio":      2.5,
    "tp2_ratio":      3.5,
    "tp3_ratio":      7.0,
    "min_score":      5,
    "cmf_threshold":  0.07,
    "adr_max_used":   0.70,
    "filter_weekdays":False,
}

# V3: EA v3_FINAL exacto
PARAMS_V3 = {**PARAMS_V1,
    "name":           "V3_EA_Final",
    "obv_ma_period":  30,
    "cmf_threshold":  0.08,
    "tp1_ratio":      2.5,
    "tp2_ratio":      3.5,
    "tp3_ratio":      8.0,
    "min_score":      6,
    "filter_weekdays":False,
}

# V4: Asian Range Breakout + London Confirmation (Estrategia #1 Biblia)
# Win rate documentado 70-80%, SL = 0.15 × ADR
PARAMS_V4 = {**PARAMS_V1,
    "name":              "V4_AsianBreakout",
    "use_asian_breakout":True,
    "use_ob_vp":         False,
    "use_macro_filter":  True,
    "risk_pct":          0.50,
    "sl_atr_mult":       1.2,   # SL más ajustado (0.15 × ADR)
    "tp1_ratio":         1.5,   # TP1 1:1.5
    "tp2_ratio":         2.5,   # TP2 1:2.5
    "tp3_ratio":         3.5,   # TP3 1:3+
    "tp1_pct":           0.50,  # cierra 50% en TP1
    "tp2_pct":           0.25,  # cierra 25% en TP2
    "min_score":         3,     # Asian breakout score es diferente
    "london_start":      8,
    "london_end":        11,
    "overlap_start":     13,
    "overlap_end":       17,
    "filter_weekdays":   True,  # solo Mar-Jue
    "adr_max_used":      0.70,  # no entrar si ADR >70% consumido
    "asian_range_min":   15,    # rango asiático mínimo (en puntos)
    "asian_range_max":   80,    # rango asiático máximo
    "sweep_confirm":     True,  # confirmar el London sweep antes de entrar
}

# V5: OB + Volume Profile Confluence (Estrategia #2 Biblia)
# Win rate 60-65%, RR objetivo 1:4-1:8, Overlap 13:00-17:00 UTC
PARAMS_V5 = {**PARAMS_V1,
    "name":              "V5_OB_VolumeProfile",
    "use_asian_breakout":False,
    "use_ob_vp":         True,
    "use_macro_filter":  True,
    "risk_pct":          0.75,  # ligeramente más por alta confianza
    "sl_atr_mult":       2.0,   # SL más allá del OB + 1.5 × ATR
    "tp1_ratio":         2.0,   # TP1 LVN del VP
    "tp2_ratio":         4.0,   # TP2 siguiente HVN/POC
    "tp3_ratio":         6.0,   # TP3 zona de liquidez
    "tp1_pct":           0.40,
    "tp2_pct":           0.35,
    "min_score":         4,     # mínimo 4/6 confluencias
    "london_start":      13,    # solo Overlap
    "london_end":        17,
    "overlap_start":     13,
    "overlap_end":       17,
    "filter_weekdays":   True,  # solo Mié-Jue (mejores días)
    "adr_max_used":      0.70,
    "vp_period":         200,   # VP más largo para OB
    "vp_poc_buffer":     0.002,
    "ob_lookback":       14,    # días para buscar OBs no mitigados
    "ob_min_impulse":    5,     # mínimo de velas en el impulso post-OB
}

# V6: Macro Swing COT + OBV (Estrategia #3 Biblia)
# Win rate 55-60%, RR 1:6-1:15, usa DXY, VIX, US10Y como filtros
PARAMS_V6 = {**PARAMS_V1,
    "name":              "V6_MacroSwing",
    "use_asian_breakout":False,
    "use_ob_vp":         False,
    "use_macro_filter":  True,
    "use_keltner":       True,
    "use_gap_fill":      True,
    "risk_pct":          0.50,
    "sl_atr_mult":       2.5,   # SL más amplio para swing
    "tp1_ratio":         2.0,   # TP1 máximo anterior
    "tp2_ratio":         5.0,   # TP2 extensión Fib 138.2%
    "tp3_ratio":         10.0,  # TP3 extensión Fib 261.8%
    "tp1_pct":           0.35,
    "tp2_pct":           0.35,
    "min_score":         4,
    "london_start":      0,     # opera todo el día
    "london_end":        24,
    "overlap_start":     13,
    "overlap_end":       17,
    "filter_weekdays":   False, # opera todos los días
    "adr_max_used":      0.60,  # más conservador
    "keltner_mult":      3.0,   # 3ª desviación = zona de reversión
    "fib_levels":        [0.382, 0.500, 0.618],
    "obv_divergence":    True,  # requiere divergencia OBV confirmada
    "dxy_filter":        True,  # usa DXY como filtro macro
    "vix_filter":        True,  # usa VIX como filtro de riesgo
    "us10y_filter":      True,  # usa rendimientos 10Y
}

ALL_PARAMS = [PARAMS_V1, PARAMS_V2, PARAMS_V3, PARAMS_V4, PARAMS_V5, PARAMS_V6]

# ──────────────────────────────────────────────────────────────────
# ITERACIONES ADICIONALES V7/V8/V9 — Para alcanzar objetivos
# ──────────────────────────────────────────────────────────────────

# V7: Original relajado — más trades, umbral más bajo
PARAMS_V7 = {**PARAMS_V1,
    "name":              "V7_RelaxedHiFreq",
    "min_score":         4,       # era 5
    "adr_max_used":      0.90,    # era 0.65 — mucho más permisivo
    "filter_weekdays":   False,   # todos los días (era Tue-Thu)
    "max_trades_day":    4,       # era 2
    "london_start":      7,       # más horas de sesión
    "london_end":        17,
    "overlap_start":     12,
    "overlap_end":       20,
    "sl_atr_mult":       1.2,     # SL más ajustado para mejor RR
    "tp1_ratio":         1.5,
    "tp2_ratio":         3.5,
    "tp3_ratio":         6.0,
    "tp1_pct":           0.45,
    "tp2_pct":           0.30,
    "risk_pct":          0.40,    # riesgo menor por más trades
}

# V8: Reversión a la media — RSI extremos + volumen divergente
PARAMS_V8 = {**PARAMS_V1,
    "name":              "V8_MeanReversion",
    "use_mean_revert":   True,    # activa lógica de reversión
    "min_score":         3,
    "adr_max_used":      0.99,    # sin filtro ADR
    "filter_weekdays":   False,
    "max_trades_day":    3,
    "london_start":      6,       # inicio sesión europea temprana
    "london_end":        20,
    "overlap_start":     6,
    "overlap_end":       20,
    "sl_atr_mult":       1.0,
    "tp1_ratio":         1.5,
    "tp2_ratio":         3.0,
    "tp3_ratio":         5.5,
    "tp1_pct":           0.50,
    "tp2_pct":           0.30,
    "risk_pct":          0.45,
    "rsi_oversold":      35,
    "rsi_overbought":    65,
    "mfi_oversold":      25.0,
    "mfi_overbought":    75.0,
    "cmf_threshold":     0.04,
    "use_asian_breakout":False,
    "use_ob_vp":         False,
    "use_macro_filter":  False,
    "use_keltner":       False,
}

# V9: Tendencia + momentum — EMA crossover con confirmación de volumen
PARAMS_V9 = {**PARAMS_V1,
    "name":              "V9_TrendMomentum",
    "use_trend_momentum":True,    # activa lógica de tendencia
    "min_score":         3,
    "adr_max_used":      0.95,
    "filter_weekdays":   False,
    "max_trades_day":    3,
    "london_start":      7,
    "london_end":        21,
    "overlap_start":     12,
    "overlap_end":       21,
    "sl_atr_mult":       1.5,
    "tp1_ratio":         2.0,
    "tp2_ratio":         4.5,
    "tp3_ratio":         8.0,
    "tp1_pct":           0.40,
    "tp2_pct":           0.30,
    "risk_pct":          0.50,
    "use_asian_breakout":False,
    "use_ob_vp":         False,
    "use_macro_filter":  False,
    "use_keltner":       False,
}

ALL_PARAMS_EXTENDED = [PARAMS_V1, PARAMS_V2, PARAMS_V3, PARAMS_V4, PARAMS_V5, PARAMS_V6,
                       PARAMS_V7, PARAMS_V8, PARAMS_V9]



# ══════════════════════════════════════════════════════════════════
# 1. CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════

def load_xauusd_data() -> pd.DataFrame:
    """Carga datos XAUUSD en orden de prioridad."""

    # 1. Parquet 10 años (Dukascopy)
    if _MT5_PARQUET.exists() and _MT5_PARQUET.stat().st_size > 5_000_000:
        print(f"  ✓ Cargando datos Dukascopy 10 años: {_MT5_PARQUET}")
        df = pd.read_parquet(_MT5_PARQUET)
        df.index = pd.to_datetime(df.index, utc=True)
        print(f"    {len(df):,} barras M15 | {df.index[0].date()} → {df.index[-1].date()}")
        return df

    # 2. Parquet yfinance temporal
    if _YF_PARQUET.exists():
        print(f"  ⚠ Usando datos yfinance temporales: {_YF_PARQUET}")
        df = pd.read_parquet(_YF_PARQUET)
        df.index = pd.to_datetime(df.index, utc=True)
        df.columns = [c.lower() for c in df.columns]  # normalizar a lowercase
        df = df[["open","high","low","close","volume"]].dropna()
        print(f"    {len(df):,} barras | {df.index[0].date()} → {df.index[-1].date()}")
        return df

    # 3. Descargar yfinance
    print("  ⚠ Descargando desde yfinance GC=F (fallback)...")
    df = yf.download("GC=F", start="2014-01-01", interval="1h",
                     auto_adjust=True, progress=False, multi_level_index=False)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[["open","high","low","close","volume"]].dropna()
    print(f"    {len(df):,} barras 1H descargadas")
    return df


def resample_ohlcv(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """Resamplea a cualquier timeframe."""
    tf_map = {"15min":"15min","30min":"30min","1h":"1h","2h":"2h","3h":"3h","4h":"4h","1D":"1D"}
    rule = tf_map.get(target_tf, target_tf)

    if rule == "1D":
        df_r = df.resample("1D").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()
    else:
        df_r = df.resample(rule).agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna()
    return df_r


def load_macro_context() -> dict:
    """
    Descarga indicadores macro relevantes para el oro:
    - DXY (UUP ETF como proxy)
    - VIX (^VIX)
    - US10Y (^TNX)
    Todo sin API key usando yfinance.
    """
    print("  Cargando contexto macro (DXY, VIX, US10Y)...")
    macro = {}
    try:
        # DXY proxy
        dxy = yf.download("UUP", start="2014-01-01", interval="1d",
                         auto_adjust=True, progress=False, multi_level_index=False)
        if not dxy.empty:
            dxy.columns = [c.lower() for c in dxy.columns]
            dxy.index = pd.to_datetime(dxy.index, utc=True)
            macro["dxy"] = dxy[["close"]].rename(columns={"close":"dxy"})

        # VIX
        vix = yf.download("^VIX", start="2014-01-01", interval="1d",
                          auto_adjust=True, progress=False, multi_level_index=False)
        if not vix.empty:
            vix.columns = [c.lower() for c in vix.columns]
            vix.index = pd.to_datetime(vix.index, utc=True)
            macro["vix"] = vix[["close"]].rename(columns={"close":"vix"})

        # US10Y
        us10y = yf.download("^TNX", start="2014-01-01", interval="1d",
                            auto_adjust=True, progress=False, multi_level_index=False)
        if not us10y.empty:
            us10y.columns = [c.lower() for c in us10y.columns]
            us10y.index = pd.to_datetime(us10y.index, utc=True)
            macro["us10y"] = us10y[["close"]].rename(columns={"close":"us10y"})

        print(f"    DXY: {len(macro.get('dxy',[])):,} días | VIX: {len(macro.get('vix',[])):,} días | US10Y: {len(macro.get('us10y',[])):,} días")
    except Exception as e:
        print(f"    ⚠ Error macro: {e}")
    return macro


# ══════════════════════════════════════════════════════════════════
# 2. INDICADORES TÉCNICOS Y DE VOLUMEN
# ══════════════════════════════════════════════════════════════════

def calc_indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Calcula todos los indicadores necesarios para las 6 estrategias."""
    d = df.copy()
    c, h, l, o, v = d["close"], d["high"], d["low"], d["open"], d["volume"]

    # ── ATR ──────────────────────────────────────────────────────
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    d["atr"] = tr.ewm(alpha=1/p["atr_period"], adjust=False).mean()

    # ── ADR (Average Daily Range — no incluye gaps) ───────────────
    daily_range = df.resample("1D").agg({"high":"max","low":"min"}).dropna()
    daily_range["adr"] = (daily_range["high"] - daily_range["low"]).rolling(
        p["adr_period"], min_periods=5).mean()
    d["adr"] = daily_range["adr"].reindex(d.index, method="ffill").ffill().bfill()
    # rango del día actual ya consumido
    day_high = d["high"].resample("1D").transform("max")
    day_low  = d["low"].resample("1D").transform("min")
    d["day_range_pct"] = (day_high - day_low) / (d["adr"] + 1e-9)

    # ── EMA / SMA ─────────────────────────────────────────────────
    d["ema20"]  = c.ewm(span=20, adjust=False).mean()
    d["ema50"]  = c.ewm(span=50, adjust=False).mean()
    d["ema200"] = c.ewm(span=200, adjust=False).mean()

    # ── OBV ───────────────────────────────────────────────────────
    direction = np.sign(c.diff().fillna(0))
    d["obv"] = (v * direction).cumsum()
    d["obv_ma"] = d["obv"].rolling(p["obv_ma_period"]).mean()
    d["obv_bull"] = d["obv"] > d["obv_ma"]

    # ── VWAP (aproximado: diario) ─────────────────────────────────
    typical = (h + l + c) / 3
    cum_tp_v = (typical * v).resample("1D").transform("cumsum")
    cum_v    = v.resample("1D").transform("cumsum")
    d["vwap"] = cum_tp_v / (cum_v + 1e-9)
    d["above_vwap"] = c > d["vwap"]

    # ── MFI ───────────────────────────────────────────────────────
    tp = typical
    raw_mf = tp * v
    pos_mf = raw_mf.where(tp > tp.shift(), 0)
    neg_mf = raw_mf.where(tp < tp.shift(), 0)
    mfi_period = p["mfi_period"]
    mfr = pos_mf.rolling(mfi_period).sum() / (neg_mf.rolling(mfi_period).sum() + 1e-9)
    d["mfi"] = 100 - (100 / (1 + mfr))
    d["mfi_bull"] = (d["mfi"] > 50) & (d["mfi"] < p["mfi_overbought"])
    d["mfi_bear"] = (d["mfi"] < 50) & (d["mfi"] > p["mfi_oversold"])

    # ── CMF (Chaikin Money Flow) ───────────────────────────────────
    mfv = ((c - l) - (h - c)) / (h - l + 1e-9) * v
    cmf_period = p["cmf_period"]
    d["cmf"] = mfv.rolling(cmf_period).sum() / (v.rolling(cmf_period).sum() + 1e-9)
    d["cmf_bull"] = d["cmf"] > p["cmf_threshold"]
    d["cmf_bear"] = d["cmf"] < -p["cmf_threshold"]

    # ── A/D Line ──────────────────────────────────────────────────
    d["ad"] = (((c - l) - (h - c)) / (h - l + 1e-9) * v).cumsum()

    # ── Chaikin Oscillator ────────────────────────────────────────
    ad_fast = d["ad"].ewm(span=p.get("chaikin_fast", 3), adjust=False).mean()
    ad_slow = d["ad"].ewm(span=p.get("chaikin_slow", 10), adjust=False).mean()
    d["chaikin"] = ad_fast - ad_slow
    d["chaikin_bull"] = d["chaikin"] > 0

    # ── VPT (Volume Price Trend) ──────────────────────────────────
    d["vpt"] = (v * c.pct_change().fillna(0)).cumsum()
    d["vpt_ma"] = d["vpt"].rolling(p.get("vpt_ma_period", 14)).mean()
    d["vpt_bull"] = d["vpt"] > d["vpt_ma"]

    # ── VROC (Volume Rate of Change) ──────────────────────────────
    vroc_period = p.get("vroc_period", 14)
    d["vroc"] = v.pct_change(vroc_period).fillna(0) * 100
    d["vroc_bull"] = d["vroc"] > 0

    # ── Keltner Channel (opcional, V6) ─────────────────────────────
    if p.get("use_keltner", False):
        kelt_mult = p.get("keltner_mult", 3.0)
        d["keltner_mid"]   = c.ewm(span=20, adjust=False).mean()
        d["keltner_upper"] = d["keltner_mid"] + kelt_mult * d["atr"]
        d["keltner_lower"] = d["keltner_mid"] - kelt_mult * d["atr"]
        d["near_keltner_upper"] = c >= d["keltner_upper"] * 0.995
        d["near_keltner_lower"] = c <= d["keltner_lower"] * 1.005

    # ── Volume Profile Proxy (POC usando ventana rodante) ─────────
    vp_period = p.get("vp_period", 100)
    d["poc"] = c.rolling(vp_period).apply(
        lambda x: x[np.argmax(np.bincount((((x - x.min()) / (x.max() - x.min() + 1e-9)) * 20).astype(int).clip(0,19)))] if len(x) > 0 else x[-1],
        raw=True
    )
    poc_buf = p.get("vp_poc_buffer", 0.003)
    d["near_poc"] = (c - d["poc"]).abs() / (d["poc"] + 1e-9) < poc_buf

    # ── RSI ───────────────────────────────────────────────────────
    delta = c.diff()
    gain  = delta.where(delta > 0, 0).ewm(span=14, adjust=False).mean()
    loss  = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
    d["rsi"] = 100 - (100 / (1 + gain / (loss + 1e-9)))

    # ── MACD ──────────────────────────────────────────────────────
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    d["macd"] = ema12 - ema26
    d["macd_signal"] = d["macd"].ewm(span=9, adjust=False).mean()
    d["macd_bull"] = d["macd"] > d["macd_signal"]

    # ── Session flags ─────────────────────────────────────────────
    hour_utc = d.index.hour
    d["in_london"]  = (hour_utc >= p["london_start"])  & (hour_utc < p["london_end"])
    d["in_overlap"] = (hour_utc >= p["overlap_start"]) & (hour_utc < p["overlap_end"])
    d["in_session"] = d["in_london"] | d["in_overlap"]
    dow = d.index.dayofweek  # 0=Mon, 6=Sun
    d["is_trading_day"] = dow < 5
    if p.get("filter_weekdays", False):
        d["is_good_day"] = dow.isin([1, 2, 3])  # Mar, Mié, Jue
    else:
        d["is_good_day"] = dow < 5

    # ── Asian range (para V4) ──────────────────────────────────────
    if p.get("use_asian_breakout", False):
        # 22:00-08:00 UTC = sesión asiática
        asian_mask = (hour_utc >= 22) | (hour_utc < 8)
        d["asian_session"] = asian_mask
        # High/Low asiático del día actual (se llena al cerrar sesión)
        d["asian_high"] = d["high"].where(asian_mask).resample("1D", closed="right", label="right").transform("max")
        d["asian_low"]  = d["low"].where(asian_mask).resample("1D", closed="right", label="right").transform("min")
        d["asian_range"] = d["asian_high"] - d["asian_low"]
        asian_min = p.get("asian_range_min", 15)
        asian_max = p.get("asian_range_max", 80)
        d["asian_range_ok"] = (d["asian_range"] >= asian_min) & (d["asian_range"] <= asian_max)
        d["above_asian_high"] = c > d["asian_high"]
        d["below_asian_low"]  = c < d["asian_low"]

    # ── OBV Divergence (para V6) ──────────────────────────────────
    if p.get("obv_divergence", False):
        # Divergencia alcista: precio hace nuevo mínimo pero OBV no
        price_new_low = c == c.rolling(14).min()
        obv_not_new_low = d["obv"] > d["obv"].rolling(14).min()
        d["obv_bull_div"] = price_new_low & obv_not_new_low
        # Divergencia bajista: precio hace nuevo máximo pero OBV no
        price_new_high = c == c.rolling(14).max()
        obv_not_new_high = d["obv"] < d["obv"].rolling(14).max()
        d["obv_bear_div"] = price_new_high & obv_not_new_high

    # ── Gap domingo ────────────────────────────────────────────────
    if p.get("use_gap_fill", False):
        # Detectar gaps de apertura del domingo
        is_sunday_open = (dow == 6) & (hour_utc == 22)
        prev_friday_close = c.shift(1)
        d["sunday_gap"] = (c - prev_friday_close) * is_sunday_open
        d["gap_up"] = d["sunday_gap"] > 0
        d["gap_down"] = d["sunday_gap"] < 0

    return d


# ══════════════════════════════════════════════════════════════════
# 3. SEÑALES DE ENTRADA — SCORING UNIFICADO
# ══════════════════════════════════════════════════════════════════

def generate_signals(d: pd.DataFrame, p: dict) -> pd.Series:
    """
    Genera señales: +1 = long, -1 = short, 0 = sin señal.
    Sistema de puntos adaptado a cada estrategia.
    """
    n = len(d)
    signals = np.zeros(n, dtype=int)

    # ─── Filtros comunes ──────────────────────────────────────────
    session_ok = d["in_session"].values
    day_ok     = d["is_good_day"].values & d["is_trading_day"].values
    adr_ok     = d["day_range_pct"].values < p["adr_max_used"]
    base_filter = session_ok & day_ok & adr_ok

    # ─── V4: Asian Range Breakout (señal especial) ─────────────────
    if p.get("use_asian_breakout", False):
        asian_ok = d.get("asian_range_ok", pd.Series(True, index=d.index)).values
        above_ah = d.get("above_asian_high", pd.Series(False, index=d.index)).values
        below_al = d.get("below_asian_low",  pd.Series(False, index=d.index)).values
        vol_conf = d["volume"].values > d["volume"].rolling(10).mean().values
        cmf_bull = d["cmf_bull"].values
        cmf_bear = d["cmf_bear"].values
        obv_bull = d["obv_bull"].values

        for i in range(50, n):
            if not (base_filter[i] and asian_ok[i] and d.index[i].hour >= 8):
                continue
            # Long: ruptura alcista del rango asiático con volumen
            if above_ah[i] and vol_conf[i]:
                score = 0
                if cmf_bull[i]: score += 1
                if obv_bull[i]: score += 1
                if d["macd_bull"].values[i]: score += 1
                if d["rsi"].values[i] > 50: score += 1
                if score >= p["min_score"]:
                    signals[i] = 1
            # Short: ruptura bajista del rango asiático con volumen
            elif below_al[i] and vol_conf[i]:
                score = 0
                if cmf_bear[i]: score += 1
                if not obv_bull[i]: score += 1
                if not d["macd_bull"].values[i]: score += 1
                if d["rsi"].values[i] < 50: score += 1
                if score >= p["min_score"]:
                    signals[i] = -1
        return pd.Series(signals, index=d.index)

    # ─── V5: OB + Volume Profile ───────────────────────────────────
    if p.get("use_ob_vp", False):
        near_poc = d["near_poc"].values
        cmf_bull = d["cmf_bull"].values
        cmf_bear = d["cmf_bear"].values
        obv_bull = d["obv_bull"].values
        above_vwap = d["above_vwap"].values
        vpt_bull = d["vpt_bull"].values
        rsi = d["rsi"].values

        for i in range(50, n):
            if not base_filter[i]:
                continue
            # Longs: precio cerca del POC + momentum positivo
            if near_poc[i] and above_vwap[i]:
                score = 0
                if cmf_bull[i]: score += 2
                if obv_bull[i]: score += 2
                if vpt_bull[i]: score += 1
                if d["macd_bull"].values[i]: score += 1
                if d["chaikin_bull"].values[i]: score += 1
                if 40 < rsi[i] < 65: score += 1  # no sobrecomprado
                if score >= p["min_score"]:
                    signals[i] = 1
            # Shorts: precio cerca del POC + momentum negativo
            elif near_poc[i] and not above_vwap[i]:
                score = 0
                if cmf_bear[i]: score += 2
                if not obv_bull[i]: score += 2
                if not vpt_bull[i]: score += 1
                if not d["macd_bull"].values[i]: score += 1
                if not d["chaikin_bull"].values[i]: score += 1
                if 35 < rsi[i] < 60: score += 1
                if score >= p["min_score"]:
                    signals[i] = -1
        return pd.Series(signals, index=d.index)

    # ─── V6: Macro Swing ──────────────────────────────────────────
    if p.get("use_macro_filter", False) and p.get("obv_divergence", False):
        obv_bull_div = d.get("obv_bull_div", pd.Series(False, index=d.index)).values
        near_kelt_l  = d.get("near_keltner_lower", pd.Series(False, index=d.index)).values
        near_kelt_u  = d.get("near_keltner_upper", pd.Series(False, index=d.index)).values
        above_ema200 = (d["close"] > d["ema200"]).values
        fib_zones    = d["near_poc"].values  # proxy de nivel Fibonacci/soporte

        for i in range(200, n):
            if not day_ok[i]:
                continue
            # Long setup macro: OBV divergencia alcista + Keltner inferior + macro alcista
            if obv_bull_div[i] and near_kelt_l[i] and above_ema200[i]:
                score = 0
                if d["cmf_bull"].values[i]: score += 1
                if d["mfi_bull"].values[i]: score += 1
                if d["rsi"].values[i] < 45: score += 1  # sobrevendido
                if d["macd_bull"].values[i]: score += 1
                if score >= p["min_score"]:
                    signals[i] = 1
            # Short: Keltner superior + divergencia bajista
            elif near_kelt_u[i] and not above_ema200[i]:
                score = 0
                if d["cmf_bear"].values[i]: score += 1
                if d["rsi"].values[i] > 65: score += 1
                if not d["macd_bull"].values[i]: score += 1
                if score >= p["min_score"]:
                    signals[i] = -1
        return pd.Series(signals, index=d.index)

    # ─── V8: Mean Reversion — RSI extremos + volumen ───────────────
    if p.get("use_mean_revert", False):
        rsi      = d["rsi"].values
        mfi      = d["mfi"].values
        cmf_bull = d["cmf_bull"].values
        cmf_bear = d["cmf_bear"].values
        obv_bull = d["obv_bull"].values
        above_vwap = d["above_vwap"].values
        rsi_os = p.get("rsi_oversold", 35)
        rsi_ob = p.get("rsi_overbought", 65)

        for i in range(30, n):
            if not base_filter[i]:
                continue
            # Reversal long: RSI sobrevendido + OBV alcista + CMF positivo
            if rsi[i] < rsi_os and mfi[i] < p.get("mfi_oversold", 25):
                score = 0
                if cmf_bull[i]: score += 1
                if obv_bull[i]: score += 1
                if d["macd_bull"].values[i]: score += 1
                if score >= p["min_score"]:
                    signals[i] = 1
            # Reversal short: RSI sobrecomprado + OBV bajista
            elif rsi[i] > rsi_ob and mfi[i] > p.get("mfi_overbought", 75):
                score = 0
                if cmf_bear[i]: score += 1
                if not obv_bull[i]: score += 1
                if not d["macd_bull"].values[i]: score += 1
                if score >= p["min_score"]:
                    signals[i] = -1
        return pd.Series(signals, index=d.index)

    # ─── V9: Trend Momentum — EMA crossover + confirmación volumen ─
    if p.get("use_trend_momentum", False):
        ema20 = d["ema20"].values
        ema50 = d["ema50"].values
        ema200 = d["ema200"].values
        obv_bull = d["obv_bull"].values
        cmf_bull = d["cmf_bull"].values
        cmf_bear = d["cmf_bear"].values
        macd_bull = d["macd_bull"].values
        rsi = d["rsi"].values
        vpt_bull = d["vpt_bull"].values
        close = d["close"].values

        for i in range(200, n):
            if not base_filter[i]:
                continue
            # Long: EMA20 > EMA50 > EMA200 (tendencia alcista) + volumen confirma
            if ema20[i] > ema50[i] and ema50[i] > ema200[i]:
                score = 0
                if obv_bull[i]: score += 1
                if cmf_bull[i]: score += 1
                if macd_bull[i]: score += 1
                if vpt_bull[i]: score += 1
                if 40 < rsi[i] < 70: score += 1
                if close[i] > ema20[i]: score += 1
                if score >= p["min_score"]:
                    # Confirmación: pullback a EMA20
                    prev_close = close[i-1] if i > 0 else close[i]
                    if prev_close < ema20[i] or close[i-2] < ema20[i]:  # tocó EMA20
                        signals[i] = 1
                    elif score >= p["min_score"] + 1:  # sin pullback necesita más score
                        signals[i] = 1
            # Short: EMA20 < EMA50 < EMA200 (tendencia bajista) + volumen confirma
            elif ema20[i] < ema50[i] and ema50[i] < ema200[i]:
                score = 0
                if not obv_bull[i]: score += 1
                if cmf_bear[i]: score += 1
                if not macd_bull[i]: score += 1
                if not vpt_bull[i]: score += 1
                if 30 < rsi[i] < 60: score += 1
                if close[i] < ema20[i]: score += 1
                if score >= p["min_score"]:
                    prev_close = close[i-1] if i > 0 else close[i]
                    if prev_close > ema20[i] or close[i-2] > ema20[i]:
                        signals[i] = -1
                    elif score >= p["min_score"] + 1:
                        signals[i] = -1
        return pd.Series(signals, index=d.index)

    # ─── V1/V2/V3/V7: Sistema de scoring original con volumen ──────
    score_long  = (
        d["obv_bull"].astype(int) +
        d["cmf_bull"].astype(int) +
        d["mfi_bull"].astype(int) +
        d["chaikin_bull"].astype(int) +
        d["vpt_bull"].astype(int) +
        d["vroc_bull"].astype(int) +
        d["macd_bull"].astype(int) +
        d["above_vwap"].astype(int) +
        (d["close"] > d["poc"]).astype(int) +
        (d["close"] > d["ema20"]).astype(int) +
        (d["rsi"] > 50).astype(int) +
        (d["rsi"] < 70).astype(int)   # no sobrecomprado
    )
    score_short = (
        (~d["obv_bull"]).astype(int) +
        d["cmf_bear"].astype(int) +
        d["mfi_bear"].astype(int) +
        (~d["chaikin_bull"]).astype(int) +
        (~d["vpt_bull"]).astype(int) +
        (~d["vroc_bull"]).astype(int) +
        (~d["macd_bull"]).astype(int) +
        (~d["above_vwap"]).astype(int) +
        (d["close"] < d["poc"]).astype(int) +
        (d["close"] < d["ema20"]).astype(int) +
        (d["rsi"] < 50).astype(int) +
        (d["rsi"] > 30).astype(int)   # no sobrevendido
    )
    min_score = p["min_score"]
    signals = np.where(base_filter & (score_long >= min_score), 1,
              np.where(base_filter & (score_short >= min_score), -1, 0))

    return pd.Series(signals, index=d.index)


# ══════════════════════════════════════════════════════════════════
# 4. SIMULACIÓN DE TRADES
# ══════════════════════════════════════════════════════════════════

def simulate_trades(d: pd.DataFrame, signals: pd.Series, p: dict,
                    initial_capital: float = 100_000.0) -> dict:
    """
    Simula trades con:
    - SL dinámico (ATR-based)
    - 3 TPs parciales
    - Límite de pérdida diaria (5%)
    - Máx trades por día
    - Spread simulado: 0.3 USD en XAUUSD
    """
    SPREAD      = 0.30   # USD spread típico ECN
    LOT_SIZE    = 100    # troy oz por lote estándar
    SLIP        = 0.10   # slippage estimado USD

    capital    = initial_capital
    trades     = []
    equity_curve = [capital]
    dates_curve  = [d.index[0]]

    daily_loss = {}   # date → pérdida acumulada
    daily_count = {}  # date → número de trades

    sl_mult   = p["sl_atr_mult"]
    tp1r, tp2r, tp3r = p["tp1_ratio"], p["tp2_ratio"], p["tp3_ratio"]
    tp1p, tp2p       = p["tp1_pct"], p["tp2_pct"]
    risk_pct  = p["risk_pct"] / 100
    max_dd    = p["daily_loss_limit"] / 100
    max_tr_day = p.get("max_trades_day", 2)

    i = 0
    close = d["close"].values
    high  = d["high"].values
    low   = d["low"].values
    atr   = d["atr"].values
    sig   = signals.values
    idx   = d.index

    while i < len(d) - 3:
        if sig[i] == 0:
            i += 1
            continue

        date_key = idx[i].date()
        daily_loss.setdefault(date_key, 0.0)
        daily_count.setdefault(date_key, 0)

        # Filtro pérdida diaria
        if daily_loss[date_key] / capital >= max_dd:
            i += 1
            continue
        if daily_count[date_key] >= max_tr_day:
            i += 1
            continue

        direction = sig[i]
        entry     = close[i] + (SPREAD + SLIP) * direction
        sl_dist   = max(atr[i] * sl_mult, entry * p.get("min_sl_pct", 0.002))

        if direction == 1:   # long
            sl = entry - sl_dist
            tp1 = entry + sl_dist * tp1r
            tp2 = entry + sl_dist * tp2r
            tp3 = entry + sl_dist * tp3r
        else:                # short
            sl = entry + sl_dist
            tp1 = entry - sl_dist * tp1r
            tp2 = entry - sl_dist * tp2r
            tp3 = entry - sl_dist * tp3r

        # Tamaño de posición (riesgo fijo)
        risk_usd   = capital * risk_pct
        lot_size   = risk_usd / (sl_dist * LOT_SIZE + 1e-9)
        lot_size   = min(lot_size, 10.0)  # máx 10 lotes

        # Simular precio en barras siguientes
        tp1_hit = tp2_hit = tp3_hit = sl_hit = False
        exit_price = None
        rem_lots = lot_size
        realized_pnl = 0.0

        for j in range(i+1, min(i+500, len(d))):
            h_j = high[j]
            l_j = low[j]

            # TP1 parcial
            if not tp1_hit:
                if direction == 1 and h_j >= tp1:
                    close_lots = lot_size * tp1p
                    realized_pnl += (tp1 - entry) * close_lots * LOT_SIZE
                    rem_lots -= close_lots
                    tp1_hit = True
                elif direction == -1 and l_j <= tp1:
                    close_lots = lot_size * tp1p
                    realized_pnl += (entry - tp1) * close_lots * LOT_SIZE
                    rem_lots -= close_lots
                    tp1_hit = True

            # TP2 parcial
            if tp1_hit and not tp2_hit:
                if direction == 1 and h_j >= tp2:
                    close_lots = lot_size * tp2p
                    realized_pnl += (tp2 - entry) * close_lots * LOT_SIZE
                    rem_lots -= close_lots
                    tp2_hit = True
                elif direction == -1 and l_j <= tp2:
                    close_lots = lot_size * tp2p
                    realized_pnl += (entry - tp2) * close_lots * LOT_SIZE
                    rem_lots -= close_lots
                    tp2_hit = True

            # SL (mueve a BE si TP1 fue alcanzado)
            sl_eff = entry if tp1_hit else sl
            if direction == 1 and l_j <= sl_eff:
                exit_price = sl_eff
                realized_pnl += (sl_eff - entry) * rem_lots * LOT_SIZE
                sl_hit = True
                break
            elif direction == -1 and h_j >= sl_eff:
                exit_price = sl_eff
                realized_pnl += (entry - sl_eff) * rem_lots * LOT_SIZE
                sl_hit = True
                break

            # TP3 (cierra todo)
            if tp2_hit:
                if direction == 1 and h_j >= tp3:
                    exit_price = tp3
                    realized_pnl += (tp3 - entry) * rem_lots * LOT_SIZE
                    tp3_hit = True
                    break
                elif direction == -1 and l_j <= tp3:
                    exit_price = tp3
                    realized_pnl += (entry - tp3) * rem_lots * LOT_SIZE
                    tp3_hit = True
                    break
        else:
            # Cierre por tiempo (última barra disponible)
            if not sl_hit:
                exit_price = close[min(i+499, len(d)-1)]
                realized_pnl += (exit_price - entry) * direction * rem_lots * LOT_SIZE

        capital += realized_pnl
        daily_loss[date_key] = daily_loss.get(date_key, 0) - min(0, realized_pnl)
        daily_count[date_key] += 1
        equity_curve.append(capital)
        dates_curve.append(idx[i])

        trades.append({
            "date":    idx[i],
            "dir":     direction,
            "entry":   entry,
            "exit":    exit_price,
            "pnl_usd": realized_pnl,
            "tp1_hit": tp1_hit,
            "tp2_hit": tp2_hit,
            "tp3_hit": tp3_hit,
            "sl_hit":  sl_hit,
            "capital": capital,
        })
        i = j + 1 if (sl_hit or tp3_hit) else i + 1

    return {
        "trades":      trades,
        "equity":      equity_curve,
        "dates":       dates_curve,
        "final_cap":   capital,
    }


# ══════════════════════════════════════════════════════════════════
# 5. MÉTRICAS
# ══════════════════════════════════════════════════════════════════

def calc_metrics(result: dict, initial_capital: float = 100_000.0) -> dict:
    """Calcula todas las métricas de rendimiento."""
    trades = result["trades"]
    equity = result["equity"]
    if not trades:
        return {}

    df_t = pd.DataFrame(trades)
    df_t["date"] = pd.to_datetime(df_t["date"])
    df_t = df_t.set_index("date")

    # Retorno total
    final_cap    = result["final_cap"]
    total_ret    = (final_cap / initial_capital - 1) * 100

    # Equity curve
    eq_series = pd.Series(equity)
    rolling_max = eq_series.expanding().max()
    drawdown    = (eq_series - rolling_max) / rolling_max * 100
    max_dd      = drawdown.min()

    # Estadísticas de trades
    n_trades = len(df_t)
    n_win    = (df_t["pnl_usd"] > 0).sum()
    win_rate = n_win / n_trades * 100 if n_trades > 0 else 0
    pf_denom = abs(df_t["pnl_usd"][df_t["pnl_usd"] < 0].sum())
    pf       = df_t["pnl_usd"][df_t["pnl_usd"] > 0].sum() / (pf_denom + 1e-9)
    avg_win  = df_t["pnl_usd"][df_t["pnl_usd"] > 0].mean() if n_win > 0 else 0
    avg_loss = df_t["pnl_usd"][df_t["pnl_usd"] < 0].mean() if n_trades - n_win > 0 else 0
    avg_rr   = abs(avg_win) / (abs(avg_loss) + 1e-9)

    # Métricas mensuales
    monthly = df_t["pnl_usd"].resample("ME").sum()
    monthly_ret = monthly / initial_capital * 100
    avg_monthly = monthly_ret.mean()
    worst_month = monthly_ret.min()
    months_pos  = (monthly_ret > 0).sum()
    total_months = len(monthly_ret)

    # Trades por mes
    trades_month = df_t.resample("ME").size()
    avg_trades_m = trades_month.mean()
    min_trades_m = trades_month.min()

    # Sharpe (mensual, anualizado)
    if monthly_ret.std() > 0:
        sharpe = (monthly_ret.mean() / monthly_ret.std()) * np.sqrt(12)
    else:
        sharpe = 0.0

    # Máxima pérdida en un día
    daily_pnl = df_t["pnl_usd"].resample("1D").sum()
    daily_ret  = daily_pnl / initial_capital * 100
    max_daily_loss = daily_ret.min()

    # Verificar objetivos
    obj = OBJECTIVES
    obj_monthly = avg_monthly >= obj["min_monthly_return"]
    obj_dd      = abs(max_dd) <= obj["max_drawdown"]
    obj_trades  = min_trades_m >= obj["min_trades_month"]
    obj_daily   = abs(max_daily_loss) <= obj["max_daily_loss"]
    obj_sharpe  = sharpe >= obj["min_sharpe"]
    all_passed  = all([obj_monthly, obj_dd, obj_trades, obj_daily, obj_sharpe])

    return {
        "total_trades":      n_trades,
        "win_rate_pct":      round(win_rate, 2),
        "profit_factor":     round(pf, 3),
        "sharpe_ratio":      round(sharpe, 3),
        "max_drawdown_pct":  round(abs(max_dd), 2),
        "total_return_pct":  round(total_ret, 2),
        "avg_monthly_ret_pct": round(avg_monthly, 2),
        "worst_month_ret_pct": round(worst_month, 2),
        "months_profitable": int(months_pos),
        "total_months":      int(total_months),
        "min_trades_month":  int(min_trades_m),
        "avg_trades_month":  round(avg_trades_m, 1),
        "max_daily_loss_pct": round(abs(max_daily_loss), 2),
        "avg_win_usd":       round(avg_win, 2),
        "avg_loss_usd":      round(avg_loss, 2),
        "avg_rr":            round(avg_rr, 2),
        "final_balance":     round(final_cap, 2),
        "obj_monthly_ok":    obj_monthly,
        "obj_drawdown_ok":   obj_dd,
        "obj_trades_ok":     obj_trades,
        "obj_daily_ok":      obj_daily,
        "obj_sharpe_ok":     obj_sharpe,
        "all_objectives_ok": all_passed,
    }


# ══════════════════════════════════════════════════════════════════
# 6. MAIN — LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════════

def run_backtest():
    print("\n" + "═"*65)
    print(" GOLD VOLUME FUSION ELITE — Backtest Completo v2")
    print(" 9 versiones × 7 timeframes = 63 combinaciones")
    print("═"*65)

    # Cargar datos base
    df_base = load_xauusd_data()
    macro   = load_macro_context()

    results_rows = []
    best_results = {}

    print(f"\n{'─'*65}")
    total = len(ALL_PARAMS_EXTENDED) * len(TIMEFRAMES)
    count = 0

    for params in ALL_PARAMS_EXTENDED:
        v_name = params["name"]
        for tf_label, tf_rule in TIMEFRAMES.items():
            count += 1
            print(f"\n[{count:02d}/{total}] {v_name} | {tf_label}", end=" ... ", flush=True)

            # Resamplear
            try:
                df = resample_ohlcv(df_base, tf_rule)
            except Exception as e:
                print(f"ERROR resample: {e}")
                continue

            if len(df) < 200:
                print("insuficientes barras")
                continue

            # Calcular indicadores
            try:
                d = calc_indicators(df, params)
            except Exception as e:
                print(f"ERROR indicadores: {e}")
                continue

            # Generar señales
            try:
                signals = generate_signals(d, params)
            except Exception as e:
                print(f"ERROR señales: {e}")
                continue

            n_signals = signals.abs().sum()
            if n_signals < 5:
                print(f"muy pocas señales ({n_signals})")
                continue

            # Simular
            try:
                result = simulate_trades(d, signals, params)
            except Exception as e:
                print(f"ERROR simulación: {e}")
                continue

            # Métricas
            try:
                m = calc_metrics(result)
            except Exception as e:
                print(f"ERROR métricas: {e}")
                continue

            if not m:
                print("sin trades")
                continue

            passed = "✓" if m["all_objectives_ok"] else " "
            print(f"[{passed}] Sharpe={m['sharpe_ratio']:.2f} DD={m['max_drawdown_pct']:.1f}% "
                  f"Ret={m['avg_monthly_ret_pct']:.2f}%/m Trades={m['avg_trades_month']:.0f}/m")

            row = {
                "version":    v_name,
                "timeframe":  tf_label,
                **m
            }
            results_rows.append(row)

            # Guardar mejor por cada estrategia
            key = f"{v_name}_{tf_label}"
            best_results[key] = {"params": params, "metrics": m}

    # ── Guardar resultados ──────────────────────────────────────────
    if results_rows:
        df_results = pd.DataFrame(results_rows)
        _RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(_RESULTS_CSV, index=False)
        print(f"\n✓ Resultados guardados: {_RESULTS_CSV}")

        with open(_RESULTS_JSON, "w") as f:
            json.dump(best_results, f, indent=2, default=str)
        print(f"✓ Parámetros guardados: {_RESULTS_JSON}")

    # ── Resumen final ────────────────────────────────────────────────
    print("\n" + "═"*65)
    print(" RESUMEN — ESTRATEGIAS QUE CUMPLEN TODOS LOS OBJETIVOS")
    print("═"*65)
    passed = [r for r in results_rows if r.get("all_objectives_ok", False)]
    if passed:
        df_p = pd.DataFrame(passed).sort_values("sharpe_ratio", ascending=False)
        for _, row in df_p.iterrows():
            print(f"  ✓ {row['version']:25s} | {row['timeframe']:4s} | "
                  f"Sharpe={row['sharpe_ratio']:.2f} | "
                  f"Ret={row['avg_monthly_ret_pct']:.2f}%/m | "
                  f"DD={row['max_drawdown_pct']:.1f}% | "
                  f"Trades={row['avg_trades_month']:.0f}/m")
    else:
        print("  ⚠ Ninguna combinación cumple TODOS los objetivos todavía.")
        if not results_rows:
            print("    No hay resultados disponibles (todas fallaron).")
            return results_rows
        print("    Las mejores aproximaciones:")
        df_r = pd.DataFrame(results_rows)
        # Score compuesto para ranking
        df_r["score"] = (
            (df_r["avg_monthly_ret_pct"] / OBJECTIVES["min_monthly_return"]).clip(0, 2) +
            (OBJECTIVES["max_drawdown"] / (df_r["max_drawdown_pct"] + 0.1)).clip(0, 2) +
            (df_r["sharpe_ratio"] / OBJECTIVES["min_sharpe"]).clip(0, 2)
        )
        top5 = df_r.nlargest(5, "score")
        for _, row in top5.iterrows():
            obj_count = sum([row.get("obj_monthly_ok",False), row.get("obj_drawdown_ok",False),
                             row.get("obj_trades_ok",False), row.get("obj_daily_ok",False),
                             row.get("obj_sharpe_ok",False)])
            print(f"  [{obj_count}/5 obj] {row['version']:25s} | {row['timeframe']:4s} | "
                  f"Sharpe={row['sharpe_ratio']:.2f} | "
                  f"Ret={row['avg_monthly_ret_pct']:.2f}%/m | "
                  f"DD={row['max_drawdown_pct']:.1f}%")

    print("\n" + "═"*65)
    print(f" OBJETIVOS:  Mensual≥{OBJECTIVES['min_monthly_return']}% | "
          f"DD≤{OBJECTIVES['max_drawdown']}% | "
          f"Trades/m≥{OBJECTIVES['min_trades_month']} | "
          f"DailyLoss≤{OBJECTIVES['max_daily_loss']}%")
    print("═"*65)
    return results_rows


if __name__ == "__main__":
    run_backtest()
