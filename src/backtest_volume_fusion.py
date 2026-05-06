"""
src/backtest_volume_fusion.py
==============================
Gold Volume Fusion Elite — Python Backtesting Engine
======================================================
Implementa la misma estrategia que el EA de MT5:
  OBV, VWAP, MFI, A/D, CMF, Volume Profile,
  Chaikin Oscillator, VPT, VROC, PVI, NVI

Backtesting: 10 años XAUUSD (GC=F COMEX)
TFs: 15m, 30m, 1h, 2h, 3h, 4h
3 iteraciones con optimización de parámetros

Objetivos:
  Sharpe >= 1.0 | MaxDD <= 8% | Min 7 trades/mes
  Min monthly return >= 1.5% | Max daily loss <= 1.5%
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

# Dukascopy loader (M15 histórico sin límite de tiempo)
try:
    from src.dukascopy_loader import download_xauusd_m15 as _dk_download
    _HAS_DUKASCOPY = True
except ImportError:
    try:
        from dukascopy_loader import download_xauusd_m15 as _dk_download
        _HAS_DUKASCOPY = True
    except ImportError:
        _HAS_DUKASCOPY = False

# MT5 Data Client (fuente preferida — conexión directa a MetaTrader 5)
try:
    from src.mt5_data_client import get_mt5_client as _get_mt5_client
    _HAS_MT5_CLIENT = True
except ImportError:
    try:
        from mt5_data_client import get_mt5_client as _get_mt5_client
        _HAS_MT5_CLIENT = True
    except ImportError:
        _HAS_MT5_CLIENT = False

# ──────────────────────────────────────────────────────────────────
# PARÁMETROS — Iteración 1 (base)
# ──────────────────────────────────────────────────────────────────
PARAMS_V1 = {
    "risk_pct":          0.50,   # % riesgo por trade
    "daily_loss_limit":  1.50,   # % pérdida diaria máxima
    "weekly_loss_limit": 3.00,   # % pérdida semanal máxima
    "max_trades_day":    2,
    "max_trades_week":   6,
    # Volume indicators
    "obv_ma_period":     20,
    "cmf_period":        20,
    "cmf_threshold":     0.05,
    "mfi_period":        14,
    "mfi_neutral_low":   35.0,
    "mfi_neutral_high":  65.0,
    "mfi_oversold":      25.0,
    "mfi_overbought":    75.0,
    "chaikin_fast":      3,
    "chaikin_slow":      10,
    "vpt_ma_period":     14,
    "vroc_period":       14,
    "pvi_ma_period":     255,
    "nvi_ma_period":     255,
    "vp_period":         100,    # barras para Volume Profile
    "vp_zones":          20,
    "vp_poc_buffer":     0.003,  # 0.3% distancia al POC
    # Risk/reward
    "atr_period":        14,
    "sl_atr_mult":       1.8,
    "min_sl_pct":        0.002,  # mínimo SL 0.2%
    "tp1_ratio":         2.0,
    "tp2_ratio":         4.0,
    "tp3_ratio":         6.5,
    "tp1_pct":           0.40,   # cierra 40% en TP1
    "tp2_pct":           0.35,   # cierra 35% en TP2
    # Entry scoring
    "min_score":         5,      # mínimo de 5/12 puntos
    "high_conf_score":   8,
    # Session filters (UTC hour)
    "london_start":      8,
    "london_end":        11,
    "overlap_start":     13,
    "overlap_end":       17,
    "filter_weekdays":   True,   # solo Mar-Jue
    # ADR filter
    "adr_period":        14,
    "adr_max_used":      0.65,
}

# ──────────────────────────────────────────────────────────────────
# PARÁMETROS V3 — coinciden exactamente con EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5
# ──────────────────────────────────────────────────────────────────
PARAMS_V3 = {**PARAMS_V1,
    "obv_ma_period":   30,     # [V3: 20→30]
    "cmf_threshold":   0.08,   # [V3: 0.05→0.08]
    "tp1_ratio":       2.5,    # [V3: 2.0→2.5]
    "tp2_ratio":       3.5,    # [V3: 4.0→3.5]
    "tp3_ratio":       8.0,    # [V3: 6.5→8.0]
    "min_score":       6,      # [V3: 5→6 mayor selectividad]
    "filter_weekdays": False,  # [V3: True→False mayor frecuencia]
}

# Objetivos objetivo (del objectives.yaml)
OBJECTIVES = {
    "min_sharpe":         1.0,
    "max_drawdown":       8.0,
    "max_daily_loss":     1.5,
    "min_trades_month":   7,
    "min_monthly_return": 1.5,
}

# ──────────────────────────────────────────────────────────────────
# 1. DESCARGA DE DATOS
# ──────────────────────────────────────────────────────────────────
def download_data(symbol: str = "GC=F",
                  start: str = "2015-01-01",
                  end:   str = "2025-01-01",
                  interval: str = "1d") -> pd.DataFrame:
    """
    Descarga datos OHLCV de yfinance.
    GC=F = Gold Futures COMEX (volumen real).
    Para intervalos intradiarios >= 1h usa hasta ~2 años.
    """
    print(f"  Descargando {symbol} {interval} desde {start} hasta {end}...")

    # yfinance limita intraday histórico
    intraday_intervals = ["1m","2m","5m","15m","30m","60m","1h","90m"]
    if interval in intraday_intervals:
        # Descargar en chunks de 59 días para intervalos < 1h
        # Para 1h/60m descarga ~730 días
        df = yf.download(symbol, start=start, end=end,
                         interval=interval, auto_adjust=True,
                         progress=False)
        if df.empty:
            # Fallback: usar lo disponible
            print(f"  WARNING: No hay datos intradiarios para {interval}, usando datos disponibles")
            df = yf.download(symbol, period="730d" if interval in ["60m","1h"] else "60d",
                             interval=interval, auto_adjust=True, progress=False)
    else:
        df = yf.download(symbol, start=start, end=end,
                         interval=interval, auto_adjust=True,
                         progress=False)

    if df.empty:
        raise ValueError(f"No se pudieron descargar datos para {symbol} {interval}")

    # Aplanar MultiIndex (distintas versiones de yfinance usan distintas estructuras)
    if isinstance(df.columns, pd.MultiIndex):
        for level in range(df.columns.nlevels):
            lvl = df.columns.get_level_values(level)
            if any(str(c).lower() in ["open","high","low","close","volume"] for c in lvl):
                df.columns = lvl
                break
        else:
            df.columns = df.columns.get_level_values(0)

    # Normalizar nombres de columnas a Title Case
    df.columns = [str(c).strip().title() for c in df.columns]

    cols_needed = [c for c in ["Open","High","Low","Close","Volume"] if c in df.columns]
    if len(cols_needed) < 5:
        raise ValueError(f"Columnas insuficientes en datos descargados: {list(df.columns)}")
    df = df[cols_needed].copy()

    # Eliminar barras sin volumen o datos inválidos (evita divisiones por cero)
    df = df[df["Volume"] > 0].dropna()

    df.index = pd.to_datetime(df.index, utc=True)
    print(f"  OK: {len(df)} barras desde {df.index[0]} hasta {df.index[-1]}")
    return df


def resample_data(df_1h: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Remuestrea datos horarios a mayor timeframe."""
    rule_map = {
        "15min": "15min",
        "30min": "30min",
        "1h":    "1h",
        "2h":    "2h",
        "3h":    "3h",
        "4h":    "4h",
    }
    rule = rule_map.get(tf, tf)
    resampled = df_1h.resample(rule).agg({
        "Open":   "first",
        "High":   "max",
        "Low":    "min",
        "Close":  "last",
        "Volume": "sum"
    }).dropna()
    return resampled


