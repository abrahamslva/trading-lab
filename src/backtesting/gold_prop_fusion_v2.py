#!/usr/bin/env python3
"""
GoldPropFusion v2 — Estrategia Híbrida Mejorada XAUUSD
========================================================
Mejoras sobre v1:
  - Señal EMA-cross + RSI-50-cross (mayor win rate)
  - Asian Breakout RETEST confirmado (70-80% win rate documentado)
  - Filtro macro EMA(200): no shortear en bull market
  - SL más amplio: 2.0× ATR (evita "Gold Trap")
  - TP escalonado: TP1 a 1.5R (cierra 50%), TP2 a 4.0R (cierra 50%)

SEÑALES POR TIMEFRAME:
  15m/30m:  Asian Breakout RETEST (Londres 07-11 UTC)
            + RSI-50 en tendencia + EMA cross
  1h/2h/3h: EMA(20/50) cross + RSI-50-cross + OBV + CMF
  4h:       EMA cross + volumen (igual pero raro → calidad alta)
  1D:       EMA cross + OBV new high + CMF fuerte

GESTIÓN DE RIESGO:
  SL = 2.0 × ATR(14)        ← dinámico, más amplio
  TP1 = 1.5× riesgo (50%)  ← cierra mitad, SL mueve a BE
  TP2 = 4.0× riesgo (50%)  ← deja correr
  Riesgo/trade = 0.5% capital
  Pérdida diaria max = 1.5%

FILTRO MACRO:
  EMA(200): solo LONG cuando close > EMA(200) y EMA(200) sube
            solo SHORT cuando close < EMA(200) y EMA(200) baja
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
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.65,
        session_filter=True, london=(7, 11), ny=(13, 17),
        avoid_monday=True, avoid_friday=True,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=True,
        use_ema_cross=True, use_rsi_cross=True,
        macro_filter=True,
        warmup=210,
    ),
    '30min': dict(
        resample='30min',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.65,
        session_filter=True, london=(7, 11), ny=(13, 17),
        avoid_monday=True, avoid_friday=True,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=True,
        use_ema_cross=True, use_rsi_cross=True,
        macro_filter=True,
        warmup=210,
    ),
    '1h': dict(
        resample='1h',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.70,
        session_filter=True, london=(7, 12), ny=(13, 18),
        avoid_monday=False, avoid_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False,
        use_ema_cross=True, use_rsi_cross=True,
        macro_filter=True,
        warmup=210,
    ),
    '2h': dict(
        resample='2h',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.75,
        session_filter=True, london=(6, 18), ny=(6, 18),
        avoid_monday=False, avoid_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False,
        use_ema_cross=True, use_rsi_cross=True,
        macro_filter=True,
        warmup=210,
    ),
    '3h': dict(
        resample='3h',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.80,
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday=False, avoid_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=2,
        use_asian_breakout=False,
        use_ema_cross=True, use_rsi_cross=True,
        macro_filter=True,
        warmup=210,
    ),
    '4h': dict(
        resample='4h',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=4.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=0.85,
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday=False, avoid_friday=False,
        risk_pct=0.005, daily_loss_limit=0.015, max_trades_day=1,
        use_asian_breakout=False,
        use_ema_cross=True, use_rsi_cross=False,
        macro_filter=True,
        warmup=210,
    ),
    '1D': dict(
        resample='1D',
        sl_atr_mult=2.0, tp1_ratio=1.5, tp2_ratio=5.0,
        atr_period=14, ema_fast=20, ema_slow=50, ema_macro=200,
        cmf_period=20, obv_ema=20, mfi_period=14, rsi_period=14,
        adr_period=14, adr_max_pct=1.0,
        session_filter=False, london=(0, 24), ny=(0, 24),
        avoid_monday=False, avoid_friday=False,
        risk_pct=0.005, daily_loss_limit=0.020, max_trades_day=1,
        use_asian_breakout=False,
        use_ema_cross=True, use_rsi_cross=False,
        macro_filter=True,
        warmup=210,
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES
# ─────────────────────────────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()

def _rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d  = s.diff()
    up = d.clip(lower=0)
    dn = (-d).clip(lower=0)
    rs = up.ewm(span=n, adjust=False).mean() / dn.ewm(span=n, adjust=False).mean()
    return 100 - (100 / (1 + rs))

def _atr(df: pd.DataFrame, n: int) -> pd.Series:
    hl = df['high'] - df['low']
    hc = (df['high'] - df['close'].shift()).abs()
    lc = (df['low']  - df['close'].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=n, adjust=False).mean()

def _cmf(df: pd.DataFrame, n: int) -> pd.Series:
    denom  = (df['high'] - df['low']).replace(0, np.nan)
    mf_mul = ((df['close'] - df['low']) - (df['high'] - df['close'])) / denom
    mf_vol = mf_mul * df['volume']
    vol_sum = df['volume'].rolling(n).sum()
    return mf_vol.rolling(n).sum() / vol_sum.replace(0, np.nan)

def _obv(df: pd.DataFrame) -> pd.Series:
    return (np.sign(df['close'].diff()).fillna(0) * df['volume']).cumsum()

def _mfi(df: pd.DataFrame, n: int) -> pd.Series:
    tp   = (df['high'] + df['low'] + df['close']) / 3
    mf   = tp * df['volume']
    pos  = mf.where(tp > tp.shift(), 0.0)
    neg  = mf.where(tp < tp.shift(), 0.0)
    mfr  = pos.rolling(n).sum() / neg.rolling(n).sum().replace(0, np.nan)
    return 100 - (100 / (1 + mfr))

def add_indicators(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    df = df.copy()
    df['atr']        = _atr(df, cfg['atr_period'])
    df['ema_fast']   = _ema(df['close'], cfg['ema_fast'])
    df['ema_slow']   = _ema(df['close'], cfg['ema_slow'])
    df['ema_macro']  = _ema(df['close'], cfg['ema_macro'])
    df['cmf']        = _cmf(df, cfg['cmf_period'])
    raw_obv          = _obv(df)
    df['obv_ema']    = _ema(raw_obv, cfg['obv_ema'])
    df['mfi']        = _mfi(df, cfg['mfi_period'])
    df['rsi']        = _rsi(df['close'], cfg['rsi_period'])
    # ADR: rolling average of daily ranges
    daily_hl = df.groupby(df.index.date).apply(
        lambda g: g['high'].max() - g['low'].min()
    )
    daily_hl.index = pd.to_datetime(daily_hl.index)
    adr_rolling = daily_hl.rolling(cfg['adr_period']).mean()
    bar_dates   = pd.to_datetime(df.index.date)
    df['adr']   = bar_dates.map(adr_rolling.to_dict()).values
    # Intraday range consumed so far
    day_hi  = np.zeros(len(df))
    day_lo  = np.full(len(df), np.inf)
    prev_d  = None; ch = -np.inf; cl = np.inf
    for i, d in enumerate(df.index.date):
        if d != prev_d:
            ch = df['high'].iloc[i]; cl = df['low'].iloc[i]; prev_d = d
        else:
            ch = max(ch, df['high'].iloc[i]); cl = min(cl, df['low'].iloc[i])
        day_hi[i] = ch; day_lo[i] = cl
    df['day_range'] = day_hi - day_lo
    df['hour']      = df.index.hour
    df['weekday']   = df.index.dayofweek   # 0=Mon, 4=Fri
    return df

# ─────────────────────────────────────────────────────────────────────────────
# ASIAN RANGES
# ─────────────────────────────────────────────────────────────────────────────

def compute_asian_ranges(df_m15: pd.DataFrame) -> dict:
    """Asian session 22:00–07:00 UTC → maps to the trading day of London open."""
    df   = df_m15[['high', 'low']].copy()
    hrs  = df.index.hour
    nd   = df.index.normalize()
    if nd.tz is not None:
        nd = nd.tz_convert(None)
    nd_arr   = nd.values.copy()
    late     = hrs >= 22
    nd_arr[late] = (pd.DatetimeIndex(nd_arr[late]) + pd.Timedelta(days=1)).values
    df['sd'] = nd_arr
    asia     = df[(hrs >= 22) | (hrs < 7)].copy()
    out      = {}
    for sd, g in asia.groupby('sd'):
        if len(g) >= 4:
            out[pd.Timestamp(sd).date()] = {
                'hi':  g['high'].max(),
                'lo':  g['low'].min(),
                'rng': g['high'].max() - g['low'].min(),
            }
    return out

# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def generate_signals(df: pd.DataFrame, cfg: dict,
                     asian_ranges: dict | None = None) -> pd.Series:
    """
    Signal on bar i → entry on bar i+1 open.
    Returns +1 (long), -1 (short), 0 (flat).
    """
    n    = len(df)
    sig  = np.zeros(n, dtype=int)
    wu   = cfg['warmup']

    ef   = df['ema_fast'].values
    es   = df['ema_slow'].values
    em   = df['ema_macro'].values   # EMA(200) macro filter
    cl   = df['close'].values
    hi   = df['high'].values
    lo   = df['low'].values
    at   = df['atr'].values
    cm   = df['cmf'].values
    ob   = df['obv_ema'].values
    mf   = df['mfi'].values
    rs   = df['rsi'].values
    adr  = df['adr'].values
    drng = df['day_range'].values
    hrs  = df['hour'].values
    wds  = df['weekday'].values

    lon_s, lon_e = cfg['london']
    ny_s,  ny_e  = cfg['ny']
    dates        = [idx.date() for idx in df.index]

    # Pre-track: did a London-session breakout happen today (for Asian Retest)
    # We compute this by scanning forward — it's fine because we check PAST bars
    # to verify the breakout occurred in an EARLIER bar of the same day
    asian_breakout_long_day  = set()   # dates where bullish breakout happened
    asian_breakout_short_day = set()   # dates where bearish breakout happened

    if cfg.get('use_asian_breakout') and asian_ranges:
        for i in range(wu, n):
            d = dates[i]
            h = hrs[i]
            ar = asian_ranges.get(d)
            if ar and (lon_s <= h < lon_e):
                if cl[i] > ar['hi'] + 0.2 * at[i]:
                    asian_breakout_long_day.add((d, i))   # store (date, bar_idx)
                if cl[i] < ar['lo'] - 0.2 * at[i]:
                    asian_breakout_short_day.add((d, i))

    # Build fast lookup: for each date, the earliest breakout bar index
    ab_long_first  = {}   # date → first long-breakout bar idx
    ab_short_first = {}   # date → first short-breakout bar idx
    for d, idx in sorted(asian_breakout_long_day, key=lambda x: x[1]):
        if d not in ab_long_first:
            ab_long_first[d] = idx
    for d, idx in sorted(asian_breakout_short_day, key=lambda x: x[1]):
        if d not in ab_short_first:
            ab_short_first[d] = idx

    for i in range(wu, n - 1):
        if np.isnan(ef[i]) or np.isnan(es[i]) or np.isnan(em[i]):
            continue

        d = dates[i]
        h = hrs[i]
        w = wds[i]

        # ── Mon/Fri filter ───────────────────────────────────────────
        if cfg['avoid_monday'] and w == 0:
            continue
        if cfg['avoid_friday'] and w == 4:
            continue

        # ── Session filter ───────────────────────────────────────────
        if cfg['session_filter']:
            in_sess = (lon_s <= h < lon_e) or (ny_s <= h < ny_e)
            if not in_sess:
                continue

        # ── ADR filter ───────────────────────────────────────────────
        adr_v = adr[i]
        if not np.isnan(adr_v) and adr_v > 0:
            if drng[i] / adr_v > cfg['adr_max_pct']:
                continue

        # ── Macro EMA(200) filter ────────────────────────────────────
        macro_bull = cl[i] > em[i] and (em[i] > em[i - 3]) if cfg['macro_filter'] else True
        macro_bear = cl[i] < em[i] and (em[i] < em[i - 3]) if cfg['macro_filter'] else True

        # ── Volume conditions ────────────────────────────────────────
        cmf_v    = cm[i] if not np.isnan(cm[i]) else 0
        obv_up   = (ob[i] > ob[i - 5]) if (i >= 5 and not np.isnan(ob[i])) else False
        obv_dn   = (ob[i] < ob[i - 5]) if (i >= 5 and not np.isnan(ob[i])) else False
        mfi_v    = mf[i] if not np.isnan(mf[i]) else 50
        rsi_v    = rs[i] if not np.isnan(rs[i]) else 50
        rsi_p    = rs[i - 1] if (i >= 1 and not np.isnan(rs[i - 1])) else 50

        vol_bull = cmf_v > 0.02 and obv_up
        vol_bear = cmf_v < -0.02 and obv_dn

        mfi_bull = 35 < mfi_v < 75
        mfi_bear = 25 < mfi_v < 65

        long_ok  = macro_bull and vol_bull and mfi_bull
        short_ok = macro_bear and vol_bear and mfi_bear

        # ── SIGNAL 1: EMA Cross ──────────────────────────────────────
        if cfg['use_ema_cross']:
            ema_cross_long  = ef[i] > es[i] and ef[i - 1] <= es[i - 1]
            ema_cross_short = ef[i] < es[i] and ef[i - 1] >= es[i - 1]
            if ema_cross_long  and long_ok:
                sig[i] = max(sig[i], 1)
            if ema_cross_short and short_ok:
                sig[i] = min(sig[i], -1)

        # ── SIGNAL 2: RSI 50-line cross in trend ─────────────────────
        if cfg['use_rsi_cross']:
            uptrend  = ef[i] > es[i]
            dntrend  = ef[i] < es[i]
            rsi_cl   = rsi_v > 50 and rsi_p <= 50 and rsi_v < 65   # cross above 50
            rsi_cs   = rsi_v < 50 and rsi_p >= 50 and rsi_v > 35   # cross below 50
            if uptrend and rsi_cl and long_ok:
                sig[i] = max(sig[i], 1)
            if dntrend and rsi_cs and short_ok:
                sig[i] = min(sig[i], -1)

        # ── SIGNAL 3: Asian Breakout RETEST (15m/30m) ────────────────
        if cfg.get('use_asian_breakout') and asian_ranges and sig[i] == 0:
            ar = asian_ranges.get(d)
            if ar and (lon_s <= h < lon_e):
                atr_i = at[i]
                rng   = ar['rng']
                # Valid range: 0.3–3× ATR
                if not np.isnan(atr_i) and atr_i > 0 and 0.3 * atr_i < rng < 3.5 * atr_i:
                    retest_zone = 0.5 * atr_i

                    # LONG RETEST: breakout above happened earlier today
                    bf_long = ab_long_first.get(d)
                    if bf_long is not None and bf_long < i:
                        # Current bar: price pulled back to Asian High area
                        pulled_back = lo[i] <= ar['hi'] + retest_zone
                        bounced     = cl[i] > ar['hi']
                        if pulled_back and bounced and macro_bull and cmf_v > 0:
                            sig[i] = 1

                    # SHORT RETEST: breakout below happened earlier today
                    bf_short = ab_short_first.get(d)
                    if bf_short is not None and bf_short < i:
                        pulled_back = hi[i] >= ar['lo'] - retest_zone
                        bounced     = cl[i] < ar['lo']
                        if pulled_back and bounced and macro_bear and cmf_v < 0:
                            sig[i] = -1

    return pd.Series(sig, index=df.index, name='signal')

# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST (bar-by-bar)
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest(df: pd.DataFrame, cfg: dict,
                 initial: float = 100_000.0) -> tuple[list, np.ndarray]:
    """
    Bar-by-bar simulation.
    Entry: bar i+1 open when signal fires on bar i.
    Partial TP: close 50% at TP1, move SL to BE, close 50% at TP2.
    """
    n     = len(df)
    sig   = df['signal'].values
    op    = df['open'].values
    hi    = df['high'].values
    lo    = df['low'].values
    at    = df['atr'].values
    dates = [idx.date() for idx in df.index]

    capital  = initial
    eq       = initial
    pos      = 0       # 1=long, -1=short, 0=flat
    entry_p  = 0.0
    sl       = 0.0
    tp1      = 0.0
    tp2      = 0.0
    tp1_done = False
    risk_usd = 0.0     # risk on entry

    trades       = []
    equity_arr   = np.full(n, initial)
    day_pnl_map  = {}
    day_trd_map  = {}

    def gd(d):
        if d not in day_pnl_map:
            day_pnl_map[d] = 0.0; day_trd_map[d] = 0

    for i in range(1, n):
        d = dates[i]
        gd(d)

        # ── Manage open position ──────────────────────────────────────
        if pos != 0:
            bop = op[i]; bhi = hi[i]; blo = lo[i]

            if pos == 1:   # LONG ──────────────────────────────────────
                if bop <= sl:                          # gap through SL
                    pnl = -risk_usd
                    eq += pnl; capital += pnl
                    day_pnl_map[d] += pnl
                    trades.append(dict(dir='L', entry=entry_p, exit=sl,
                                       pnl_usd=pnl, exit_type='SL_GAP', date=d))
                    pos = 0; tp1_done = False

                elif blo <= sl and not tp1_done:       # SL hit intrabar
                    pnl = -risk_usd
                    eq += pnl; capital += pnl
                    day_pnl_map[d] += pnl
                    trades.append(dict(dir='L', entry=entry_p, exit=sl,
                                       pnl_usd=pnl, exit_type='SL', date=d))
                    pos = 0; tp1_done = False

                elif tp1_done and blo <= sl:           # BE stop hit after TP1
                    # Second half: closed at BE (entry_p), no P&L
                    trades.append(dict(dir='L', entry=entry_p, exit=entry_p,
                                       pnl_usd=0.0, exit_type='BE', date=d))
                    pos = 0; tp1_done = False

                elif not tp1_done and bhi >= tp1:      # TP1 hit
                    pnl1 = risk_usd * cfg['tp1_ratio'] * 0.5
                    eq += pnl1; capital += pnl1
                    day_pnl_map[d] += pnl1
                    sl       = entry_p                 # move SL to BE
                    tp1_done = True
                    if bhi >= tp2:                     # TP2 also hit same bar
                        pnl2 = risk_usd * cfg['tp2_ratio'] * 0.5
                        eq += pnl2; capital += pnl2
                        day_pnl_map[d] += pnl2
                        trades.append(dict(dir='L', entry=entry_p, exit=tp2,
                                           pnl_usd=pnl1 + pnl2,
                                           exit_type='TP2', date=d))
                        pos = 0; tp1_done = False

                elif tp1_done and bhi >= tp2:          # TP2 hit after TP1
                    pnl2 = risk_usd * cfg['tp2_ratio'] * 0.5
                    eq += pnl2; capital += pnl2
                    day_pnl_map[d] += pnl2
                    trades.append(dict(dir='L', entry=entry_p, exit=tp2,
                                       pnl_usd=pnl2, exit_type='TP2', date=d))
                    pos = 0; tp1_done = False

            else:  # SHORT ─────────────────────────────────────────────
                if bop >= sl:
                    pnl = -risk_usd
                    eq += pnl; capital += pnl
                    day_pnl_map[d] += pnl
                    trades.append(dict(dir='S', entry=entry_p, exit=sl,
                                       pnl_usd=pnl, exit_type='SL_GAP', date=d))
                    pos = 0; tp1_done = False

                elif bhi >= sl and not tp1_done:
                    pnl = -risk_usd
                    eq += pnl; capital += pnl
                    day_pnl_map[d] += pnl
                    trades.append(dict(dir='S', entry=entry_p, exit=sl,
                                       pnl_usd=pnl, exit_type='SL', date=d))
                    pos = 0; tp1_done = False

                elif tp1_done and bhi >= sl:
                    trades.append(dict(dir='S', entry=entry_p, exit=entry_p,
                                       pnl_usd=0.0, exit_type='BE', date=d))
                    pos = 0; tp1_done = False

                elif not tp1_done and blo <= tp1:
                    pnl1 = risk_usd * cfg['tp1_ratio'] * 0.5
                    eq += pnl1; capital += pnl1
                    day_pnl_map[d] += pnl1
                    sl       = entry_p
                    tp1_done = True
                    if blo <= tp2:
                        pnl2 = risk_usd * cfg['tp2_ratio'] * 0.5
                        eq += pnl2; capital += pnl2
                        day_pnl_map[d] += pnl2
                        trades.append(dict(dir='S', entry=entry_p, exit=tp2,
                                           pnl_usd=pnl1 + pnl2,
                                           exit_type='TP2', date=d))
                        pos = 0; tp1_done = False

                elif tp1_done and blo <= tp2:
                    pnl2 = risk_usd * cfg['tp2_ratio'] * 0.5
                    eq += pnl2; capital += pnl2
                    day_pnl_map[d] += pnl2
                    trades.append(dict(dir='S', entry=entry_p, exit=tp2,
                                       pnl_usd=pnl2, exit_type='TP2', date=d))
                    pos = 0; tp1_done = False

        # ── Check entry ───────────────────────────────────────────────
        if pos == 0:
            prev_sig = sig[i - 1]
            if prev_sig == 0:
                equity_arr[i] = eq
                continue

            # Daily loss limit
            if day_pnl_map.get(d, 0) / capital <= -cfg['daily_loss_limit']:
                equity_arr[i] = eq
                continue

            # Daily trade limit
            if day_trd_map.get(d, 0) >= cfg['max_trades_day']:
                equity_arr[i] = eq
                continue

            atr_i = at[i]
            if np.isnan(atr_i) or atr_i <= 0:
                equity_arr[i] = eq
                continue

            entry_p  = op[i]
            sl_dist  = cfg['sl_atr_mult'] * atr_i
            risk_usd = cfg['risk_pct'] * capital

            if prev_sig == 1:
                sl   = entry_p - sl_dist
                tp1  = entry_p + sl_dist * cfg['tp1_ratio']
                tp2  = entry_p + sl_dist * cfg['tp2_ratio']
                pos  = 1
            else:
                sl   = entry_p + sl_dist
                tp1  = entry_p - sl_dist * cfg['tp1_ratio']
                tp2  = entry_p - sl_dist * cfg['tp2_ratio']
                pos  = -1

            tp1_done = False
            day_trd_map[d] = day_trd_map.get(d, 0) + 1

        equity_arr[i] = eq

    # Close end-of-data
    if pos != 0:
        lc  = df['close'].iloc[-1]
        pct = (lc - entry_p) / entry_p * pos
        pnl = pct * risk_usd / (cfg['sl_atr_mult'] * at[-1] / entry_p) if entry_p else 0
        pnl = np.clip(pnl, -risk_usd * 2, risk_usd * 6)
        eq += pnl
        trades.append(dict(dir='L' if pos == 1 else 'S', entry=entry_p,
                            exit=lc, pnl_usd=pnl, exit_type='EOD', date=dates[-1]))
        equity_arr[-1] = eq

    return trades, equity_arr

# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

def compute_metrics(trades: list, equity_arr: np.ndarray,
                    initial: float = 100_000.0) -> dict:
    if not trades:
        return dict(monthly_return=0, total_return=0, max_drawdown=0,
                    sharpe=0, trades_month=0, win_rate=0, worst_day=0,
                    passed=False, n_trades=0)

    eq  = equity_arr[equity_arr > 0]
    if len(eq) == 0:
        eq = np.array([initial])

    total_ret   = (eq[-1] - initial) / initial * 100
    months      = 10.3 * 12                                # dataset span
    monthly_ret = (((eq[-1] / initial) ** (1 / months)) - 1) * 100
    trades_month = len(trades) / months

    run_max = np.maximum.accumulate(eq)
    dd      = (eq - run_max) / run_max * 100
    max_dd  = dd.min()

    # win rate: trades with positive pnl_usd (includes partial TP1 gains)
    # NOTE: BE trades have pnl_usd=0.0 for second half but TP1 was already in equity
    # True win: any trade that yielded TP1 (even if second half at BE)
    tp1_exits = sum(1 for t in trades
                    if t['exit_type'] in ('TP2', 'BE') or
                    (t['exit_type'] == 'TP2' and t.get('pnl_usd', 0) > 0))
    sl_exits  = sum(1 for t in trades if 'SL' in t['exit_type'])
    win_rate  = (tp1_exits / len(trades) * 100) if trades else 0

    day_pnl: dict = {}
    for t in trades:
        ds = str(t.get('date', 'x'))
        day_pnl[ds] = day_pnl.get(ds, 0) + t.get('pnl_usd', 0)
    worst_day_usd = min(day_pnl.values()) if day_pnl else 0
    worst_day_pct = worst_day_usd / initial * 100

    daily_rets = np.diff(eq) / eq[:-1]
    sharpe = 0.0
    if len(daily_rets) > 0 and daily_rets.std() > 0:
        sharpe = float(daily_rets.mean() / daily_rets.std() * np.sqrt(252))

    passed = (
        monthly_ret   >= 1.5
        and max_dd    >= -9.0
        and trades_month >= 7
        and worst_day_pct >= -5.0
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
        sl_exits=sl_exits,
        tp1_exits=tp1_exits,
    )

# ─────────────────────────────────────────────────────────────────────────────
# RESAMPLE
# ─────────────────────────────────────────────────────────────────────────────

def resample_ohlcv(df_m15: pd.DataFrame, rule: str) -> pd.DataFrame:
    if rule in ('15min', '15T', '15min'):
        return df_m15.copy()
    agg = {'open': 'first', 'high': 'max', 'low': 'min',
           'close': 'last', 'volume': 'sum'}
    return df_m15.resample(rule).agg(agg).dropna(subset=['close'])

# ─────────────────────────────────────────────────────────────────────────────
# PARAMETER GRID SEARCH
# ─────────────────────────────────────────────────────────────────────────────

OPT_GRID = {
    'sl_atr_mult': [1.5, 2.0, 2.5],
    'tp2_ratio':   [3.0, 4.0, 5.0],
    'ema_fast':    [10, 20],
    'ema_slow':    [30, 50],
}

def optimize(df_m15: pd.DataFrame, tf: str, cfg_base: dict,
             asian_ranges: dict | None,
             max_trials: int = 36) -> tuple[dict, dict]:
    from itertools import product
    keys   = list(OPT_GRID.keys())
    combos = list(product(*[OPT_GRID[k] for k in keys]))[:max_trials]
    rule   = cfg_base['resample']
    df_tf  = resample_ohlcv(df_m15, rule)

    best_score  = -999.0
    best_params = {}
    best_met    = {}

    for combo in combos:
        ov = dict(zip(keys, combo))
        if ov['ema_fast'] >= ov['ema_slow']:
            continue
        cfg = {**cfg_base, **ov}
        df_ind = add_indicators(df_tf, cfg)
        ar = asian_ranges if cfg.get('use_asian_breakout') else None
        df_ind['signal'] = generate_signals(df_ind, cfg, ar)
        trades, eq = run_backtest(df_ind, cfg)
        m = compute_metrics(trades, eq)
        score = (10.0 if m['passed'] else 0.0) + m['sharpe'] + 0.05 * m['monthly_return']
        if score > best_score:
            best_score = score; best_params = ov; best_met = m

    return best_params, best_met

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    data_path = Path('data/dukascopy/XAUUSD_15min_mt5.parquet')
    if not data_path.exists():
        raise FileNotFoundError(f"No encontrado: {data_path}")

    print(f"📂 Cargando {data_path}")
    df_m15 = pd.read_parquet(data_path)
    df_m15.index = pd.to_datetime(df_m15.index)
    df_m15.columns = [c.lower() for c in df_m15.columns]
    if 'volume' not in df_m15.columns:
        df_m15['volume'] = 1.0

    print(f"   {len(df_m15):,} barras  |  {df_m15.index[0].date()} → {df_m15.index[-1].date()}")
    print()

    print("📊 Pre-calculando rangos asiáticos (para 15m/30m)...")
    asian_ranges = compute_asian_ranges(df_m15)
    print(f"   {len(asian_ranges)} días con rango asiático válido\n")

    TIMEFRAMES = ['15min', '30min', '1h', '2h', '3h', '4h', '1D']
    results = []

    print("=" * 100)
    print(f"{'GOLDPROPFUSION v2 — XAUUSD 2016-2026 — BASE PARAMETERS':^100}")
    print("=" * 100)
    print(f"{'TF':<8} {'Mensual':>8} {'Total':>8} {'MaxDD':>8} {'Sharpe':>8} "
          f"{'Trd/Mes':>8} {'WinRate':>8} {'PeorDía':>9} {'SL':>6} {'TP1+':>6} {'✓?':>4}")
    print("-" * 100)

    for tf in TIMEFRAMES:
        cfg   = dict(TF_CONFIG[tf])
        df_tf = resample_ohlcv(df_m15, cfg['resample'])
        df_tf = add_indicators(df_tf, cfg)
        ar    = asian_ranges if cfg.get('use_asian_breakout') else None
        df_tf['signal'] = generate_signals(df_tf, cfg, ar)

        n_sig = (df_tf['signal'] != 0).sum()
        trades, eq = run_backtest(df_tf, cfg)
        m = compute_metrics(trades, eq)
        m['tf'] = tf
        results.append(m)

        passed = '✅' if m['passed'] else '✗'
        print(
            f"{tf:<8} {m['monthly_return']:>7.2f}%  {m['total_return']:>6.1f}%  "
            f"{m['max_drawdown']:>6.2f}%  {m['sharpe']:>7.2f}  "
            f"{m['trades_month']:>7.1f}  {m['win_rate']:>7.1f}%  "
            f"{m['worst_day']:>8.2f}%  {m.get('sl_exits',0):>5}  {m.get('tp1_exits',0):>5}  {passed}"
        )

    print("=" * 100)
    print()

    # ── Optimization for best TFs ──────────────────────────────────
    # Pick TFs with monthly_return >= 0.5% for optimization
    to_opt = sorted(results, key=lambda x: x['monthly_return'], reverse=True)[:4]
    if not to_opt:
        to_opt = results[:3]

    print("🔧 OPTIMIZACIÓN DE PARÁMETROS (grid search — top timeframes)")
    print("-" * 100)

    opt_results = []
    for r in to_opt:
        tf  = r['tf']
        cfg = dict(TF_CONFIG[tf])
        ar  = asian_ranges if cfg.get('use_asian_breakout') else None
        bov, bm = optimize(df_m15, tf, cfg, ar, max_trials=36)
        bm['tf'] = tf; bm['params'] = bov
        opt_results.append(bm)
        passed = '✅' if bm['passed'] else '✗'
        print(
            f"{tf:<8} {bm['monthly_return']:>7.2f}%  DD={bm['max_drawdown']:.2f}%  "
            f"Sharpe={bm['sharpe']:.2f}  Trd/mes={bm['trades_month']:.1f}  "
            f"WR={bm['win_rate']:.1f}%  {passed}"
        )
        if bov:
            print(f"         → {bov}")

    print("=" * 100)

    # ── Save ───────────────────────────────────────────────────────
    out_dir = Path('results')
    out_dir.mkdir(exist_ok=True)

    rows_base = []
    for r in results:
        rows_base.append({
            'Strategy': 'GoldPropFusion_v2',
            'Timeframe': r['tf'],
            'Monthly Return %': r['monthly_return'],
            'Total Return %': r['total_return'],
            'Max Drawdown %': r['max_drawdown'],
            'Sharpe Ratio': r['sharpe'],
            'Trades/Month': r['trades_month'],
            'Win Rate %': r['win_rate'],
            'Worst Day %': r['worst_day'],
            'SL exits': r.get('sl_exits', 0),
            'TP1+ exits': r.get('tp1_exits', 0),
            'Passed': '✅' if r['passed'] else '✗',
        })
    pd.DataFrame(rows_base).to_csv(out_dir / 'backtest_gpf_v2_base.csv', index=False)

    rows_opt = []
    for r in opt_results:
        rows_opt.append({
            'Strategy': 'GoldPropFusion_v2_OPT',
            'Timeframe': r['tf'],
            'Monthly Return %': r['monthly_return'],
            'Total Return %': r['total_return'],
            'Max Drawdown %': r['max_drawdown'],
            'Sharpe Ratio': r['sharpe'],
            'Trades/Month': r['trades_month'],
            'Win Rate %': r['win_rate'],
            'Worst Day %': r['worst_day'],
            'Best Params': str(r.get('params', {})),
            'Passed': '✅' if r['passed'] else '✗',
        })
    pd.DataFrame(rows_opt).to_csv(out_dir / 'backtest_gpf_v2_optimized.csv', index=False)

    print(f"\n💾 Guardado: results/backtest_gpf_v2_base.csv")
    print(f"💾 Guardado: results/backtest_gpf_v2_optimized.csv")

    passed_base = sum(1 for r in results if r['passed'])
    passed_opt  = sum(1 for r in opt_results if r['passed'])
    print(f"\n📊 RESULTADOS:")
    print(f"   Base:       {passed_base}/{len(results)} timeframes pasan objetivos")
    print(f"   Optimizado: {passed_opt}/{len(opt_results)} timeframes pasan objetivos")

    best_all = sorted(opt_results + results, key=lambda x: x['monthly_return'], reverse=True)[:5]
    print(f"\n   TOP 5 combinaciones:")
    for r in best_all:
        p = '✅' if r['passed'] else '✗'
        src = 'OPT' if 'params' in r else 'BASE'
        print(f"   {r['tf']:>6} [{src}]  {r['monthly_return']:>5.2f}%/mes  "
              f"DD={r['max_drawdown']:.2f}%  Sharpe={r['sharpe']:.2f}  "
              f"WR={r['win_rate']:.1f}%  {p}")


if __name__ == '__main__':
    main()
