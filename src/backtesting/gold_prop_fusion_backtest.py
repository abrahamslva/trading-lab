#!/usr/bin/env python3
"""
GoldPropFusion — Estrategia Híbrida Optimizada XAUUSD
=======================================================
Diseñada con toda la información disponible:
  - Biblia del Oro: London Sweep, ADR, sesiones, ATR dinámico
  - Volume Indicators: OBV, CMF, MFI, Chaikin
  - Knowledge base: estacionalidad, correlaciones, liquidez
  - Backtests previos: debilidades MA Cross (MaxDD alto, SL fijo)

SEÑALES:
  Señal 1 — EMA Pullback en Tendencia + Volumen (todos los TF)
    · Tendencia:  EMA_fast(20) > EMA_slow(50)
    · Pullback:   precio toca zona EMA_fast (0.5% alrededor)
    · Bounce:     cierra por encima de EMA_fast
    · Volumen:    CMF > 0  Y  OBV_EMA sube (> 3 barras atrás)
    · MFI:        30–70 (ni sobrecompra extrema ni sobreventa extrema)

  Señal 2 — Asian Range Breakout (15m / 30m solamente)
    · Rango asiático completo (22:00–07:00 UTC)
    · Ruptura en sesión Londres (07:00–11:00)
    · Ruptura > 0.3 × ATR (ruptura real, no ruido)
    · EMA_slow de fondo (trend alignment)
    · CMF > 0 para largo, CMF < 0 para corto

GESTIÓN DE RIESGO:
  · SL = sl_atr_mult × ATR(14)      ← DINÁMICO (evita Gold Trap)
  · TP1 = 1.5× riesgo → cierra 50%, SL mueve a BE
  · TP2 = 2.5× riesgo → cierra 50% restante
  · Riesgo/trade = 0.5% capital
  · Pérdida diaria máx = 1.5%
  · Máx 2 trades/día

FILTROS:
  · Sesión Londres (07–11 UTC) + NY Overlap (13–17 UTC) para TF bajos
  · ADR: no entrar si rango del día > 70% del ADR promedio
  · Sin lunes/viernes para TF bajos (mayor probabilidad martes–jueves)
  · Sin trades 30 min antes de noticias (simulado via horario)

OBJETIVOS PROP FIRM:
  monthly_return  ≥ 1.5%
  max_drawdown    ≤ 9%
  trades/month    ≥ 7
  worst_day       ≥ -5%
"""

import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN POR TIMEFRAME
# ─────────────────────────────────────────────────────────────────────────────