def download_dukascopy_ohlcv(
    start: str = "2015-01-01",
    end:   str = "2025-01-01",
    timeframe: str = "15min",
    cache_dir: str = "data/dukascopy",
) -> pd.DataFrame:
    """
    Descarga datos XAUUSD de Dukascopy (CDN público, sin credenciales).
    Soporta cualquier timeframe: '15min', '30min', '1h', '4h', etc.
    Los datos se cachean en disco para no re-descargar en ejecuciones siguientes.
    Incluye datos históricos de hasta ~20 años.
    """
    if not _HAS_DUKASCOPY:
        raise RuntimeError(
            "dukascopy_loader no disponible. "
            "Asegúrate de que src/dukascopy_loader.py existe."
        )

    # Verificar si ya existe parquet cacheado para este timeframe+periodo
    cache_path = os.path.join(cache_dir, f"XAUUSD_{timeframe}_{start[:7]}_{end[:7]}.parquet")
    if os.path.exists(cache_path):
        print(f"  Cargando desde caché: {cache_path}")
        df = pd.read_parquet(cache_path)
        df.index = pd.to_datetime(df.index, utc=True)
        print(f"  OK: {len(df)} barras desde {df.index[0]} hasta {df.index[-1]}")
        return df

    df = _dk_download(
        start=start,
        end=end,
        timeframe=timeframe,
        cache_dir=cache_dir,
        max_workers=8,
        show_progress=True,
    )

    # Guardar parquet para carga rápida futura
    os.makedirs(cache_dir, exist_ok=True)
    df.to_parquet(cache_path)
    print(f"  Datos guardados en: {cache_path}")
    return df


