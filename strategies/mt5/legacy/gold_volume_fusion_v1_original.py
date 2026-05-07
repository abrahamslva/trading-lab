"""
gold_volume_fusion_v1_original.py
===================================
ARCHIVO DE REFERENCIA INMUTABLE — NO MODIFICAR

Parámetros originales de la estrategia Gold Volume Fusion Elite
tal como están definidos en:
  mt5/EA_XAUUSD_GoldVolumeFusionElite_v1.mq5

Estos valores son la línea base contra la que se miden V2 y V3.
Usados en src/backtest_volume_fusion.py como PARAMS_V1.

Creado: 2026-05-06
"""

# ─────────────────────────────────────────────────────────────────
# PARÁMETROS ORIGINALES V1 — NO TOCAR
# ─────────────────────────────────────────────────────────────────
PARAMS_V1_ORIGINAL: dict = {
    # ── Gestión de riesgo ────────────────────────────────────────
    "risk_pct":          0.50,   # % riesgo por trade sobre capital
    "daily_loss_limit":  1.50,   # % pérdida diaria máxima → cierra operaciones
    "weekly_loss_limit": 3.00,   # % pérdida semanal máxima
    "max_trades_day":    2,      # máximo operaciones abiertas por día
    "max_trades_week":   6,      # máximo operaciones abiertas por semana

    # ── OBV (On-Balance Volume) ──────────────────────────────────
    "obv_ma_period":     20,     # período MA sobre OBV

    # ── CMF (Chaikin Money Flow) ─────────────────────────────────
    "cmf_period":        20,     # período de cálculo CMF
    "cmf_threshold":     0.05,   # umbral mínimo para señal alcista/bajista

    # ── MFI (Money Flow Index) ───────────────────────────────────
    "mfi_period":        14,
    "mfi_neutral_low":   35.0,   # zona neutral inferior
    "mfi_neutral_high":  65.0,   # zona neutral superior
    "mfi_oversold":      25.0,   # sobrevendido
    "mfi_overbought":    75.0,   # sobrecomprado

    # ── Chaikin Oscillator ───────────────────────────────────────
    "chaikin_fast":      3,
    "chaikin_slow":      10,

    # ── VPT (Volume Price Trend) ─────────────────────────────────
    "vpt_ma_period":     14,

    # ── VROC (Volume Rate of Change) ─────────────────────────────
    "vroc_period":       14,

    # ── PVI / NVI (Positive/Negative Volume Index) ───────────────
    "pvi_ma_period":     255,
    "nvi_ma_period":     255,

    # ── Volume Profile ───────────────────────────────────────────
    "vp_period":         100,    # barras lookback para VP
    "vp_zones":          20,     # número de zonas de precio
    "vp_poc_buffer":     0.003,  # distancia al POC = 0.3%

    # ── ATR / SL / TP ────────────────────────────────────────────
    "atr_period":        14,
    "sl_atr_mult":       1.8,    # SL = 1.8 × ATR
    "min_sl_pct":        0.002,  # mínimo SL absoluto 0.2%
    "tp1_ratio":         2.0,    # TP1 = 2.0 × SL
    "tp2_ratio":         4.0,    # TP2 = 4.0 × SL
    "tp3_ratio":         6.5,    # TP3 = 6.5 × SL
    "tp1_pct":           0.40,   # cierra 40% posición en TP1
    "tp2_pct":           0.35,   # cierra 35% posición en TP2

    # ── Scoring de entrada (0–12 puntos) ─────────────────────────
    "min_score":         5,      # mínimo 5/12 para abrir
    "high_conf_score":   8,      # alta confianza → tamaño aumentado

    # ── Filtros de sesión (hora UTC) ─────────────────────────────
    "london_start":      8,
    "london_end":        11,
    "overlap_start":     13,     # Londres + NY overlap
    "overlap_end":       17,
    "filter_weekdays":   True,   # solo martes–jueves

    # ── ADR (Average Daily Range) ─────────────────────────────────
    "adr_period":        14,
    "adr_max_used":      0.65,   # no entrar si ya se usó >65% del ADR diario
}

# ─────────────────────────────────────────────────────────────────
# OBJETIVOS DE VALIDACIÓN (del objectives.yaml)
# ─────────────────────────────────────────────────────────────────
OBJECTIVES_V1: dict = {
    "min_sharpe":         1.0,
    "max_drawdown":       8.0,   # %
    "max_daily_loss":     1.5,   # %
    "min_trades_month":   7,
    "min_monthly_return": 1.5,   # %
}

# ─────────────────────────────────────────────────────────────────
# CAMBIOS APLICADOS EN V3 (referencia de qué se modificó)
# ─────────────────────────────────────────────────────────────────
PARAMS_V3_CHANGES: dict = {
    # param          : (valor_v1, valor_v3, razón)
    "obv_ma_period"  : (20,    30,    "MA más lenta → menos falsas señales"),
    "cmf_threshold"  : (0.05,  0.08,  "Umbral más alto → señales de mayor convicción"),
    "tp1_ratio"      : (2.0,   2.5,   "TP1 más alejado → deja correr más"),
    "tp2_ratio"      : (4.0,   3.5,   "TP2 más cercano → asegura antes de TP3"),
    "tp3_ratio"      : (6.5,   8.0,   "TP3 más ambicioso"),
    "min_score"      : (5,     6,     "Mayor selectividad → menos trades, más calidad"),
    "filter_weekdays": (True,  False, "Opera todos los días → más frecuencia"),
}