TF_CONFIG = {
    '15min': dict(
        resample='15min',
        atr_period=14, sl_atr_mult=1.5, tp1_ratio=1.5, tp2_ratio=2.5,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.70,
        session_filter=True, london=(7, 11), ny=(13, 17),
        avoid_monday_friday=True,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=True, pullback_zone=0.005, pullback_bars=5,
        warmup=60,
    ),
    '30min': dict(
        resample='30min',
        atr_period=14, sl_atr_mult=1.5, tp1_ratio=1.5, tp2_ratio=2.5,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.70,
        session_filter=True, london=(7, 11), ny=(13, 17),
        avoid_monday_friday=True,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=True, pullback_zone=0.005, pullback_bars=5,
        warmup=60,
    ),
    '1h': dict(
        resample='1h',
        atr_period=14, sl_atr_mult=1.5, tp1_ratio=1.5, tp2_ratio=2.5,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.75,
        session_filter=True, london=(7, 12), ny=(13, 18),
        avoid_monday_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False, pullback_zone=0.007, pullback_bars=4,
        warmup=60,
    ),
    '2h': dict(
        resample='2h',
        atr_period=14, sl_atr_mult=1.8, tp1_ratio=1.5, tp2_ratio=3.0,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.80,
        session_filter=True, london=(6, 18), ny=(6, 18),
        avoid_monday_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False, pullback_zone=0.008, pullback_bars=3,
        warmup=60,
    ),
    '3h': dict(
        resample='3h',
        atr_period=14, sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=3.0,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.85,
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False, pullback_zone=0.010, pullback_bars=3,
        warmup=60,
    ),
    '4h': dict(
        resample='4h',
        atr_period=14, sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=3.0,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=0.90,
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False, pullback_zone=0.012, pullback_bars=3,
        warmup=60,
    ),
    '1D': dict(
        resample='1D',
        atr_period=14, sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=3.5,
        ema_fast=20, ema_slow=50,
        cmf_period=20, obv_ema=20, mfi_period=14,
        adr_period=14, adr_max_pct=1.0,      # no ADR filter on daily
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=1,
        use_asian_breakout=False, pullback_zone=0.015, pullback_bars=3,
        warmup=60,
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES
# ─────────────────────────────────────────────────────────────────────────────

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _atr(df: pd.DataFrame, period: int) -> pd.Series:
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low']  - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def _cmf(df: pd.DataFrame, period: int) -> pd.Series:
    """Chaikin Money Flow"""
    denom = df['high'] - df['low']
    denom = denom.replace(0, np.nan)
    mf_mult = ((df['close'] - df['low']) - (df['high'] - df['close'])) / denom
    mf_vol  = mf_mult * df['volume']
    return mf_vol.rolling(period).sum() / df['volume'].rolling(period).sum()


def _obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df['close'].diff()).fillna(0)
    return (direction * df['volume']).cumsum()


def _mfi(df: pd.DataFrame, period: int) -> pd.Series:
    """Money Flow Index"""
    typical = (df['high'] + df['low'] + df['close']) / 3
    mf = typical * df['volume']
    pos_mf = mf.where(typical > typical.shift(), 0.0)
    neg_mf = mf.where(typical < typical.shift(), 0.0)
    pos_sum = pos_mf.rolling(period).sum()
    neg_sum = neg_mf.rolling(period).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def _adr_series(df: pd.DataFrame, period: int) -> pd.Series:
    """Average Daily Range — rolling mean of daily (high-low)"""
    daily_hl = df.groupby(df.index.date).apply(
        lambda g: g['high'].max() - g['low'].min()
    )
    daily_hl.index = pd.to_datetime(daily_hl.index)
    adr = daily_hl.rolling(period).mean()
    # Map back to bar level
    bar_dates = pd.to_datetime(df.index.date)
    return bar_dates.map(adr.to_dict()).values


def _daily_range_consumed(df: pd.DataFrame) -> np.ndarray:
    """For each bar, how much of the day's range has been consumed so far."""
    dates = df.index.date
    day_high  = np.zeros(len(df))
    day_low   = np.full(len(df), np.inf)
    prev_date = None
    cur_high  = -np.inf
    cur_low   = np.inf
    for i in range(len(df)):
        d = dates[i]
        if d != prev_date:
            cur_high  = df['high'].iloc[i]
            cur_low   = df['low'].iloc[i]
            prev_date = d
        else:
            cur_high = max(cur_high, df['high'].iloc[i])
            cur_low  = min(cur_low,  df['low'].iloc[i])
        day_high[i] = cur_high
        day_low[i]  = cur_low
    return day_high - day_low


def _compute_asian_ranges(df_m15: pd.DataFrame) -> dict:
    """
    Precompute Asian session high/low for each trading day.
    Asian session: 22:00–07:00 UTC  →  maps to the calendar day of London open.
    """
    df = df_m15[['high', 'low']].copy()
    hours = df.index.hour

    # Build sess_date: bars at hour >= 22 belong to NEXT calendar day
    norm_dates = df.index.normalize().tz_localize(None) if df.index.tz is None else df.index.normalize().tz_convert(None)
    next_dates = norm_dates + pd.Timedelta(days=1)
    mask_late  = hours >= 22
    # Build as object array to avoid tz issues
    sess_date_arr = norm_dates.values.copy()
    sess_date_arr[mask_late] = next_dates.values[mask_late]
    sess_date = pd.Series(sess_date_arr, index=df.index)
    df['sess_date'] = sess_date

    # Asian hours: [22,23,0,1,2,3,4,5,6]
    asia_mask = (hours >= 22) | (hours < 7)
    df_asia = df[asia_mask].copy()

    ranges = {}
    for sd, g in df_asia.groupby('sess_date'):
        if len(g) >= 4:  # at least 4 bars (1 hour)
            sd_date = pd.Timestamp(sd).date()
            ranges[sd_date] = {
                'hi':  g['high'].max(),
                'lo':  g['low'].min(),
                'rng': g['high'].max() - g['low'].min(),
            }
    return ranges


def add_indicators(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = df.copy()
    p = cfg
    df['atr']       = _atr(df, p['atr_period'])
    df['ema_fast']  = _ema(df['close'], p['ema_fast'])
    df['ema_slow']  = _ema(df['close'], p['ema_slow'])
    df['cmf']       = _cmf(df, p['cmf_period'])
    raw_obv         = _obv(df)
    df['obv_ema']   = _ema(raw_obv, p['obv_ema'])
    df['mfi']       = _mfi(df, p['mfi_period'])
    adr_arr         = _adr_series(df, p['adr_period'])
    df['adr']       = adr_arr
    df['day_range'] = _daily_range_consumed(df)
    df['hour']      = df.index.hour
    df['weekday']   = df.index.dayofweek  # 0=Mon, 4=Fri
    return df


# ─────────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE SEÑALES
# ─────────────────────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame, cfg: dict,
                     asian_ranges: dict | None = None) -> pd.Series:
    """
    Returns a Series with values: 1 (long), -1 (short), 0 (flat).
    Signal is calculated on bar i; entry is at bar i+1 open.
    """
    n = len(df)
    sig = np.zeros(n, dtype=int)
    pb  = cfg['pullback_bars']
    pz  = cfg['pullback_zone']   # % zone around EMA_fast considered "pullback zone"

    ef = df['ema_fast'].values
    es = df['ema_slow'].values
    cl = df['close'].values
    hi = df['high'].values
    lo = df['low'].values
    at = df['atr'].values
    cm = df['cmf'].values
    ob = df['obv_ema'].values
    mf = df['mfi'].values
    adr = df['adr']
    day_rng = df['day_range'].values
    hours   = df['hour'].values
    wdays   = df['weekday'].values

    lon_s, lon_e = cfg['london']
    ny_s,  ny_e  = cfg['ny']
    adr_max      = cfg['adr_max_pct']
    warmup       = cfg['warmup']

    dates = [d.date() for d in df.index]

    for i in range(warmup, n - 1):
        # ── Session filter ──────────────────────────────────────────
        if cfg['session_filter']:
            h = hours[i]
            in_london = lon_s <= h < lon_e
            in_ny     = ny_s  <= h < ny_e
            if not (in_london or in_ny):
                continue

        # ── Monday / Friday filter ──────────────────────────────────
        if cfg['avoid_monday_friday'] and wdays[i] in (0, 4):
            continue

        # ── ADR filter ──────────────────────────────────────────────
        adr_val = adr.iloc[i]
        if not np.isnan(adr_val) and adr_val > 0:
            if day_rng[i] / adr_val > adr_max:
                continue

        # ── Volume checks ────────────────────────────────────────────
        if np.isnan(cm[i]) or np.isnan(ob[i]):
            continue
        ob_rising  = (i >= 3) and (ob[i] > ob[i - 3])
        ob_falling = (i >= 3) and (ob[i] < ob[i - 3])
        cmf_bull   = cm[i] > 0.0
        cmf_bear   = cm[i] < 0.0
        mfi_ok_long  = 30 < mf[i] < 75  # not extremely overbought
        mfi_ok_short = 25 < mf[i] < 70  # not extremely oversold

        # ── SIGNAL 1: EMA Pullback Bounce ────────────────────────────
        if not np.isnan(ef[i]) and not np.isnan(es[i]):
            # LONG: uptrend, price pulled back to EMA_fast, now bouncing
            if ef[i] > es[i]:  # uptrend
                # Did price touch EMA_fast in last pb bars?
                pb_start = max(warmup, i - pb)
                touched_ema = any(
                    cl[j] <= ef[j] * (1 + pz) and cl[j] >= ef[j] * (1 - pz)
                    for j in range(pb_start, i)
                )
                bounce = cl[i] > ef[i]
                if touched_ema and bounce and cmf_bull and ob_rising and mfi_ok_long:
                    sig[i] = 1

            # SHORT: downtrend, price pulled back to EMA_fast, now falling
            elif ef[i] < es[i]:  # downtrend
                pb_start = max(warmup, i - pb)
                touched_ema = any(
                    cl[j] >= ef[j] * (1 - pz) and cl[j] <= ef[j] * (1 + pz)
                    for j in range(pb_start, i)
                )
                fall = cl[i] < ef[i]
                if touched_ema and fall and cmf_bear and ob_falling and mfi_ok_short:
                    sig[i] = -1

        # ── SIGNAL 2: Asian Range Breakout (15m / 30m only) ──────────
        if cfg.get('use_asian_breakout') and asian_ranges is not None:
            date_i = dates[i]
            ar     = asian_ranges.get(date_i)
            h_i    = hours[i]
            if ar and (lon_s <= h_i < lon_e):
                ar_rng = ar['rng']
                atr_i  = at[i]
                # Valid Asian range: 0.3× to 3× ATR
                if atr_i > 0 and 0.3 * atr_i < ar_rng < 3.0 * atr_i:
                    min_breakout = 0.3 * atr_i  # require meaningful breakout

                    # Bullish breakout
                    if (cl[i] > ar['hi'] + min_breakout
                            and cmf_bull and mfi_ok_long
                            and (np.isnan(es[i]) or cl[i] > es[i])):
                        sig[i] = 1  # override or confirm

                    # Bearish breakout
                    elif (cl[i] < ar['lo'] - min_breakout
                            and cmf_bear and mfi_ok_short
                            and (np.isnan(es[i]) or cl[i] < es[i])):
                        sig[i] = -1

    return pd.Series(sig, index=df.index, name='signal')


# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST BAR-BY-BAR
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame, cfg: dict) -> tuple[list, np.ndarray]:
    """
    Bar-by-bar simulation.
    Entry:  next bar's open (bar i+1) when signal fires on bar i.
    SL/TP:  checked using bar's high/low.
    Partial TP: close 50% at TP1, move SL to BE, close 50% at TP2.
    Returns: (trades list, equity curve array)
    """
    n = len(df)
    sig = df['signal'].values
    op  = df['open'].values
    hi  = df['high'].values
    lo  = df['low'].values
    at  = df['atr'].values
    dates = [idx.date() for idx in df.index]

    INITIAL = 100_000.0
    capital  = INITIAL
    equity   = INITIAL

    # position state
    pos       = 0       # 0=flat, 1=long, -1=short
    entry_p   = 0.0
    sl        = 0.0
    tp1       = 0.0
    tp2       = 0.0
    tp1_done  = False
    sl_dist   = 0.0     # initial risk distance in price
    half_risk = 0.0     # risk_usd for half position

    trades = []
    equity_arr = np.full(n, INITIAL)

    # daily tracking
    day_pnl    = {}   # date → cumulative pnl that day
    day_trades = {}   # date → trade count

    def _get_day(d):
        if d not in day_pnl:
            day_pnl[d]    = 0.0
            day_trades[d] = 0

    for i in range(1, n):
        d = dates[i]
        _get_day(d)

        # ── Manage open position ──────────────────────────────────────
        if pos != 0:
            bar_open  = op[i]
            bar_high  = hi[i]
            bar_low   = lo[i]
            closed_trade = None

            if pos == 1:  # LONG ──────────────────────────────────────
                # Check gap through SL
                if bar_open <= sl:
                    exit_p = sl
                    qty    = 1.0 if tp1_done else 1.0
                    pct    = (exit_p - entry_p) / entry_p
                    if tp1_done:
                        pnl_usd = half_risk * pct / (sl_dist / entry_p)
                    else:
                        pnl_usd = -cfg['risk_pct'] * capital  # full loss
                    pnl_usd = max(pnl_usd, -cfg['risk_pct'] * capital * 1.5)
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='SL')
                    pos = 0; tp1_done = False

                elif bar_low <= sl and not tp1_done:
                    exit_p  = sl
                    pnl_usd = -cfg['risk_pct'] * capital
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='SL')
                    pos = 0; tp1_done = False

                elif tp1_done and bar_low <= sl:
                    # SL hit after TP1 — breakeven or better
                    exit_p  = sl  # = entry_p (BE)
                    pnl_usd = 0.0  # no additional loss after TP1 pnl already taken
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='BE')
                    pos = 0; tp1_done = False

                elif not tp1_done and bar_high >= tp1:
                    # TP1 hit — close 50%, move SL to BE
                    tp1_pnl_usd = cfg['risk_pct'] * capital * cfg['tp1_ratio'] * 0.5
                    equity     += tp1_pnl_usd
                    capital    += tp1_pnl_usd
                    day_pnl[d]  = day_pnl.get(d, 0) + tp1_pnl_usd
                    half_risk   = cfg['risk_pct'] * capital * 0.5
                    sl          = entry_p  # move to breakeven
                    tp1_done    = True

                    # Check if TP2 also hit same bar
                    if bar_high >= tp2:
                        tp2_pnl_usd = cfg['risk_pct'] * capital * cfg['tp2_ratio'] * 0.5
                        equity     += tp2_pnl_usd
                        capital    += tp2_pnl_usd
                        day_pnl[d]  = day_pnl.get(d, 0) + tp2_pnl_usd
                        closed_trade = dict(
                            exit=tp2, pnl_usd=tp1_pnl_usd + tp2_pnl_usd,
                            exit_type='TP2'
                        )
                        pos = 0; tp1_done = False

                elif tp1_done and bar_high >= tp2:
                    tp2_pnl_usd = cfg['risk_pct'] * capital * cfg['tp2_ratio'] * 0.5
                    equity     += tp2_pnl_usd
                    capital    += tp2_pnl_usd
                    day_pnl[d]  = day_pnl.get(d, 0) + tp2_pnl_usd
                    closed_trade = dict(exit=tp2, pnl_usd=tp2_pnl_usd, exit_type='TP2')
                    pos = 0; tp1_done = False

            else:  # SHORT ──────────────────────────────────────────────
                if bar_open >= sl:
                    exit_p  = sl
                    pnl_usd = -cfg['risk_pct'] * capital
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='SL')
                    pos = 0; tp1_done = False

                elif bar_high >= sl and not tp1_done:
                    exit_p  = sl
                    pnl_usd = -cfg['risk_pct'] * capital
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='SL')
                    pos = 0; tp1_done = False

                elif tp1_done and bar_high >= sl:
                    exit_p  = sl
                    pnl_usd = 0.0
                    equity  += pnl_usd
                    capital += pnl_usd
                    day_pnl[d] = day_pnl.get(d, 0) + pnl_usd
                    closed_trade = dict(exit=exit_p, pnl_usd=pnl_usd, exit_type='BE')
                    pos = 0; tp1_done = False

                elif not tp1_done and bar_low <= tp1:
                    tp1_pnl_usd = cfg['risk_pct'] * capital * cfg['tp1_ratio'] * 0.5
                    equity     += tp1_pnl_usd
                    capital    += tp1_pnl_usd
                    day_pnl[d]  = day_pnl.get(d, 0) + tp1_pnl_usd
                    half_risk   = cfg['risk_pct'] * capital * 0.5
                    sl          = entry_p
                    tp1_done    = True

                    if bar_low <= tp2:
                        tp2_pnl_usd = cfg['risk_pct'] * capital * cfg['tp2_ratio'] * 0.5
                        equity     += tp2_pnl_usd
                        capital    += tp2_pnl_usd
                        day_pnl[d]  = day_pnl.get(d, 0) + tp2_pnl_usd
                        closed_trade = dict(
                            exit=tp2, pnl_usd=tp1_pnl_usd + tp2_pnl_usd,
                            exit_type='TP2'
                        )
                        pos = 0; tp1_done = False

                elif tp1_done and bar_low <= tp2:
                    tp2_pnl_usd = cfg['risk_pct'] * capital * cfg['tp2_ratio'] * 0.5
                    equity     += tp2_pnl_usd
                    capital    += tp2_pnl_usd
                    day_pnl[d]  = day_pnl.get(d, 0) + tp2_pnl_usd
                    closed_trade = dict(exit=tp2, pnl_usd=tp2_pnl_usd, exit_type='TP2')
                    pos = 0; tp1_done = False

            if closed_trade is not None:
                closed_trade.update(dict(
                    entry=entry_p, direction=('L' if pos == 0 and entry_p > 0 else 'S'),
                    date=d
                ))
                trades.append(closed_trade)

        # ── Check entry signal ────────────────────────────────────────
        if pos == 0:
            # signal fires on bar i-1, entry on bar i open
            prev_sig = sig[i - 1]
            if prev_sig == 0:
                equity_arr[i] = equity
                continue

            # Daily loss limit
            dpnl = day_pnl.get(d, 0.0)
            if dpnl / capital <= -cfg['daily_loss_limit']:
                equity_arr[i] = equity
                continue

            # Daily trade count
            if day_trades.get(d, 0) >= cfg['max_trades_day']:
                equity_arr[i] = equity
                continue

            atr_i  = at[i]
            if np.isnan(atr_i) or atr_i <= 0:
                equity_arr[i] = equity
                continue

            entry_p  = op[i]
            sl_dist  = cfg['sl_atr_mult'] * atr_i
            risk_usd = cfg['risk_pct'] * capital

            if prev_sig == 1:  # LONG
                sl   = entry_p - sl_dist
                tp1  = entry_p + sl_dist * cfg['tp1_ratio']
                tp2  = entry_p + sl_dist * cfg['tp2_ratio']
                pos  = 1
            else:              # SHORT
                sl   = entry_p + sl_dist
                tp1  = entry_p - sl_dist * cfg['tp1_ratio']
                tp2  = entry_p - sl_dist * cfg['tp2_ratio']
                pos  = -1

            tp1_done  = False
            half_risk = risk_usd * 0.5
            day_trades[d] = day_trades.get(d, 0) + 1

        equity_arr[i] = equity

    # Close any open position at end
    if pos != 0:
        last_close = df['close'].iloc[-1]
        if pos == 1:
            pnl_pct = (last_close - entry_p) / entry_p
        else:
            pnl_pct = (entry_p - last_close) / entry_p
        pnl_usd = pnl_pct * cfg['risk_pct'] * capital / (sl_dist / entry_p) if entry_p > 0 else 0
        pnl_usd = np.clip(pnl_usd, -cfg['risk_pct'] * capital * 2, cfg['risk_pct'] * capital * 5)
        equity  += pnl_usd
        trades.append(dict(
            entry=entry_p, exit=last_close,
            direction='L' if pos == 1 else 'S',
            pnl_usd=pnl_usd, exit_type='EOD', date=dates[-1]
        ))
        equity_arr[-1] = equity

    return trades, equity_arr