# ──────────────────────────────────────────────────────────────────
# 2. INDICADORES DE VOLUMEN
# ──────────────────────────────────────────────────────────────────
class VolumeIndicators:
    """Calcula todos los indicadores de volumen sobre un DataFrame OHLCV."""

    @staticmethod
    def obv(df: pd.DataFrame, ma_period: int = 20) -> pd.DataFrame:
        """On-Balance Volume + su MA."""
        direction = np.sign(df["Close"].diff())
        direction.iloc[0] = 0
        obv = (direction * df["Volume"]).cumsum()
        df["OBV"]    = obv
        df["OBV_MA"] = obv.ewm(span=ma_period, adjust=False).mean()
        return df

    @staticmethod
    def vwap_daily(df: pd.DataFrame) -> pd.DataFrame:
        """VWAP con reset diario (a las 22:00 UTC = apertura Asia)."""
        tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
        # Reset a las 22:00 UTC (apertura Asia); floor('D') funciona con índices tz-aware
        adjusted  = df.index - pd.Timedelta(hours=22)
        day_group = adjusted.floor("D")

        tp_vol    = tp * df["Volume"]
        cumsum_pv = tp_vol.groupby(day_group).cumsum()
        cumsum_v  = df["Volume"].groupby(day_group).cumsum()
        df["VWAP"] = cumsum_pv / cumsum_v.replace(0, np.nan)
        df.drop(columns=["_trading_day", "_day_label"], inplace=True, errors="ignore")
        return df

    @staticmethod
    def mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Money Flow Index (RSI ponderado por volumen)."""
        tp = (df["High"] + df["Low"] + df["Close"]) / 3.0
        mf = tp * df["Volume"]

        tp_diff = tp.diff()
        pos_mf = mf.where(tp_diff > 0, 0.0)
        neg_mf = mf.where(tp_diff < 0, 0.0)

        pos_sum = pos_mf.rolling(period).sum()
        neg_sum = neg_mf.abs().rolling(period).sum()

        mfr = pos_sum / neg_sum.replace(0, np.nan)
        df["MFI"] = 100.0 - (100.0 / (1.0 + mfr))
        return df

    @staticmethod
    def ad_line(df: pd.DataFrame) -> pd.DataFrame:
        """Accumulation/Distribution Line."""
        hl = df["High"] - df["Low"]
        clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / hl.replace(0, np.nan)
        df["AD"] = (clv * df["Volume"]).cumsum()
        return df

    @staticmethod
    def cmf(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """Chaikin Money Flow."""
        hl = df["High"] - df["Low"]
        clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / hl.replace(0, np.nan)
        mfv = clv * df["Volume"]
        df["CMF"] = mfv.rolling(period).sum() / df["Volume"].rolling(period).sum().replace(0, np.nan)
        return df

    @staticmethod
    def chaikin_oscillator(df: pd.DataFrame, fast: int = 3, slow: int = 10) -> pd.DataFrame:
        """Chaikin Oscillator = EMA_fast(AD) - EMA_slow(AD)."""
        if "AD" not in df.columns:
            df = VolumeIndicators.ad_line(df)
        df["ChaikinOsc"] = (
            df["AD"].ewm(span=fast, adjust=False).mean() -
            df["AD"].ewm(span=slow, adjust=False).mean()
        )
        return df

    @staticmethod
    def vpt(df: pd.DataFrame, ma_period: int = 14) -> pd.DataFrame:
        """Volume Price Trend."""
        pct_change = df["Close"].pct_change()
        vpt_val = (pct_change * df["Volume"]).cumsum()
        df["VPT"]    = vpt_val
        df["VPT_MA"] = vpt_val.ewm(span=ma_period, adjust=False).mean()
        return df

    @staticmethod
    def vroc(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Volume Rate of Change."""
        df["VROC"] = df["Volume"].pct_change(period) * 100.0
        return df

    @staticmethod
    def pvi_nvi(df: pd.DataFrame,
                pvi_ma: int = 255, nvi_ma: int = 255) -> pd.DataFrame:
        """
        Positive Volume Index (sube cuando volumen sube — retail)
        Negative Volume Index (sube cuando volumen baja — smart money)
        """
        pct = df["Close"].pct_change()
        vol_up   = df["Volume"] > df["Volume"].shift(1)
        vol_down = df["Volume"] < df["Volume"].shift(1)

        pvi_arr = np.ones(len(df)) * 1000.0
        nvi_arr = np.ones(len(df)) * 1000.0

        for i in range(1, len(df)):
            if vol_up.iloc[i]:
                pvi_arr[i] = pvi_arr[i-1] * (1.0 + pct.iloc[i])
            else:
                pvi_arr[i] = pvi_arr[i-1]

            if vol_down.iloc[i]:
                nvi_arr[i] = nvi_arr[i-1] * (1.0 + pct.iloc[i])
            else:
                nvi_arr[i] = nvi_arr[i-1]

        df["PVI"] = pvi_arr
        df["NVI"] = nvi_arr

        # MAs para señal (EMA)
        df["PVI_MA"] = pd.Series(pvi_arr, index=df.index).ewm(span=pvi_ma, adjust=False).mean()
        df["NVI_MA"] = pd.Series(nvi_arr, index=df.index).ewm(span=nvi_ma, adjust=False).mean()
        return df

    @staticmethod
    def volume_profile(df: pd.DataFrame,
                       period: int = 100,
                       zones: int = 20,
                       poc_buffer: float = 0.003) -> pd.DataFrame:
        """
        Volume Profile simulado con rolling window.
        Calcula POC, VAH, VAL para cada barra.
        """
        n = len(df)
        poc = np.full(n, np.nan)
        vah = np.full(n, np.nan)
        val = np.full(n, np.nan)
        vp_zone = np.zeros(n, dtype=int)

        for i in range(period, n):
            window = df.iloc[i-period:i]
            h_max = window["High"].max()
            h_min = window["Low"].min()
            rng = h_max - h_min
            if rng <= 0:
                poc[i] = df["Close"].iloc[i]
                vah[i] = poc[i] * 1.002
                val[i] = poc[i] * 0.998
                continue

            zone_size = rng / zones
            zone_centers = h_min + (np.arange(zones) + 0.5) * zone_size
            zone_vols = np.zeros(zones)

            tp = (window["High"] + window["Low"] + window["Close"]) / 3.0
            for j in range(len(window)):
                z = int((tp.iloc[j] - h_min) / zone_size)
                z = max(0, min(zones - 1, z))
                zone_vols[z] += window["Volume"].iloc[j]

            poc_idx = np.argmax(zone_vols)
            poc[i] = zone_centers[poc_idx]

            # Value Area 70%
            total_vol = zone_vols.sum()
            target = total_vol * 0.70
            va_lo = va_hi = poc_idx
            va_vol = zone_vols[poc_idx]

            while va_vol < target:
                ext_lo = zone_vols[va_lo - 1] if va_lo > 0 else 0
                ext_hi = zone_vols[va_hi + 1] if va_hi < zones - 1 else 0
                if ext_hi >= ext_lo and va_hi < zones - 1:
                    va_hi += 1
                    va_vol += zone_vols[va_hi]
                elif va_lo > 0:
                    va_lo -= 1
                    va_vol += zone_vols[va_lo]
                else:
                    break

            vah[i] = zone_centers[va_hi] + zone_size * 0.5
            val[i] = zone_centers[va_lo] - zone_size * 0.5

            # Zona del precio actual
            cp = df["Close"].iloc[i]
            if cp > vah[i]:
                vp_zone[i] = 1
            elif cp < val[i]:
                vp_zone[i] = -1
            else:
                vp_zone[i] = 0

        df["VP_POC"]  = poc
        df["VP_VAH"]  = vah
        df["VP_VAL"]  = val
        df["VP_ZONE"] = vp_zone
        return df

    @staticmethod
    def add_all(df: pd.DataFrame, p: dict) -> pd.DataFrame:
        """Agrega todos los indicadores de volumen al DataFrame."""
        print("    Calculando indicadores de volumen...")
        df = VolumeIndicators.obv(df, p["obv_ma_period"])
        df = VolumeIndicators.vwap_daily(df)
        df = VolumeIndicators.mfi(df, p["mfi_period"])
        df = VolumeIndicators.ad_line(df)
        df = VolumeIndicators.cmf(df, p["cmf_period"])
        df = VolumeIndicators.chaikin_oscillator(df, p["chaikin_fast"], p["chaikin_slow"])
        df = VolumeIndicators.vpt(df, p["vpt_ma_period"])
        df = VolumeIndicators.vroc(df, p["vroc_period"])
        df = VolumeIndicators.pvi_nvi(df, p["pvi_ma_period"], p["nvi_ma_period"])
        df = VolumeIndicators.volume_profile(df, p["vp_period"], p["vp_zones"], p["vp_poc_buffer"])

        # ATR para stops
        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - df["Close"].shift(1)).abs(),
            (df["Low"]  - df["Close"].shift(1)).abs()
        ], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(p["atr_period"]).mean()

        # EMAs de tendencia
        df["EMA20"]  = df["Close"].ewm(span=20,  adjust=False).mean()
        df["EMA50"]  = df["Close"].ewm(span=50,  adjust=False).mean()
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

        # ADR correcto: resampling a diario (igual que el EA que usa PERIOD_D1)
        # Evita el bug de comparar rango de barra intradiaria vs ADR diario
        df_d = df[["High","Low"]].resample("1D").agg({"High":"max","Low":"min"}).dropna()
        df_d["DailyRange"] = df_d["High"] - df_d["Low"]
        df_d["ADR"]        = df_d["DailyRange"].rolling(p["adr_period"]).mean()

        # Mapear ADR por fecha (string evita problemas de timezone en el join)
        df_d["_date"] = df_d.index.strftime("%Y-%m-%d")
        df["_date"]   = df.index.strftime("%Y-%m-%d")
        adr_map = dict(zip(df_d["_date"], df_d["ADR"]))
        df["ADR"] = df["_date"].map(adr_map).ffill()
        df.drop(columns=["_date"], inplace=True, errors="ignore")

        # Rango acumulado del día actual (cummax/cummin desde apertura de cada día)
        # Reproduce el PERIOD_D1 High/Low del EA: iHigh(D1,0) y iLow(D1,0) en tiempo real
        _date_key = df.index.strftime("%Y-%m-%d")
        df["DayHigh"]    = df["High"].groupby(_date_key).cummax()
        df["DayLow"]     = df["Low"].groupby(_date_key).cummin()
        df["TodayRange"] = df["DayHigh"] - df["DayLow"]

        return df


# ──────────────────────────────────────────────────────────────────
# 3. SCORING ENGINE — Gold Volume Fusion Score
# ──────────────────────────────────────────────────────────────────
def calculate_gvfs(row: pd.Series, p: dict) -> int:
    """
    Calcula el Gold Volume Fusion Score (-12 a +12).
    Positivo = señal alcista, negativo = señal bajista.
    """
    score = 0

    # 1. OBV vs su MA
    if pd.notna(row.get("OBV")) and pd.notna(row.get("OBV_MA")):
        score += 1 if row["OBV"] > row["OBV_MA"] else -1

    # 2. Precio vs VWAP
    if pd.notna(row.get("VWAP")):
        score += 1 if row["Close"] > row["VWAP"] else -1

    # 3. CMF
    if pd.notna(row.get("CMF")):
        if   row["CMF"] >  p["cmf_threshold"]: score += 1
        elif row["CMF"] < -p["cmf_threshold"]: score -= 1

    # 4. MFI
    if pd.notna(row.get("MFI")):
        mfi = row["MFI"]
        if   mfi < p["mfi_oversold"]:   score += 1  # oversold = oportunidad long
        elif mfi > p["mfi_overbought"]: score -= 1  # overbought = oportunidad short
        elif p["mfi_neutral_low"] <= mfi <= p["mfi_neutral_high"]:
            # neutral: confirmar con OBV
            if pd.notna(row.get("OBV")) and pd.notna(row.get("OBV_MA")):
                score += 1 if row["OBV"] > row["OBV_MA"] else -1

    # 5. Chaikin Oscillator (momentum A/D)
    if pd.notna(row.get("ChaikinOsc")):
        score += 1 if row["ChaikinOsc"] > 0 else -1

    # 6. VPT vs su MA
    if pd.notna(row.get("VPT")) and pd.notna(row.get("VPT_MA")):
        score += 1 if row["VPT"] > row["VPT_MA"] else -1

    # 7. VROC (volumen aumentando = confirmación)
    if pd.notna(row.get("VROC")):
        score += 1 if row["VROC"] > 0 else -1

    # 8. NVI > NVI_MA (smart money alcista)
    if pd.notna(row.get("NVI")) and pd.notna(row.get("NVI_MA")):
        score += 1 if row["NVI"] > row["NVI_MA"] else -1

    # 9. PVI > PVI_MA (retail confirma tendencia)
    if pd.notna(row.get("PVI")) and pd.notna(row.get("PVI_MA")):
        score += 1 if row["PVI"] > row["PVI_MA"] else -1

    # 10. Volume Profile: posición del precio
    if pd.notna(row.get("VP_POC")):
        poc_dist = abs(row["Close"] - row["VP_POC"]) / row["Close"]
        if poc_dist < p["vp_poc_buffer"]:
            # Cerca del POC: CMF decide
            if pd.notna(row.get("CMF")):
                score += 1 if row["CMF"] > 0 else -1
        elif pd.notna(row.get("VP_ZONE")):
            if row["VP_ZONE"] == 0:  # Dentro del Value Area
                if pd.notna(row.get("OBV")) and pd.notna(row.get("OBV_MA")):
                    score += 1 if row["OBV"] > row["OBV_MA"] else -1

    # 11. EMA trend alignment bonus
    if pd.notna(row.get("EMA20")) and pd.notna(row.get("EMA50")) and pd.notna(row.get("EMA200")):
        if row["EMA20"] > row["EMA50"] > row["EMA200"]:
            if score > 0: score = min(score + 1, 12)
        elif row["EMA20"] < row["EMA50"] < row["EMA200"]:
            if score < 0: score = max(score - 1, -12)

    return score


# ──────────────────────────────────────────────────────────────────
# 4. SESSION FILTER
# ──────────────────────────────────────────────────────────────────
def is_valid_session(ts: pd.Timestamp, p: dict) -> bool:
    """Verifica si el timestamp está en sesión válida (UTC)."""
    hour = ts.hour
    dow  = ts.dayofweek  # 0=Lun, 4=Vie, 5=Sab, 6=Dom

    # Fin de semana
    if dow >= 5: return False

    # Filtro días
    if p.get("filter_weekdays"):
        # Solo martes (1), miércoles (2), jueves (3)
        if dow not in [1, 2, 3]: return False

    # Viernes tarde
    if dow == 4 and hour >= 14: return False

    # Ventana London
    london  = p["london_start"] <= hour < p["london_end"]
    # Ventana Overlap NY-London
    overlap = p["overlap_start"] <= hour < p["overlap_end"]

    return london or overlap


def is_valid_dayofweek(ts: pd.Timestamp, p: dict) -> bool:
    """Filtro por día de la semana (más suave, para datos diarios)."""
    dow = ts.dayofweek
    if dow >= 5: return False
    if p.get("filter_weekdays") and dow not in [1, 2, 3]: return False
    return True


# ──────────────────────────────────────────────────────────────────
# 5. BACKTESTING ENGINE
# ──────────────────────────────────────────────────────────────────
class GoldBacktester:
    """
    Motor de backtesting para la estrategia Gold Volume Fusion Elite.
    Soporta múltiples timeframes y gestión de posiciones escalada.
    """

    def __init__(self, df: pd.DataFrame, params: dict,
                 initial_balance: float = 100_000.0,
                 is_intraday: bool = True):
        self.df      = df.copy()
        self.p       = params
        self.balance = initial_balance
        self.equity  = initial_balance
        self.is_intraday = is_intraday

        # Estado del backtesting
        self.trades: list[dict] = []
        self.equity_curve: list[tuple] = []
        self.open_positions: list[dict] = []
        self.daily_start_balance   = initial_balance
        self.weekly_start_balance  = initial_balance
        self.daily_trades   = 0
        self.weekly_trades  = 0
        self.last_day  = None
        self.last_week = None

    def run(self, verbose: bool = True) -> pd.DataFrame:
        """Ejecuta el backtest barra por barra."""
        if verbose:
            print("    Ejecutando backtest...")
        warmup = max(
            self.p["nvi_ma_period"],
            self.p["pvi_ma_period"],
            self.p["vp_period"],
            self.p["adr_period"] * 5,
            300
        )

        for i in range(warmup, len(self.df)):
            row = self.df.iloc[i]
            ts  = self.df.index[i]

            # Reset contadores
            self._reset_daily(ts)
            self._reset_weekly(ts)

            # Actualizar posiciones abiertas
            self._update_positions(row, ts)

            # Registrar equity
            self.equity_curve.append((ts, self.equity))

            # Filtros de entrada
            if not self._can_open():
                continue

            # Filtro de sesión
            if self.is_intraday and not is_valid_session(ts, self.p):
                continue
            elif not self.is_intraday and not is_valid_dayofweek(ts, self.p):
                continue

            # Calcular score
            score = calculate_gvfs(row, self.p)

            # ADR filter
            if not self._adr_filter(row):
                continue

            # Entrada
            if score >= self.p["min_score"]:
                self._open_trade(row, ts, score, direction=1)
            elif score <= -self.p["min_score"]:
                self._open_trade(row, ts, score, direction=-1)

        # Cerrar posiciones abiertas al final
        last_row = self.df.iloc[-1]
        for pos in self.open_positions[:]:
            self._close_position(pos, last_row["Close"], self.df.index[-1], "EOD")
        self.open_positions.clear()

        return pd.DataFrame(self.trades)

    def _reset_daily(self, ts: pd.Timestamp):
        day = ts.date()
        if self.last_day != day:
            self.daily_start_balance = self.balance
            self.daily_trades = 0
            self.last_day = day

    def _reset_weekly(self, ts: pd.Timestamp):
        week = ts.isocalendar()[:2]
        if self.last_week != week:
            self.weekly_start_balance = self.balance
            self.weekly_trades = 0
            self.last_week = week

    def _can_open(self) -> bool:
        # Límite de trades
        if self.daily_trades  >= self.p["max_trades_day"]:  return False
        if self.weekly_trades >= self.p["max_trades_week"]: return False

        # Daily loss limit
        daily_loss = (self.balance - self.daily_start_balance) / self.daily_start_balance * 100
        if daily_loss < -self.p["daily_loss_limit"]: return False

        # Weekly loss limit
        weekly_loss = (self.balance - self.weekly_start_balance) / self.weekly_start_balance * 100
        if weekly_loss < -self.p["weekly_loss_limit"]: return False

        return True

    def _adr_filter(self, row: pd.Series) -> bool:
        """No entrar si el rango del día ya superó el límite del ADR."""
        # Para datos diarios el ADR filter no aplica (la barra YA es el día completo)
        if not self.is_intraday:
            return True
        if pd.isna(row.get("ADR")) or row["ADR"] == 0:
            return True
        # Usar rango acumulado del día (TodayRange), NO el rango de la barra actual
        # Bug original: usaba H-L de la barra → siempre ≈ ADR → rechazaba todo
        today_range = row.get("TodayRange", np.nan)
        if pd.isna(today_range) or today_range == 0:
            today_range = row["High"] - row["Low"]
        return (today_range / row["ADR"]) < self.p["adr_max_used"]

    def _calc_lot_size(self, price: float, sl_dist: float) -> float:
        """Calcula tamaño de posición basado en % riesgo."""
        risk_usd = self.balance * self.p["risk_pct"] / 100.0
        # Para XAU/USD: 1 lote = 100 oz, valor pip ~$1 por 0.01 usd
        # En GC Futures: 1 contrato = 100 oz; pip = 0.10 = $10
        # Para XAUUSD spot: valor de 1 pip (0.01) = $1 por 0.01 lote
        # Simplificación: lot_size = risk_usd / (sl_dist * 100)
        # Donde sl_dist está en USD y 1 lote = 100 oz
        if sl_dist == 0:
            return 0.01
        lots = risk_usd / (sl_dist * 100.0)
        return max(0.01, round(lots, 2))

    def _open_trade(self, row: pd.Series, ts: pd.Timestamp,
                    score: int, direction: int):
        """Abre una nueva posición (dividida en 3 sub-posiciones para TP)."""
        if pd.isna(row.get("ATR")) or row["ATR"] == 0:
            return

        entry = row["Close"]
        atr   = row["ATR"]
        sl_dist = max(atr * self.p["sl_atr_mult"],
                      entry * self.p["min_sl_pct"])

        sl  = entry - direction * sl_dist
        tp1 = entry + direction * sl_dist * self.p["tp1_ratio"]
        tp2 = entry + direction * sl_dist * self.p["tp2_ratio"]
        tp3 = entry + direction * sl_dist * self.p["tp3_ratio"]

        # Ajustar riesgo por score
        risk_mult = 1.0 if abs(score) >= self.p["high_conf_score"] else 0.75
        lots = self._calc_lot_size(entry, sl_dist) * risk_mult

        pos = {
            "id":          len(self.trades),
            "open_time":   ts,
            "entry":       entry,
            "direction":   direction,
            "score":       score,
            "sl":          sl,
            "tp1":         tp1,
            "tp2":         tp2,
            "tp3":         tp3,
            "lots":        lots,
            "lots_remaining": lots,
            "tp1_hit":     False,
            "tp2_hit":     False,
            "sl_at_be":    False,
            "status":      "open",
        }
        self.open_positions.append(pos)
        self.daily_trades  += 1
        self.weekly_trades += 1

    def _update_positions(self, row: pd.Series, ts: pd.Timestamp):
        """Verifica TP/SL de posiciones abiertas."""
        for pos in self.open_positions[:]:
            d     = pos["direction"]
            entry = pos["entry"]
            price_high = row["High"]
            price_low  = row["Low"]
            price_close= row["Close"]

            # Determinar precio favorable/adverso
            fav   = price_high if d == 1 else price_low
            adv   = price_low  if d == 1 else price_high

            # Verificar SL
            sl_hit = (d == 1 and adv <= pos["sl"]) or (d == -1 and adv >= pos["sl"])
            if sl_hit:
                self._close_position(pos, pos["sl"], ts, "SL")
                continue

            # TP1
            if not pos["tp1_hit"]:
                tp1_hit = (d == 1 and fav >= pos["tp1"]) or (d == -1 and fav <= pos["tp1"])
                if tp1_hit:
                    close_lots = pos["lots"] * self.p["tp1_pct"]
                    self._record_partial_close(pos, pos["tp1"], ts, close_lots, "TP1")
                    pos["lots_remaining"] -= close_lots
                    pos["tp1_hit"] = True
                    # Mover SL a breakeven
                    pos["sl"] = entry
                    pos["sl_at_be"] = True
                    continue

            # TP2
            if pos["tp1_hit"] and not pos["tp2_hit"]:
                tp2_hit = (d == 1 and fav >= pos["tp2"]) or (d == -1 and fav <= pos["tp2"])
                if tp2_hit:
                    close_lots = pos["lots"] * self.p["tp2_pct"]
                    self._record_partial_close(pos, pos["tp2"], ts, close_lots, "TP2")
                    pos["lots_remaining"] -= close_lots
                    pos["tp2_hit"] = True
                    # Trailing stop a TP1
                    pos["sl"] = pos["tp1"]
                    continue

            # TP3 (resto de la posición)
            if pos["tp1_hit"] and pos["tp2_hit"]:
                tp3_hit = (d == 1 and fav >= pos["tp3"]) or (d == -1 and fav <= pos["tp3"])
                if tp3_hit:
                    self._close_position(pos, pos["tp3"], ts, "TP3")
                    continue

                # Trailing stop con EMA20
                if pd.notna(row.get("EMA20")) and pd.notna(row.get("ATR")):
                    if d == 1:
                        trail = row["EMA20"] - row["ATR"] * 0.5
                        if trail > pos["sl"]:
                            pos["sl"] = trail
                    else:
                        trail = row["EMA20"] + row["ATR"] * 0.5
                        if trail < pos["sl"]:
                            pos["sl"] = trail

    def _record_partial_close(self, pos: dict, close_price: float,
                               ts: pd.Timestamp, lots: float, reason: str):
        """Registra un cierre parcial."""
        pnl = (close_price - pos["entry"]) * pos["direction"] * lots * 100.0
        self.balance += pnl
        self.equity   = self.balance
        self.trades.append({
            "open_time":  pos["open_time"],
            "close_time": ts,
            "entry":      pos["entry"],
            "exit":       close_price,
            "direction":  pos["direction"],
            "score":      pos["score"],
            "lots":       lots,
            "pnl_usd":    pnl,
            "pnl_pct":    pnl / (self.balance - pnl) * 100,
            "reason":     reason,
            "duration_h": (ts - pos["open_time"]).total_seconds() / 3600,
        })

    def _close_position(self, pos: dict, close_price: float,
                        ts: pd.Timestamp, reason: str):
        """Cierra toda la posición restante."""
        lots = pos.get("lots_remaining", pos["lots"])
        pnl  = (close_price - pos["entry"]) * pos["direction"] * lots * 100.0
        self.balance += pnl
        self.equity   = self.balance

        self.trades.append({
            "open_time":  pos["open_time"],
            "close_time": ts,
            "entry":      pos["entry"],
            "exit":       close_price,
            "direction":  pos["direction"],
            "score":      pos["score"],
            "lots":       lots,
            "pnl_usd":    pnl,
            "pnl_pct":    pnl / max(self.balance - pnl, 1) * 100,
            "reason":     reason,
            "duration_h": (ts - pos["open_time"]).total_seconds() / 3600,
        })

        if pos in self.open_positions:
            self.open_positions.remove(pos)