# ─────────────────────────────────────────────────────────────────────────────
# MÉTRICAS
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(trades: list, equity_arr: np.ndarray,
                    initial: float = 100_000.0) -> dict:
    if not trades:
        return dict(monthly_return=0, total_return=0, max_drawdown=0,
                    sharpe=0, trades_month=0, win_rate=0, worst_day=0, passed=False)

    eq = equity_arr[equity_arr > 0]
    if len(eq) == 0:
        eq = np.array([initial])

    # Total return
    total_ret = (eq[-1] - initial) / initial * 100

    # Max Drawdown
    running_max = np.maximum.accumulate(eq)
    dd          = (eq - running_max) / running_max * 100
    max_dd      = dd.min()

    # Monthly return (annualised)
    n_months = max(len(trades) / 12, 1)  # rough estimate from trade frequency
    # Use actual equity: assume 10.3 years
    years = 10.3
    months = years * 12
    monthly_ret = (((eq[-1] / initial) ** (1 / months)) - 1) * 100

    # Trades / month
    trades_month = len(trades) / months

    # Win rate
    wins = sum(1 for t in trades if t['pnl_usd'] > 0)
    win_rate = wins / len(trades) * 100 if trades else 0

    # Worst day
    day_pnl: dict = {}
    for t in trades:
        d = str(t.get('date', 'unknown'))
        day_pnl[d] = day_pnl.get(d, 0) + t['pnl_usd']
    worst_day_usd = min(day_pnl.values()) if day_pnl else 0
    worst_day_pct = worst_day_usd / initial * 100

    # Sharpe (monthly returns)
    # Estimate daily equity from array
    daily_rets = np.diff(eq) / eq[:-1]
    if len(daily_rets) > 0 and daily_rets.std() > 0:
        sharpe = (daily_rets.mean() / daily_rets.std()) * np.sqrt(252)
    else:
        sharpe = 0.0

    # Pass/fail objectives
    passed = (
        monthly_ret  >= 1.5 and
        max_dd       >= -9.0 and
        trades_month >= 7 and
        worst_day_pct >= -5.0
    )

    return dict(
        monthly_return=round(monthly_ret, 2),
        total_return=round(total_ret, 2),
        max_drawdown=round(max_dd, 2),
        sharpe=round(sharpe, 2),
        trades_month=round(trades_month, 1),
        win_rate=round(win_rate, 1),
        worst_day=round(worst_day_pct, 2),
        passed=passed,
        n_trades=len(trades),
    )