# ──────────────────────────────────────────────────────────────────
# 6. MÉTRICAS DE RENDIMIENTO
# ──────────────────────────────────────────────────────────────────
def compute_metrics(trades_df: pd.DataFrame,
                    equity_curve: list[tuple],
                    initial_balance: float = 100_000.0) -> dict:
    """Calcula métricas completas de backtesting."""
    if trades_df.empty:
        return {"error": "Sin trades"}

    equity_ts = pd.Series(
        [e for _, e in equity_curve],
        index=[t for t, _ in equity_curve]
    )

    pnl = trades_df["pnl_usd"]
    total_trades = len(trades_df)
    winners = pnl[pnl > 0]
    losers  = pnl[pnl < 0]

    win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0
    avg_win  = winners.mean() if len(winners) > 0 else 0
    avg_loss = losers.mean()  if len(losers)  > 0 else 0
    profit_factor = (winners.sum() / abs(losers.sum())) if abs(losers.sum()) > 0 else np.inf

    # Drawdown máximo
    equity_arr  = equity_ts.values
    running_max = np.maximum.accumulate(equity_arr)
    drawdowns   = (equity_arr - running_max) / running_max * 100
    max_dd      = abs(drawdowns.min())

    # Retorno total
    total_return = (equity_arr[-1] - initial_balance) / initial_balance * 100

    # Retornos diarios para Sharpe
    daily_equity = equity_ts.resample("1D").last().dropna()
    daily_ret    = daily_equity.pct_change().dropna()
    sharpe       = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)
                    if daily_ret.std() > 0 else 0)

    # Estadísticas mensuales
    if not trades_df.empty and "close_time" in trades_df.columns:
        trades_df = trades_df.copy()
        trades_df["month"] = pd.to_datetime(trades_df["close_time"]).dt.to_period("M")
        monthly_pnl   = trades_df.groupby("month")["pnl_usd"].sum()
        monthly_ret   = monthly_pnl / initial_balance * 100
        monthly_count = trades_df.groupby("month").size()

        worst_month_ret    = monthly_ret.min() if len(monthly_ret) > 0 else 0
        avg_monthly_ret    = monthly_ret.mean() if len(monthly_ret) > 0 else 0
        min_trades_month   = monthly_count.min() if len(monthly_count) > 0 else 0
        avg_trades_month   = monthly_count.mean() if len(monthly_count) > 0 else 0
        months_profitable  = (monthly_ret > 0).sum()
        total_months       = len(monthly_ret)
    else:
        worst_month_ret  = avg_monthly_ret = 0
        min_trades_month = avg_trades_month = 0
        months_profitable = total_months = 0

    # Daily max loss
    if not trades_df.empty and "close_time" in trades_df.columns:
        trades_df["day"] = pd.to_datetime(trades_df["close_time"]).dt.date
        daily_pnl  = trades_df.groupby("day")["pnl_usd"].sum()
        max_daily_loss = abs(daily_pnl.min()) / initial_balance * 100 if len(daily_pnl) > 0 else 0
    else:
        max_daily_loss = 0

    # RR promedio
    avg_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    return {
        "total_trades":       total_trades,
        "win_rate_pct":       round(win_rate, 2),
        "profit_factor":      round(profit_factor, 3),
        "sharpe_ratio":       round(sharpe, 3),
        "max_drawdown_pct":   round(max_dd, 2),
        "total_return_pct":   round(total_return, 2),
        "avg_monthly_ret_pct": round(avg_monthly_ret, 2),
        "worst_month_ret_pct": round(worst_month_ret, 2),
        "min_trades_month":   int(min_trades_month),
        "avg_trades_month":   round(avg_trades_month, 1),
        "months_profitable":  int(months_profitable),
        "total_months":       int(total_months),
        "max_daily_loss_pct": round(max_daily_loss, 2),
        "avg_win_usd":        round(avg_win, 2),
        "avg_loss_usd":       round(avg_loss, 2),
        "avg_rr":             round(avg_rr, 2),
        "final_balance":      round(equity_arr[-1], 2),
    }


def check_objectives(metrics: dict, obj: dict = OBJECTIVES) -> dict:
    """Verifica si los métricas cumplen los objetivos."""
    results = {}
    results["sharpe_ok"]     = metrics.get("sharpe_ratio", 0)       >= obj["min_sharpe"]
    results["drawdown_ok"]   = metrics.get("max_drawdown_pct", 99)   <= obj["max_drawdown"]
    results["daily_loss_ok"] = metrics.get("max_daily_loss_pct", 99) <= obj["max_daily_loss"]
    results["trades_ok"]     = metrics.get("min_trades_month", 0)    >= obj["min_trades_month"]
    results["monthly_ok"]    = metrics.get("worst_month_ret_pct", -99) >= obj["min_monthly_return"]
    results["all_pass"]      = all(results.values())
    return results


# ──────────────────────────────────────────────────────────────────
# 7. OPTIMIZADOR DE PARÁMETROS (Iteración 2)
# ──────────────────────────────────────────────────────────────────
def optimize_params(df_with_indicators: pd.DataFrame,
                    base_params: dict,
                    initial_balance: float = 100_000.0,
                    is_intraday: bool = True) -> dict:
    """
    Grid search sobre parámetros clave para maximizar Sharpe
    manteniendo todos los objetivos.
    """
    print("\n  Optimizando parámetros (Iteración 2)...")

    search_space = {
        "min_score":        [4, 5, 6],
        "sl_atr_mult":      [1.5, 1.8, 2.2],
        "cmf_threshold":    [0.03, 0.05, 0.08],
        "tp1_ratio":        [1.8, 2.0, 2.5],
        "tp2_ratio":        [3.5, 4.0, 5.0],
        "tp3_ratio":        [5.5, 6.5, 8.0],
        "obv_ma_period":    [14, 20, 30],
        "cmf_period":       [14, 20, 26],
        "vroc_period":      [10, 14, 20],
    }

    best_score = -np.inf
    best_params = base_params.copy()
    n_trials = 0
    max_trials = 40   # Limitar tiempo — indicadores ya calculados

    np.random.seed(42)

    # Random search eficiente (indicadores ya pre-calculados)
    keys = list(search_space.keys())
    for trial_num in range(max_trials):
        trial_params = base_params.copy()
        for k in keys:
            trial_params[k] = np.random.choice(search_space[k])

        # Validar que tp1 < tp2 < tp3
        if not (trial_params["tp1_ratio"] < trial_params["tp2_ratio"] < trial_params["tp3_ratio"]):
            continue

        try:
            bt = GoldBacktester(df_with_indicators, trial_params,
                                initial_balance, is_intraday)
            trades = bt.run(verbose=False)
            if trades.empty: continue

            m = compute_metrics(trades, bt.equity_curve, initial_balance)
            obj_check = check_objectives(m)

            # Score compuesto: prioriza Sharpe + penaliza fallos de objetivos
            composite = (
                m["sharpe_ratio"] * 1.0
                + m["avg_monthly_ret_pct"] * 0.3
                - m["max_drawdown_pct"] * 0.1
                - (0 if obj_check["all_pass"] else 5.0)
            )

            if composite > best_score:
                best_score  = composite
                best_params = trial_params.copy()
                n_trials += 1
                print(f"    Mejor trial {n_trials}/{trial_num+1}: Sharpe={m['sharpe_ratio']:.3f} "
                      f"DD={m['max_drawdown_pct']:.1f}% "
                      f"AllPass={obj_check['all_pass']}")
        except Exception:
            continue

    return best_params