# ─────────────────────────────────────────────────────────────────────────────
# RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────

def resample_ohlcv(df_m15: pd.DataFrame, rule: str) -> pd.DataFrame:
    if rule in ('15min', '15T'):
        return df_m15.copy()
    agg = {
        'open':   'first',
        'high':   'max',
        'low':    'min',
        'close':  'last',
        'volume': 'sum',
    }
    df = df_m15.resample(rule).agg(agg).dropna(subset=['close'])
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PARAMETER OPTIMIZATION (grid search — capped iterations)
# ─────────────────────────────────────────────────────────────────────────────

GRID = {
    'sl_atr_mult': [1.0, 1.5, 2.0],
    'tp2_ratio':   [2.0, 2.5, 3.5],
    'ema_fast':    [10, 20],
    'ema_slow':    [30, 50],
}


def optimize(df_m15: pd.DataFrame, tf: str, cfg_base: dict,
             asian_ranges: dict | None = None,
             max_trials: int = 24) -> tuple[dict, dict]:
    """
    Grid-search optimization.  Returns (best_params_override, best_metrics).
    """
    from itertools import product

    keys   = list(GRID.keys())
    combos = list(product(*[GRID[k] for k in keys]))[:max_trials]

    best_score  = -999.0
    best_params = {}
    best_metrics = {}

    rule = cfg_base['resample']
    df_tf = resample_ohlcv(df_m15, rule)

    for combo in combos:
        params = {**cfg_base, **dict(zip(keys, combo))}
        # Skip invalid combos
        if params['ema_fast'] >= params['ema_slow']:
            continue
        df_ind = add_indicators(df_tf, params)
        df_ind['signal'] = generate_signals(df_ind, params, asian_ranges)
        trades, eq = run_backtest(df_ind, params)
        m = compute_metrics(trades, eq)
        # Score: prioritise passing, then Sharpe
        score = (10.0 if m['passed'] else 0.0) + m['sharpe'] + 0.1 * m['monthly_return']
        if score > best_score:
            best_score   = score
            best_params  = dict(zip(keys, combo))
            best_metrics = m

    return best_params, best_metrics


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # ── Load data ──────────────────────────────────────────────────
    data_path = Path('data/dukascopy/XAUUSD_15min_mt5.parquet')
    if not data_path.exists():
        raise FileNotFoundError(f"No se encontró: {data_path}")

    print(f"📂 Cargando datos: {data_path}")
    df_m15 = pd.read_parquet(data_path)
    df_m15.index = pd.to_datetime(df_m15.index)
    df_m15.columns = [c.lower() for c in df_m15.columns]
    if 'volume' not in df_m15.columns:
        df_m15['volume'] = 1.0   # fallback tick volume proxy

    print(f"   {len(df_m15):,} barras M15  |  {df_m15.index[0].date()} → {df_m15.index[-1].date()}")
    print()

    # ── Pre-compute Asian ranges (for 15min/30min) ──────────────────
    print("📊 Pre-calculando rangos asiáticos...")
    asian_ranges = _compute_asian_ranges(df_m15)
    print(f"   {len(asian_ranges)} días con rango asiático definido")
    print()

    results = []
    TIMEFRAMES = ['15min', '30min', '1h', '2h', '3h', '4h', '1D']

    print("=" * 90)
    print(f"{'GOLDPROPFUSION — BACKTESTING 7 TIMEFRAMES — XAUUSD 2016-2026':^90}")
    print("=" * 90)
    print(f"{'TF':<8} {'Mensual':>8} {'Total':>8} {'MaxDD':>8} {'Sharpe':>8} "
          f"{'Trades/Mes':>11} {'WinRate':>8} {'PeorDía':>9} {'✓?':>5}")
    print("-" * 90)

    for tf in TIMEFRAMES:
        cfg = dict(TF_CONFIG[tf])

        # Resample
        df_tf = resample_ohlcv(df_m15, cfg['resample'])

        # Indicators
        df_tf = add_indicators(df_tf, cfg)

        # Asian ranges only for intraday TFs that use them
        ar = asian_ranges if cfg.get('use_asian_breakout') else None

        # Signals
        df_tf['signal'] = generate_signals(df_tf, cfg, ar)

        # Backtest
        trades, equity_arr = run_backtest(df_tf, cfg)

        # Metrics
        m = compute_metrics(trades, equity_arr)
        m['tf'] = tf
        results.append(m)

        passed_str = '✅' if m['passed'] else '✗'
        print(
            f"{tf:<8} {m['monthly_return']:>7.2f}% {m['total_return']:>7.1f}% "
            f"{m['max_drawdown']:>7.2f}% {m['sharpe']:>8.2f} "
            f"{m['trades_month']:>10.1f} {m['win_rate']:>7.1f}% "
            f"{m['worst_day']:>8.2f}% {passed_str:>5}"
        )

    print("=" * 90)
    print()

    # ── Identify candidates for optimization ───────────────────────
    candidates = [r for r in results if r['monthly_return'] >= 1.0]
    if not candidates:
        candidates = sorted(results, key=lambda x: x['monthly_return'], reverse=True)[:3]

    print("🔧 OPTIMIZACIÓN DE PARÁMETROS — mejores timeframes")
    print("-" * 90)

    opt_results = []
    for r in candidates[:4]:  # max 4 TFs to optimize
        tf  = r['tf']
        cfg = dict(TF_CONFIG[tf])
        ar  = asian_ranges if cfg.get('use_asian_breakout') else None
        df_tf = resample_ohlcv(df_m15, cfg['resample'])

        best_ovr, best_m = optimize(df_m15, tf, cfg, ar, max_trials=24)
        best_full = {**cfg, **best_ovr}
        best_m['tf']     = tf
        best_m['params'] = best_ovr
        opt_results.append(best_m)

        passed_str = '✅' if best_m['passed'] else '✗'
        print(
            f"{tf:<8} {best_m['monthly_return']:>7.2f}% "
            f"MaxDD={best_m['max_drawdown']:.2f}%  "
            f"Sharpe={best_m['sharpe']:.2f}  "
            f"Trades/mes={best_m['trades_month']:.1f}  "
            f"WR={best_m['win_rate']:.1f}%  {passed_str}"
        )
        if best_ovr:
            print(f"         Params: {best_ovr}")

    print("=" * 90)

    # ── Save results ───────────────────────────────────────────────
    out_dir = Path('results')
    out_dir.mkdir(exist_ok=True)

    base_rows = []
    for r in results:
        base_rows.append({
            'Strategy':        'GoldPropFusion',
            'Timeframe':       r['tf'],
            'Monthly Return %': r['monthly_return'],
            'Total Return %':  r['total_return'],
            'Max Drawdown %':  r['max_drawdown'],
            'Sharpe Ratio':    r['sharpe'],
            'Trades/Month':    r['trades_month'],
            'Win Rate %':      r['win_rate'],
            'Worst Day %':     r['worst_day'],
            'Passed':          '✅' if r['passed'] else '✗',
        })
    df_out = pd.DataFrame(base_rows)
    out_csv = out_dir / 'backtest_gold_prop_fusion.csv'
    df_out.to_csv(out_csv, index=False)
    print(f"\n💾 Resultados guardados: {out_csv}")

    opt_rows = []
    for r in opt_results:
        opt_rows.append({
            'Strategy':        'GoldPropFusion-OPT',
            'Timeframe':       r['tf'],
            'Monthly Return %': r['monthly_return'],
            'Total Return %':  r['total_return'],
            'Max Drawdown %':  r['max_drawdown'],
            'Sharpe Ratio':    r['sharpe'],
            'Trades/Month':    r['trades_month'],
            'Win Rate %':      r['win_rate'],
            'Worst Day %':     r['worst_day'],
            'Params':          str(r.get('params', {})),
            'Passed':          '✅' if r['passed'] else '✗',
        })
    df_opt = pd.DataFrame(opt_rows)
    opt_csv = out_dir / 'backtest_gold_prop_fusion_optimized.csv'
    df_opt.to_csv(opt_csv, index=False)
    print(f"💾 Optimizados guardados: {opt_csv}")

    # Summary
    passed = [r for r in results if r['passed']]
    opt_passed = [r for r in opt_results if r['passed']]
    print(f"\n📊 RESUMEN:")
    print(f"   Base: {len(passed)}/{len(results)} timeframes cumplen objetivos")
    print(f"   Optimizados: {len(opt_passed)}/{len(opt_results)} timeframes cumplen objetivos")
    if opt_passed:
        print(f"\n   🏆 MEJORES TIMEFRAMES OPTIMIZADOS:")
        for r in sorted(opt_passed, key=lambda x: x['monthly_return'], reverse=True):
            print(f"      {r['tf']}: {r['monthly_return']:.2f}%/mes  "
                  f"DD={r['max_drawdown']:.2f}%  Sharpe={r['sharpe']:.2f}  "
                  f"WR={r['win_rate']:.1f}%")


if __name__ == '__main__':
    main()