# ──────────────────────────────────────────────────────────────────
# 8. RUNNER PRINCIPAL — 3 ITERACIONES
# ──────────────────────────────────────────────────────────────────
def run_backtest_iteration(df_raw: pd.DataFrame,
                           params: dict,
                           version: str,
                           tf_label: str,
                           is_intraday: bool = True,
                           initial_balance: float = 100_000.0) -> dict:
    """Ejecuta una iteración completa de backtesting."""
    print(f"\n  [{version}] TF={tf_label} — Calculando indicadores...")

    try:
        df = VolumeIndicators.add_all(df_raw.copy(), params)
        bt = GoldBacktester(df, params, initial_balance, is_intraday)
        trades = bt.run(verbose=True)

        if trades.empty:
            print(f"  [{version}] Sin trades generados — revisar sesión/score/datos")
            return {"version": version, "tf": tf_label, "total_trades": 0}, pd.DataFrame(), []

        metrics  = compute_metrics(trades, bt.equity_curve, initial_balance)
        obj_pass = check_objectives(metrics)

        result = {
            "version": version,
            "tf":      tf_label,
            **metrics,
            **{f"obj_{k}": v for k, v in obj_pass.items()},
            "params_min_score": params["min_score"],
            "params_sl_mult":   params["sl_atr_mult"],
            "params_cmf_thr":   params["cmf_threshold"],
        }

        print(f"  [{version}] TF={tf_label} | "
              f"Trades={metrics['total_trades']} | "
              f"WinR={metrics['win_rate_pct']:.1f}% | "
              f"Sharpe={metrics['sharpe_ratio']:.3f} | "
              f"MaxDD={metrics['max_drawdown_pct']:.1f}% | "
              f"TotalRet={metrics['total_return_pct']:.1f}% | "
              f"AllPass={obj_pass['all_pass']}")

        return result, trades, bt.equity_curve

    except Exception as e:
        print(f"  ERROR en {version} {tf_label}: {e}")
        return {"version": version, "tf": tf_label, "error": str(e)}, pd.DataFrame(), []


def print_summary_table(results: list[dict]):
    """Imprime tabla resumen de resultados."""
    print("\n" + "="*110)
    print("  RESUMEN COMPLETO — GOLD VOLUME FUSION ELITE")
    print("="*110)
    header = (f"{'Ver':>4} {'TF':>6} {'Trades':>7} {'WinR%':>7} "
              f"{'Sharpe':>8} {'MaxDD%':>8} {'TotRet%':>9} "
              f"{'AvgMon%':>8} {'WorMon%':>8} "
              f"{'MinTrd/M':>9} {'DlyLoss%':>9} {'PASS':>5}")
    print(header)
    print("-"*110)
    for r in results:
        if "error" in r or r.get("total_trades", 0) == 0:
            print(f"  {r.get('version','?'):>3} {r.get('tf','?'):>6}  ERROR/NO TRADES")
            continue
        passed = "YES" if r.get("obj_all_pass") else "NO "
        print(
            f"  {r['version']:>3} {r['tf']:>6} "
            f"{r.get('total_trades',0):>7} "
            f"{r.get('win_rate_pct',0):>7.1f} "
            f"{r.get('sharpe_ratio',0):>8.3f} "
            f"{r.get('max_drawdown_pct',0):>8.2f} "
            f"{r.get('total_return_pct',0):>9.1f} "
            f"{r.get('avg_monthly_ret_pct',0):>8.2f} "
            f"{r.get('worst_month_ret_pct',0):>8.2f} "
            f"{r.get('min_trades_month',0):>9} "
            f"{r.get('max_daily_loss_pct',0):>9.2f} "
            f"{passed:>5}"
        )
    print("="*110)


def main():
    """Función principal — ejecuta 3 iteraciones de backtesting."""
    print("\n" + "█"*70)
    print("  GOLD VOLUME FUSION ELITE — BACKTESTING ENGINE")
    print("  3 Iteraciones | XAUUSD | 10 años")
    print("  TFs: 15min, 30min, 1H, 2H, 3H, 4H, 1D")
    print("  Fuente #1: MT5 Data Server | #2: Parquet MT5 | #3: Dukascopy | #4: yfinance")
    print("█"*70 + "\n")

    os.makedirs("results", exist_ok=True)

    # ══════════════════════════════════════════════════════════════
    # PASO 1 — OBTENER DATOS (prioridad: MT5 Server > Parquet > Dukascopy > yfinance)
    # ══════════════════════════════════════════════════════════════
    print("PASO 1: Obteniendo datos XAUUSD 10 años...")

    timeframes = {}    # {"label": (df, is_intraday)}
    _mt5_client = None

    # ── FUENTE 1: MT5 Data Server (conexión directa a MetaTrader 5) ──
    if _HAS_MT5_CLIENT:
        _mt5_client = _get_mt5_client()

    if _mt5_client is not None:
        print("\n  ► Fuente: MT5 Data Server (conexión directa — todos los TFs en RAM)")
        try:
            mt5_data = _mt5_client.get_all_timeframes(
                symbol="XAUUSD",
                years=10,
                timeframes=["15min", "30min", "1h", "2h", "3h", "4h", "1d"],
                verbose=True,
            )
            # Mapear a nombres internos
            _TF_LABELS = {
                "15min": ("M15", True),
                "30min": ("M30", True),
                "1h":    ("1H",  True),
                "2h":    ("2H",  True),
                "3h":    ("3H",  True),
                "4h":    ("4H",  True),
                "1d":    ("1D",  False),
            }
            for tf_key, (label, is_intra) in _TF_LABELS.items():
                if tf_key in mt5_data and len(mt5_data[tf_key]) > 100:
                    timeframes[label] = (mt5_data[tf_key], is_intra)
        except Exception as e:
            print(f"  WARNING MT5 Server: {e}")
            _mt5_client = None

    # ── FUENTE 2: Parquet MT5 exportado con export_history_to_parquet.py ──
    if not timeframes:
        _MT5_PARQUET = Path("data/dukascopy/XAUUSD_15min_mt5.parquet")
        if _MT5_PARQUET.exists():
            print(f"\n  ► Fuente: Parquet MT5 ({_MT5_PARQUET})")
            try:
                df_m15 = pd.read_parquet(_MT5_PARQUET)
                print(f"    M15: {len(df_m15)} barras  "
                      f"{df_m15.index[0].date()} → {df_m15.index[-1].date()}")
                timeframes["M15"] = (df_m15, True)
                for label, rule in [("M30","30min"),("1H","1h"),("2H","2h"),
                                     ("3H","3h"),("4H","4h"),("1D","1d")]:
                    try:
                        timeframes[label] = (resample_data(df_m15, rule), label != "1D")
                        print(f"    {label}: {len(timeframes[label][0])} barras (remuestreado)")
                    except Exception as e:
                        print(f"    WARNING remuestreo {label}: {e}")
            except Exception as e:
                print(f"  WARNING leyendo parquet MT5: {e}")

    # ── FUENTE 3: Dukascopy CDN (bi5 en RAM → parquet) ────────────
    if not timeframes and _HAS_DUKASCOPY:
        print("\n  ► Fuente: Dukascopy CDN (descargando en RAM, sin archivos bi5...)")
        try:
            df_m15 = download_dukascopy_ohlcv(
                start="2016-01-01", end="2026-01-01",
                timeframe="15min", cache_dir="data/dukascopy",
            )
            timeframes["M15"] = (df_m15, True)
            for label, rule in [("M30","30min"),("1H","1h"),("2H","2h"),
                                 ("3H","3h"),("4H","4h"),("1D","1d")]:
                try:
                    timeframes[label] = (resample_data(df_m15, rule), label != "1D")
                except Exception:
                    pass
        except Exception as e:
            print(f"  WARNING Dukascopy: {e}")

    # ── FUENTE 4: yfinance (fallback — datos limitados) ────────────
    if not timeframes:
        print("\n  ► Fuente: yfinance (fallback — datos limitados)")
        df_daily = download_data("GC=F", "2016-01-01", "2026-01-01", "1d")
        timeframes["1D"] = (df_daily, False)
        try:
            df_1h = download_data("GC=F", "2022-01-01", "2026-01-01", "60m")
            timeframes["1H"] = (df_1h, True)
            for label, rule in [("2H","2h"),("3H","3h"),("4H","4h")]:
                try:
                    timeframes[label] = (resample_data(df_1h, rule), True)
                except Exception:
                    pass
        except Exception as e:
            print(f"  WARNING yfinance 1h: {e}")
    elif "1D" not in timeframes:
        # Siempre tener 1D con yfinance (10 años garantizados)
        try:
            df_daily = download_data("GC=F", "2016-01-01", "2026-01-01", "1d")
            timeframes["1D"] = (df_daily, False)
        except Exception:
            pass

    if not timeframes:
        raise RuntimeError("No se pudo obtener datos de ninguna fuente.")

    print(f"\n  Fuentes cargadas: {list(timeframes.keys())}")

    # Determinar TF primario
    for _prim in ["M15", "1H", "1D"]:
        if _prim in timeframes:
            primary_tf = _prim
            break

    print(f"  TF primario para optimización: {primary_tf}")

    all_results = []

    # ══════════════════════════════════════════════════════════════
    # ITERACIÓN 1 — Parámetros base
    # ══════════════════════════════════════════════════════════════
    print("\n" + "▓"*60)
    print("  ITERACIÓN 1 — Parámetros Base")
    print("▓"*60)

    params_v1 = PARAMS_V1.copy()

    iter1_results = []
    for tf_label, (df_tf, is_intra) in timeframes.items():
        r, trades, equity = run_backtest_iteration(
            df_tf, params_v1, "V1", tf_label, is_intra
        )
        if isinstance(r, dict):
            all_results.append(r)
            iter1_results.append(r)

    # ══════════════════════════════════════════════════════════════
    # ITERACIÓN 2 — Optimización de parámetros
    # ══════════════════════════════════════════════════════════════
    print("\n" + "▓"*60)
    print("  ITERACIÓN 2 — Optimización de Parámetros")
    print("▓"*60)

    # Optimizar sobre el TF primario (M15 si disponible)
    df_opt, is_intra_opt = timeframes[primary_tf]
    df_opt_with_ind = VolumeIndicators.add_all(df_opt.copy(), params_v1)
    params_v2 = optimize_params(df_opt_with_ind, params_v1, is_intraday=is_intra_opt)

    iter2_results = []
    for tf_label, (df_tf, is_intra) in timeframes.items():
        r, trades, equity = run_backtest_iteration(
            df_tf, params_v2, "V2", tf_label, is_intra
        )
        if isinstance(r, dict):
            all_results.append(r)
            iter2_results.append(r)

    # ══════════════════════════════════════════════════════════════
    # ITERACIÓN 3 — Refinamiento fino con PARAMS_V3
    # ══════════════════════════════════════════════════════════════
    print("\n" + "▓"*60)
    print("  ITERACIÓN 3 — Refinamiento Fino (PARAMS_V3 del EA)")
    print("▓"*60)

    params_v3 = PARAMS_V3.copy()
    print(f"\n  V3 base: min_score={params_v3['min_score']}, "
          f"obv_ma={params_v3['obv_ma_period']}, cmf_thr={params_v3['cmf_threshold']}, "
          f"filter_weekdays={params_v3['filter_weekdays']}")

    # Ajustes dinámicos basados en V2 del TF primario
    v2_primary = next((r for r in iter2_results if r.get("tf") == primary_tf), None)
    if v2_primary:
        sharpe_v2 = v2_primary.get("sharpe_ratio", 0)
        dd_v2     = v2_primary.get("max_drawdown_pct", 99)
        print(f"\n  Análisis V2 [{primary_tf}]: Sharpe={sharpe_v2:.3f} MaxDD={dd_v2:.1f}%")
        if dd_v2 > 7.0:
            print("  → MaxDD alto: reduciendo riesgo por trade")
            params_v3["risk_pct"] = max(0.25, params_v3["risk_pct"] * 0.85)
        if v2_primary.get("min_trades_month", 0) < OBJECTIVES["min_trades_month"]:
            print("  → Pocos trades/mes: V3 ya tiene filter_weekdays=False")

    iter3_results = []
    for tf_label, (df_tf, is_intra) in timeframes.items():
        r, trades, equity = run_backtest_iteration(
            df_tf, params_v3, "V3", tf_label, is_intra
        )
        if isinstance(r, dict):
            all_results.append(r)
            iter3_results.append(r)

    # ══════════════════════════════════════════════════════════════
    # RESUMEN FINAL
    # ══════════════════════════════════════════════════════════════
    print_summary_table(all_results)

    print("\n" + "="*70)
    print(f"  COMPARACIÓN DE ITERACIONES — TF: {primary_tf}")
    print("="*70)
    for version in ["V1", "V2", "V3"]:
        r = next((x for x in all_results
                  if x.get("version") == version and x.get("tf") == primary_tf), None)
        if r and "sharpe_ratio" in r:
            obj_pass = check_objectives(r)
            status = "✓ PASA OBJETIVOS" if obj_pass["all_pass"] else "✗ FALLA OBJETIVOS"
            print(f"\n  {version}: {status}")
            print(f"    Sharpe={r['sharpe_ratio']:.3f}  MaxDD={r['max_drawdown_pct']:.1f}%  "
                  f"TotalRet={r['total_return_pct']:.1f}%")
            print(f"    WinRate={r['win_rate_pct']:.1f}%  PF={r['profit_factor']:.2f}")
            print(f"    MinTrades/Mes={r['min_trades_month']}  "
                  f"WorstMon%={r['worst_month_ret_pct']:.1f}%  "
                  f"MaxDailyLoss={r['max_daily_loss_pct']:.2f}%")

    # ── GUARDAR RESULTADOS ─────────────────────────────────────────
    results_df = pd.DataFrame([r for r in all_results if "sharpe_ratio" in r])
    results_df.to_csv("results/backtest_volume_fusion_results.csv", index=False)

    best_params_out = {
        "version":      "V3_final",
        "strategy":     "Gold Volume Fusion Elite",
        "primary_tf":   primary_tf,
        "data_source":  "Dukascopy CDN" if _HAS_DUKASCOPY and df_m15 is not None else "yfinance fallback",
        "generated":    datetime.now().isoformat(),
        "params":       params_v3,
        "objectives_target": OBJECTIVES,
    }

    v3_primary = next((r for r in iter3_results if r.get("tf") == primary_tf), {})
    if "sharpe_ratio" in v3_primary:
        best_params_out["metrics_v3"] = {
            k: v for k, v in v3_primary.items() if k not in ["version", "tf"]
        }
        best_params_out["objectives_passed"] = check_objectives(v3_primary)

    with open("results/best_params_volume_fusion.json", "w") as f:
        json.dump(best_params_out, f, indent=2, default=str)

    print(f"\n  Resultados guardados en results/")
    print(f"  ├── backtest_volume_fusion_results.csv")
    print(f"  └── best_params_volume_fusion.json")

    return results_df, params_v3


if __name__ == "__main__":
    results_df, best_params = main()

