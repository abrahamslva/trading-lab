//+------------------------------------------------------------------+
//|  EA_XAUUSD_GoldVolumeFusionElite_v4_M15.mq5                     |
//|  GOLD VOLUME FUSION ELITE — Strategy v4.0 M15-Optimized         |
//|                                                                  |
//|  CAMBIOS vs v3_FINAL:                                           |
//|   - DailyLossLimit: 1.5% → 5.0% (objetivo actualizado)         |
//|   - MinScoreToEnter: 6 → 5 (más señales en M15)                |
//|   - OBV_MA_Period: 30 → 20 (V1 original — mejor Sharpe)        |
//|   - CMF_Threshold: 0.08 → 0.05 (más señales confirmadas)       |
//|   - MaxTradesPerDay: 2 → 3 | MaxTradesPerWeek: 6 → 12          |
//|   - Ventana sesión extendida: London 07-12, Overlap 12-18 UTC   |
//|   - TP1/TP2/TP3: 2.5/3.5/8.0 → 2.0/4.0/6.5 (V1 optimal)      |
//|   - ADR_MaxUsed: 0.65 → 0.70 (ligeramente más permisivo)       |
//|   - WeeklyLossLimit: 3.0% → 9.0% (alineado con DD máximo)      |
//|                                                                  |
//|  Resultados backtest V1_2H (2.5 años yfinance):                 |
//|   Sharpe=1.53 | MaxDD=2.0% | WinRate=48.3% | PF=2.62 | RR=2.81 |
//|  Proyección con M15 Dukascopy 10yr:                             |
//|   Trades/mes≥7 | Ret≥1.5%/m | DD≤9% | DailyLoss≤5%            |
//+------------------------------------------------------------------+
#property copyright "Gold Volume Fusion Elite"
#property version   "4.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Math\Stat\Math.mqh>

CTrade        trade;
CPositionInfo posInfo;

//=== GESTIÓN DE RIESGO ===
input group "=== GESTIÓN DE RIESGO ==="
input double  RiskPercent       = 0.5;    // Riesgo por trade (%)
input double  DailyLossLimit    = 5.0;    // Límite pérdida diaria (%) [V4: 1.5→5.0]
input double  WeeklyLossLimit   = 9.0;    // Límite pérdida semanal (%) [V4: 3.0→9.0]
input int     MaxTradesPerDay   = 3;      // Máx trades por día [V4: 2→3]
input int     MaxTradesPerWeek  = 12;     // Máx trades por semana [V4: 6→12]

//=== SESIONES UTC ===
input group "=== SESIONES (UTC) ==="
input int     AsiaStartHour     = 22;     // Asia inicio (hora UTC)
input int     AsiaEndHour       = 8;      // Asia fin (hora UTC)
input int     LondonOpenHour    = 7;      // Londres apertura [V4: 8→7]
input int     LondonCloseHour   = 12;     // Londres cierre ventana [V4: 11→12]
input int     OverlapStartHour  = 12;     // Overlap inicio [V4: 13→12]
input int     OverlapEndHour    = 18;     // Overlap fin [V4: 17→18]
input bool    FilterWeekdays    = false;  // Solo Mar-Jue (desactivado = más trades)
input bool    FilterMonday      = false;  // Evitar lunes [V4: true→false]
input bool    FilterFriday      = true;   // Evitar viernes después de 14:00 UTC

//=== OBV ===
input group "=== OBV (On-Balance Volume) ==="
input int     OBV_MA_Period     = 20;     // MA del OBV [V4: 30→20, mejor Sharpe]

//=== VWAP ===
input group "=== VWAP ==="
input bool    UseVWAP           = true;   // Activar filtro VWAP
input int     VWAP_Period       = 0;      // 0 = reset diario (22:00 UTC)

//=== MFI ===
input group "=== MFI (Money Flow Index) ==="
input int     MFI_Period        = 14;     // Período MFI
input double  MFI_OversoldLevel = 25.0;  // Sobreventa [V4: 30→25, más selectivo]
input double  MFI_OverboughtLevel = 75.0;// Sobrecompra [V4: 70→75]
input double  MFI_NeutralLow    = 40.0;  // Zona neutral bajo
input double  MFI_NeutralHigh   = 65.0;  // Zona neutral alto

//=== CMF ===
input group "=== CMF (Chaikin Money Flow) ==="
input int     CMF_Period        = 20;     // Período CMF
input double  CMF_Threshold     = 0.05;  // Umbral CMF [V4: 0.08→0.05, más señales]

//=== VOLUME PROFILE ===
input group "=== VOLUME PROFILE ==="
input int     VP_Period         = 100;   // Barras para Volume Profile
input int     VP_ZoneCount      = 20;    // Zonas del perfil
input double  VP_POC_Buffer     = 0.003; // Buffer cerca del POC (0.3%)

//=== CHAIKIN OSCILLATOR ===
input group "=== CHAIKIN OSCILLATOR ==="
input int     ChaikinFast       = 3;     // EMA rápida A/D
input int     ChaikinSlow       = 10;    // EMA lenta A/D

//=== VPT ===
input group "=== VPT (Volume Price Trend) ==="
input int     VPT_MA_Period     = 14;    // MA del VPT

//=== VROC ===
input group "=== VROC (Volume Rate of Change) ==="
input int     VROC_Period       = 14;    // Período VROC

//=== PVI/NVI ===
input group "=== PVI / NVI ==="
input int     PVI_MA_Period     = 255;   // MA del PVI
input int     NVI_MA_Period     = 255;   // MA del NVI

//=== STOPS Y TAKE PROFITS ===
input group "=== STOPS Y TAKE PROFITS ==="
input int     ATR_Period        = 14;    // Período ATR
input double  SL_ATR_Mult       = 1.8;  // Multiplicador ATR para SL (óptimo V1)
input double  MinSL_Pips        = 200;  // SL mínimo en pips (2.00 USD XAUUSD)
input double  TP1_Ratio         = 2.0;  // TP1 ratio RR [V4: 2.5→2.0 V1 optimal]
input double  TP2_Ratio         = 4.0;  // TP2 ratio RR [V4: 3.5→4.0 V1 optimal]
input double  TP3_Ratio         = 6.5;  // TP3 ratio RR [V4: 8.0→6.5 V1 optimal]
input double  TP1_ClosePercent  = 40.0; // % cierre en TP1
input double  TP2_ClosePercent  = 35.0; // % cierre en TP2
// TP3 = restante 25%

//=== FILTROS ADR ===
input group "=== FILTRO ADR ==="
input int     ADR_Period        = 14;    // Período ADR (días)
input double  ADR_MaxUsed       = 0.70; // No entrar si ADR > 70% usado [V4: 0.65→0.70]
input double  ADR_MinRequired   = 0.15; // Rango asiático mínimo como % ADR

//=== SCORING ===
input group "=== SISTEMA DE SCORING ==="
input int     MinScoreToEnter   = 5;    // Score mínimo entrada [V4: 6→5, +frecuencia]
input int     HighConfScore     = 8;    // Score alta confianza (riesgo normal)
input bool    UseLondonSweepBonus = true;// Bonus +2 por London Sweep confirmado

//=== ASIAN BREAKOUT BOOST ===
input group "=== ASIAN BREAKOUT (Estrategia #1 Biblia) ==="
input bool    UseAsianBreakoutMode = true; // Sumar +1 si precio rompe rango asiático
input double  AsianBreakoutBuffer  = 0.0;  // Buffer adicional (USD) para confirmación

//=== MAGIC & SLIPPAGE ===
input group "=== CONFIGURACIÓN MT5 ==="
input long    MagicNumber       = 202604; // Magic v4
input int     MaxSlippage       = 30;    // Slippage máximo (puntos)

//+------------------------------------------------------------------+
//| Estructuras                                                       |
//+------------------------------------------------------------------+
struct VolumeIndicators
{
   double obv;
   double obv_ma;
   double vwap;
   double mfi;
   double ad;
   double ad_ema_fast;
   double ad_ema_slow;
   double chaikin_osc;
   double cmf;
   double vpt;
   double vpt_ma;
   double vroc;
   double pvi;
   double pvi_ma;
   double nvi;
   double nvi_ma;
   double vp_poc;
   double vp_vah;
   double vp_val;
   int    vp_zone;
};

struct AsianSession
{
   double high;
   double low;
   double range;
   bool   valid;
   bool   sweptHigh;
   bool   sweptLow;
   bool   breakoutUp;    // V4: precio rompió hacia arriba
   bool   breakoutDown;  // V4: precio rompió hacia abajo
   datetime startTime;
};

//+------------------------------------------------------------------+
//| Variables globales                                                |
//+------------------------------------------------------------------+
VolumeIndicators    g_vi;
AsianSession        g_asian;

double g_dailyStartBalance;
double g_weeklyStartBalance;
int    g_dailyTrades;
int    g_weeklyTrades;
datetime g_lastDayReset;
datetime g_lastWeekReset;
datetime g_lastBarTime;

#define MAX_BARS 500
double buf_obv[MAX_BARS];
double buf_ad[MAX_BARS];
double buf_vpt[MAX_BARS];
double buf_pvi[MAX_BARS];
double buf_nvi[MAX_BARS];

int    h_ATR;
int    h_EMA20;
int    h_EMA50;
int    h_EMA200;

//+------------------------------------------------------------------+
//| OnInit                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(MaxSlippage);
   trade.SetTypeFilling(ORDER_FILLING_FOK);

   h_ATR   = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   h_EMA20 = iMA(_Symbol, PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);
   h_EMA50 = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_EMA200= iMA(_Symbol, PERIOD_CURRENT, 200, 0, MODE_EMA, PRICE_CLOSE);

   if(h_ATR == INVALID_HANDLE || h_EMA20 == INVALID_HANDLE ||
      h_EMA50 == INVALID_HANDLE || h_EMA200 == INVALID_HANDLE)
   {
      Print("ERROR: No se pudieron crear handles de indicadores");
      return INIT_FAILED;
   }

   g_dailyStartBalance  = AccountInfoDouble(ACCOUNT_BALANCE);
   g_weeklyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   g_dailyTrades  = 0;
   g_weeklyTrades = 0;
   g_lastDayReset  = TimeCurrent();
   g_lastWeekReset = TimeCurrent();
   g_lastBarTime   = 0;

   ArrayInitialize(buf_obv, 0);
   ArrayInitialize(buf_ad, 0);
   ArrayInitialize(buf_vpt, 0);
   ArrayInitialize(buf_pvi, 1000);
   ArrayInitialize(buf_nvi, 1000);

   PrintFormat("EA GVFE v4_M15 iniciado | %s | TF=%s | Magic=%d | "
               "Score≥%d | DailyLoss≤%.1f%% | ADR≤%.0f%%",
               _Symbol, EnumToString(Period()), MagicNumber,
               MinScoreToEnter, DailyLossLimit, ADR_MaxUsed * 100);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(h_ATR);
   IndicatorRelease(h_EMA20);
   IndicatorRelease(h_EMA50);
   IndicatorRelease(h_EMA200);
}

//+------------------------------------------------------------------+
//| OnTick                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == g_lastBarTime) return;
   g_lastBarTime = currentBarTime;

   ResetDailyCounters();
   ResetWeeklyCounters();
   ManageOpenPositions();

   if(!CheckRiskLimits()) return;
   if(!IsValidSession())  return;

   CalculateAllVolumeIndicators();
   UpdateAsianRange();

   int score = CalculateGVFS();

   if(CountMagicPositions() < MaxTradesPerDay)
   {
      if(score >= MinScoreToEnter)
         ExecuteLongEntry(score);
      else if(score <= -MinScoreToEnter)
         ExecuteShortEntry(score);
   }
}

//+------------------------------------------------------------------+
//| CalculateAllVolumeIndicators                                      |
//+------------------------------------------------------------------+
void CalculateAllVolumeIndicators()
{
   int bars = MathMin(MAX_BARS, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < 50) return;

   double high[], low[], close[];
   long   volume[];
   ArraySetAsSeries(high,   true);
   ArraySetAsSeries(low,    true);
   ArraySetAsSeries(close,  true);
   ArraySetAsSeries(volume, true);

   CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, bars, volume);

   CalculateOBV(close, volume, bars);
   CalculateAD(high, low, close, volume, bars);
   CalculateVWAP(high, low, close, volume, bars);
   g_vi.mfi        = CalculateMFI(high, low, close, volume, MFI_Period);
   g_vi.cmf        = CalculateCMF(high, low, close, volume, CMF_Period);
   g_vi.chaikin_osc= CalculateChaikinOscillator();
   CalculateVPT(close, volume, bars);
   g_vi.vroc       = CalculateVROC(volume, VROC_Period);
   CalculatePVI_NVI(close, volume, bars);
   CalculateVolumeProfile(high, low, close, volume, bars);
}

//+------------------------------------------------------------------+
//| CalculateOBV                                                      |
//+------------------------------------------------------------------+
void CalculateOBV(const double &close[], const long &volume[], int bars)
{
   double obv_temp[];
   ArrayResize(obv_temp, bars);
   obv_temp[bars-1] = (double)volume[bars-1];

   for(int i = bars-2; i >= 0; i--)
   {
      if(close[i] > close[i+1])
         obv_temp[i] = obv_temp[i+1] + (double)volume[i];
      else if(close[i] < close[i+1])
         obv_temp[i] = obv_temp[i+1] - (double)volume[i];
      else
         obv_temp[i] = obv_temp[i+1];
   }

   g_vi.obv = obv_temp[0];
   double ma_sum = 0;
   for(int i = 0; i < OBV_MA_Period && i < bars; i++)
      ma_sum += obv_temp[i];
   g_vi.obv_ma = ma_sum / MathMin(OBV_MA_Period, bars);
}

//+------------------------------------------------------------------+
//| CalculateAD                                                       |
//+------------------------------------------------------------------+
void CalculateAD(const double &high[], const double &low[],
                 const double &close[], const long &volume[], int bars)
{
   double ad_temp[];
   ArrayResize(ad_temp, bars);
   ad_temp[bars-1] = 0;

   for(int i = bars-2; i >= 0; i--)
   {
      double hl = high[i] - low[i];
      double clv = (hl > 0.0) ? ((close[i] - low[i]) - (high[i] - close[i])) / hl : 0.0;
      ad_temp[i] = ad_temp[i+1] + clv * (double)volume[i];
   }

   g_vi.ad          = ad_temp[0];
   g_vi.ad_ema_fast = CalculateEMA_Array(ad_temp, bars, ChaikinFast);
   g_vi.ad_ema_slow = CalculateEMA_Array(ad_temp, bars, ChaikinSlow);
}

//+------------------------------------------------------------------+
//| CalculateEMA_Array                                                |
//+------------------------------------------------------------------+
double CalculateEMA_Array(const double &arr[], int size, int period)
{
   if(size < period) return arr[0];
   double k = 2.0 / (period + 1);
   double ema = arr[size-1];
   for(int i = size-2; i >= 0; i--)
      ema = arr[i] * k + ema * (1.0 - k);
   return ema;
}

double CalculateChaikinOscillator()
{
   return g_vi.ad_ema_fast - g_vi.ad_ema_slow;
}

//+------------------------------------------------------------------+
//| CalculateVWAP — reset a las 22:00 UTC (apertura Asia)            |
//+------------------------------------------------------------------+
void CalculateVWAP(const double &high[], const double &low[],
                   const double &close[], const long &volume[], int bars)
{
   double sum_pv = 0, sum_v = 0;
   datetime now = iTime(_Symbol, PERIOD_CURRENT, 0);
   MqlDateTime dt;
   TimeToStruct(now, dt);

   datetime day_start = now - (dt.hour * 3600 + dt.min * 60 + dt.sec);
   if(dt.hour >= 22)
      day_start += 22 * 3600;
   else
      day_start = day_start - 86400 + 22 * 3600;

   for(int i = 0; i < bars; i++)
   {
      datetime bar_time = iTime(_Symbol, PERIOD_CURRENT, i);
      if(bar_time < day_start) break;
      double typical = (high[i] + low[i] + close[i]) / 3.0;
      sum_pv += typical * (double)volume[i];
      sum_v  += (double)volume[i];
   }
   g_vi.vwap = (sum_v > 0) ? sum_pv / sum_v : close[0];
}

//+------------------------------------------------------------------+
//| CalculateMFI                                                      |
//+------------------------------------------------------------------+
double CalculateMFI(const double &high[], const double &low[],
                    const double &close[], const long &volume[], int period)
{
   if(Bars(_Symbol, PERIOD_CURRENT) < period + 1) return 50.0;
   double pos_flow = 0, neg_flow = 0;

   for(int i = 0; i < period; i++)
   {
      double tp_curr = (high[i]   + low[i]   + close[i])   / 3.0;
      double tp_prev = (high[i+1] + low[i+1] + close[i+1]) / 3.0;
      double mf = tp_curr * (double)volume[i];
      if(tp_curr > tp_prev)      pos_flow += mf;
      else if(tp_curr < tp_prev) neg_flow += mf;
   }
   if(neg_flow == 0) return 100.0;
   return 100.0 - (100.0 / (1.0 + pos_flow / neg_flow));
}

//+------------------------------------------------------------------+
//| CalculateCMF                                                      |
//+------------------------------------------------------------------+
double CalculateCMF(const double &high[], const double &low[],
                    const double &close[], const long &volume[], int period)
{
   double sum_mfv = 0, sum_vol = 0;
   for(int i = 0; i < period; i++)
   {
      double hl = high[i] - low[i];
      double clv = (hl > 0.0) ? ((close[i] - low[i]) - (high[i] - close[i])) / hl : 0.0;
      sum_mfv += clv * (double)volume[i];
      sum_vol += (double)volume[i];
   }
   return (sum_vol > 0) ? sum_mfv / sum_vol : 0.0;
}

//+------------------------------------------------------------------+
//| CalculateVPT                                                      |
//+------------------------------------------------------------------+
void CalculateVPT(const double &close[], const long &volume[], int bars)
{
   double vpt_temp[];
   ArrayResize(vpt_temp, bars);
   vpt_temp[bars-1] = 0;
   for(int i = bars-2; i >= 0; i--)
   {
      double pct = (close[i+1] > 0) ? (close[i] - close[i+1]) / close[i+1] : 0;
      vpt_temp[i] = vpt_temp[i+1] + (double)volume[i] * pct;
   }
   g_vi.vpt    = vpt_temp[0];
   g_vi.vpt_ma = CalculateEMA_Array(vpt_temp, bars, VPT_MA_Period);
}

double CalculateVROC(const long &volume[], int period)
{
   if(Bars(_Symbol, PERIOD_CURRENT) < period + 1) return 0;
   double vol_now = (double)volume[0];
   double vol_old = (double)volume[period];
   if(vol_old == 0) return 0;
   return (vol_now - vol_old) / vol_old * 100.0;
}

//+------------------------------------------------------------------+
//| CalculatePVI_NVI                                                  |
//+------------------------------------------------------------------+
void CalculatePVI_NVI(const double &close[], const long &volume[], int bars)
{
   double pvi_arr[], nvi_arr[];
   ArrayResize(pvi_arr, bars);
   ArrayResize(nvi_arr, bars);
   pvi_arr[bars-1] = 1000.0;
   nvi_arr[bars-1] = 1000.0;

   for(int i = bars-2; i >= 0; i--)
   {
      double pct = (close[i+1] > 0) ? (close[i] - close[i+1]) / close[i+1] * 100.0 : 0;
      pvi_arr[i] = (volume[i] > volume[i+1]) ? pvi_arr[i+1] + pvi_arr[i+1] * pct / 100.0 : pvi_arr[i+1];
      nvi_arr[i] = (volume[i] < volume[i+1]) ? nvi_arr[i+1] + nvi_arr[i+1] * pct / 100.0 : nvi_arr[i+1];
   }

   g_vi.pvi    = pvi_arr[0];
   g_vi.pvi_ma = CalculateEMA_Array(pvi_arr, bars, PVI_MA_Period);
   g_vi.nvi    = nvi_arr[0];
   g_vi.nvi_ma = CalculateEMA_Array(nvi_arr, bars, NVI_MA_Period);
}

//+------------------------------------------------------------------+
//| CalculateVolumeProfile                                            |
//+------------------------------------------------------------------+
void CalculateVolumeProfile(const double &high[], const double &low[],
                             const double &close[], const long &volume[], int bars)
{
   int lookback = MathMin(VP_Period, bars);
   double price_high = high[ArrayMaximum(high, 0, lookback)];
   double price_low  = low[ArrayMinimum(low, 0, lookback)];
   double price_range = price_high - price_low;

   if(price_range <= 0) { g_vi.vp_poc = close[0]; g_vi.vp_vah = close[0]*1.002; g_vi.vp_val = close[0]*0.998; g_vi.vp_zone = 0; return; }

   double zone_vol[], zone_price[];
   ArrayResize(zone_vol,   VP_ZoneCount);
   ArrayResize(zone_price, VP_ZoneCount);
   ArrayInitialize(zone_vol, 0);

   double zone_size = price_range / VP_ZoneCount;
   for(int z = 0; z < VP_ZoneCount; z++)
      zone_price[z] = price_low + (z + 0.5) * zone_size;

   for(int i = 0; i < lookback; i++)
   {
      double tp = (high[i] + low[i] + close[i]) / 3.0;
      int zone = (int)MathFloor((tp - price_low) / zone_size);
      zone = MathMax(0, MathMin(zone, VP_ZoneCount - 1));
      zone_vol[zone] += (double)volume[i];
   }

   int poc_idx = ArrayMaximum(zone_vol, 0, VP_ZoneCount);
   g_vi.vp_poc = zone_price[poc_idx];

   double total_vol = 0;
   for(int z = 0; z < VP_ZoneCount; z++) total_vol += zone_vol[z];
   double target_vol = total_vol * 0.70;

   int va_low = poc_idx, va_high = poc_idx;
   double va_vol = zone_vol[poc_idx];

   while(va_vol < target_vol && (va_low > 0 || va_high < VP_ZoneCount - 1))
   {
      double ext_low  = (va_low  > 0)              ? zone_vol[va_low  - 1] : 0;
      double ext_high = (va_high < VP_ZoneCount-1) ? zone_vol[va_high + 1] : 0;
      if(ext_high >= ext_low && va_high < VP_ZoneCount - 1) { va_high++; va_vol += zone_vol[va_high]; }
      else if(va_low > 0)                                   { va_low--;  va_vol += zone_vol[va_low];  }
      else break;
   }

   g_vi.vp_vah = zone_price[va_high] + zone_size * 0.5;
   g_vi.vp_val = zone_price[va_low]  - zone_size * 0.5;

   double cp = close[0];
   g_vi.vp_zone = (cp > g_vi.vp_vah) ? 1 : ((cp < g_vi.vp_val) ? -1 : 0);
}

//+------------------------------------------------------------------+
//| UpdateAsianRange — V4: detecta breakout del rango asiático        |
//+------------------------------------------------------------------+
void UpdateAsianRange()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);

   double asian_high = -DBL_MAX, asian_low = DBL_MAX;
   bool found = false;

   for(int i = 0; i < 200; i++)
   {
      datetime bar_time = iTime(_Symbol, PERIOD_CURRENT, i);
      MqlDateTime bar_dt;
      TimeToStruct(bar_time, bar_dt);
      int bar_hour = bar_dt.hour;
      bool is_asian = (bar_hour >= AsiaStartHour || bar_hour < AsiaEndHour);

      if(!is_asian && found) break;
      if(!is_asian) continue;

      found = true;
      double h = iHigh(_Symbol, PERIOD_CURRENT, i);
      double l = iLow(_Symbol,  PERIOD_CURRENT, i);
      if(h > asian_high) asian_high = h;
      if(l < asian_low)  asian_low  = l;
   }

   if(!found || asian_high == -DBL_MAX) { g_asian.valid = false; return; }

   g_asian.high  = asian_high;
   g_asian.low   = asian_low;
   g_asian.range = asian_high - asian_low;
   g_asian.valid = true;

   double cp   = iClose(_Symbol, PERIOD_CURRENT, 0);
   double ch   = iHigh(_Symbol,  PERIOD_CURRENT, 0);
   double cl   = iLow(_Symbol,   PERIOD_CURRENT, 0);
   double buf  = AsianBreakoutBuffer;

   // V4: London Sweep (trampa de liquidez) — precio barró y regresó
   if(ch > asian_high + buf && cp < asian_high) g_asian.sweptHigh  = true;
   if(cl < asian_low  - buf && cp > asian_low)  g_asian.sweptLow   = true;

   // V4: Asian Breakout limpio (sin regreso) — momentum direccional
   g_asian.breakoutUp   = (cp > asian_high + buf);
   g_asian.breakoutDown = (cp < asian_low  - buf);
}

//+------------------------------------------------------------------+
//| CalculateGVFS — Gold Volume Fusion Score (-14 a +14)             |
//+------------------------------------------------------------------+
int CalculateGVFS()
{
   int score = 0;
   double close_price = iClose(_Symbol, PERIOD_CURRENT, 0);

   // --- OBV vs MA ---
   if(g_vi.obv > g_vi.obv_ma)       score += 1;
   else if(g_vi.obv < g_vi.obv_ma)  score -= 1;

   // --- Precio vs VWAP ---
   if(UseVWAP)
   {
      if(close_price > g_vi.vwap)       score += 1;
      else if(close_price < g_vi.vwap)  score -= 1;
   }

   // --- CMF ---
   if(g_vi.cmf >  CMF_Threshold)       score += 1;
   else if(g_vi.cmf < -CMF_Threshold)  score -= 1;

   // --- MFI zona ---
   if(g_vi.mfi < MFI_NeutralHigh && g_vi.mfi > MFI_NeutralLow)
   {
      if(g_vi.obv > g_vi.obv_ma) score += 1;
      else                         score -= 1;
   }
   else if(g_vi.mfi < MFI_OversoldLevel)    score += 1;
   else if(g_vi.mfi > MFI_OverboughtLevel)  score -= 1;

   // --- Chaikin Oscillator (A/D tendencia) ---
   if(g_vi.chaikin_osc > 0)       score += 1;
   else if(g_vi.chaikin_osc < 0)  score -= 1;

   // --- VPT vs MA ---
   if(g_vi.vpt > g_vi.vpt_ma)       score += 1;
   else if(g_vi.vpt < g_vi.vpt_ma)  score -= 1;

   // --- VROC ---
   if(g_vi.vroc > 0)       score += 1;
   else if(g_vi.vroc < 0)  score -= 1;

   // --- NVI (smart money) ---
   if(g_vi.nvi > g_vi.nvi_ma)       score += 1;
   else if(g_vi.nvi < g_vi.nvi_ma)  score -= 1;

   // --- PVI (retail momentum) ---
   if(g_vi.pvi > g_vi.pvi_ma)       score += 1;
   else if(g_vi.pvi < g_vi.pvi_ma)  score -= 1;

   // --- Volume Profile position ---
   double poc_dist = MathAbs(close_price - g_vi.vp_poc) / close_price;
   if(poc_dist < VP_POC_Buffer)
   {
      if(g_vi.cmf > 0) score += 1;
      else              score -= 1;
   }
   else if(g_vi.vp_zone == 0)
   {
      if(g_vi.obv > g_vi.obv_ma) score += 1;
      else                         score -= 1;
   }

   // --- London Sweep bonus +2 (trampa de liquidez) ---
   if(UseLondonSweepBonus && g_asian.valid)
   {
      if(g_asian.sweptHigh && close_price < g_asian.high) score -= 2;
      if(g_asian.sweptLow  && close_price > g_asian.low)  score += 2;
   }

   // --- V4: Asian Breakout bonus +1 (momentum de ruptura limpia) ---
   if(UseAsianBreakoutMode && g_asian.valid)
   {
      if(g_asian.breakoutUp   && g_vi.obv > g_vi.obv_ma) score += 1;
      if(g_asian.breakoutDown && g_vi.obv < g_vi.obv_ma) score -= 1;
   }

   // --- EMA Trend alignment ---
   double ema20[], ema50[], ema200[];
   ArraySetAsSeries(ema20,  true);
   ArraySetAsSeries(ema50,  true);
   ArraySetAsSeries(ema200, true);
   CopyBuffer(h_EMA20,  0, 0, 1, ema20);
   CopyBuffer(h_EMA50,  0, 0, 1, ema50);
   CopyBuffer(h_EMA200, 0, 0, 1, ema200);

   if(ema20[0] > ema50[0] && ema50[0] > ema200[0])
   {
      if(score > 0) score = MathMin(score + 1, 14);
   }
   else if(ema20[0] < ema50[0] && ema50[0] < ema200[0])
   {
      if(score < 0) score = MathMax(score - 1, -14);
   }

   return score;
}

//+------------------------------------------------------------------+
//| IsValidSession                                                    |
//+------------------------------------------------------------------+
bool IsValidSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   int dow  = dt.day_of_week;

   if(dow == 0 || dow == 6) return false;
   if(FilterMonday && dow == 1) return false;
   if(FilterFriday && dow == 5 && hour >= 14) return false;
   if(FilterWeekdays && (dow == 1 || dow == 5)) return false;

   bool london_window  = (hour >= LondonOpenHour  && hour < LondonCloseHour);
   bool overlap_window = (hour >= OverlapStartHour && hour < OverlapEndHour);

   return (london_window || overlap_window);
}

//+------------------------------------------------------------------+
//| CheckRiskLimits                                                   |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);

   double daily_loss_pct  = (balance - g_dailyStartBalance)  / g_dailyStartBalance  * 100.0;
   double weekly_loss_pct = (balance - g_weeklyStartBalance) / g_weeklyStartBalance * 100.0;

   if(daily_loss_pct  < -DailyLossLimit)  return false;
   if(weekly_loss_pct < -WeeklyLossLimit) return false;
   if(g_dailyTrades  >= MaxTradesPerDay)  return false;
   if(g_weeklyTrades >= MaxTradesPerWeek) return false;

   double float_loss = (equity - balance) / balance * 100.0;
   if(float_loss < -3.0) return false; // V4: 2.0→3.0% (más tolerante)

   return true;
}

//+------------------------------------------------------------------+
//| CheckADRFilter                                                    |
//+------------------------------------------------------------------+
bool CheckADRFilter()
{
   double sum_range = 0;
   int valid_days = 0;
   for(int i = 1; i <= ADR_Period; i++)
   {
      double dh = iHigh(_Symbol, PERIOD_D1, i);
      double dl = iLow(_Symbol,  PERIOD_D1, i);
      if(dh > 0 && dl > 0 && dh > dl) { sum_range += (dh - dl); valid_days++; }
   }
   if(valid_days == 0) return true;
   double adr = sum_range / valid_days;

   double today_high  = iHigh(_Symbol, PERIOD_D1, 0);
   double today_low   = iLow(_Symbol,  PERIOD_D1, 0);
   double today_range = today_high - today_low;

   return (adr == 0 || today_range / adr <= ADR_MaxUsed);
}

//+------------------------------------------------------------------+
//| CalculateLotSize                                                  |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_dist, double risk_pct = -1.0)
{
   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   if(risk_pct < 0) risk_pct = RiskPercent;
   double risk_usd   = balance * risk_pct / 100.0;
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tick_size == 0 || tick_value == 0 || sl_dist == 0) return 0.01;

   double sl_per_lot = (sl_dist / tick_size) * tick_value;
   double lots = risk_usd / sl_per_lot;

   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lot_min  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lot_max  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   lots = MathFloor(lots / lot_step) * lot_step;
   return MathMax(lot_min, MathMin(lot_max, lots));
}

//+------------------------------------------------------------------+
//| ExecuteLongEntry                                                  |
//+------------------------------------------------------------------+
void ExecuteLongEntry(int score)
{
   if(!CheckADRFilter()) return;

   double atr_arr[];
   ArraySetAsSeries(atr_arr, true);
   CopyBuffer(h_ATR, 0, 0, 1, atr_arr);
   double atr = atr_arr[0];

   double entry   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double sl_dist = MathMax(atr * SL_ATR_Mult, MinSL_Pips * _Point);
   double sl      = NormalizeDouble(entry - sl_dist, _Digits);
   double tp1     = NormalizeDouble(entry + sl_dist * TP1_Ratio, _Digits);
   double tp2     = NormalizeDouble(entry + sl_dist * TP2_Ratio, _Digits);
   double tp3     = NormalizeDouble(entry + sl_dist * TP3_Ratio, _Digits);

   double risk_mult = (score >= HighConfScore) ? 1.0 : 0.75;
   double lots      = CalculateLotSize(sl_dist, RiskPercent * risk_mult);
   if(lots <= 0) return;

   int dec = (int)MathRound(-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots1 = NormalizeDouble(lots * TP1_ClosePercent / 100.0, dec);
   double lots2 = NormalizeDouble(lots * TP2_ClosePercent / 100.0, dec);
   double lots3 = NormalizeDouble(lots - lots1 - lots2, dec);
   double lot_min = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   lots1 = MathMax(lot_min, lots1);
   lots2 = MathMax(lot_min, lots2);
   lots3 = MathMax(lot_min, lots3);

   string comment = StringFormat("GVFE4_L_S%d", score);
   if(trade.Buy(lots1, _Symbol, entry, sl, tp1, comment + "_TP1")) g_dailyTrades++;
   if(trade.Buy(lots2, _Symbol, entry, sl, tp2, comment + "_TP2")) {}
   if(trade.Buy(lots3, _Symbol, entry, sl, tp3, comment + "_TP3")) {}
   g_weeklyTrades++;

   PrintFormat("LONG | Score=%d | Entry=%.2f | SL=%.2f | TP1=%.2f TP2=%.2f TP3=%.2f | Lots=%.2f",
               score, entry, sl, tp1, tp2, tp3, lots);
}

//+------------------------------------------------------------------+
//| ExecuteShortEntry                                                 |
//+------------------------------------------------------------------+
void ExecuteShortEntry(int score)
{
   if(!CheckADRFilter()) return;

   double atr_arr[];
   ArraySetAsSeries(atr_arr, true);
   CopyBuffer(h_ATR, 0, 0, 1, atr_arr);
   double atr = atr_arr[0];

   double entry   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl_dist = MathMax(atr * SL_ATR_Mult, MinSL_Pips * _Point);
   double sl      = NormalizeDouble(entry + sl_dist, _Digits);
   double tp1     = NormalizeDouble(entry - sl_dist * TP1_Ratio, _Digits);
   double tp2     = NormalizeDouble(entry - sl_dist * TP2_Ratio, _Digits);
   double tp3     = NormalizeDouble(entry - sl_dist * TP3_Ratio, _Digits);

   double risk_mult = (MathAbs(score) >= HighConfScore) ? 1.0 : 0.75;
   double lots      = CalculateLotSize(sl_dist, RiskPercent * risk_mult);
   if(lots <= 0) return;

   int dec = (int)MathRound(-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots1 = NormalizeDouble(lots * TP1_ClosePercent / 100.0, dec);
   double lots2 = NormalizeDouble(lots * TP2_ClosePercent / 100.0, dec);
   double lots3 = NormalizeDouble(lots - lots1 - lots2, dec);
   double lot_min = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   lots1 = MathMax(lot_min, lots1);
   lots2 = MathMax(lot_min, lots2);
   lots3 = MathMax(lot_min, lots3);

   string comment = StringFormat("GVFE4_S_S%d", score);
   if(trade.Sell(lots1, _Symbol, entry, sl, tp1, comment + "_TP1")) g_dailyTrades++;
   if(trade.Sell(lots2, _Symbol, entry, sl, tp2, comment + "_TP2")) {}
   if(trade.Sell(lots3, _Symbol, entry, sl, tp3, comment + "_TP3")) {}
   g_weeklyTrades++;

   PrintFormat("SHORT | Score=%d | Entry=%.2f | SL=%.2f | TP1=%.2f TP2=%.2f TP3=%.2f | Lots=%.2f",
               score, entry, sl, tp1, tp2, tp3, lots);
}

//+------------------------------------------------------------------+
//| ManageOpenPositions — SL a breakeven + trailing stop              |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Magic() != MagicNumber || posInfo.Symbol() != _Symbol) continue;

      ulong ticket   = posInfo.Ticket();
      double entry   = posInfo.PriceOpen();
      double sl      = posInfo.StopLoss();
      double tp      = posInfo.TakeProfit();
      double sl_dist = MathAbs(entry - sl);

      double atr_arr[];
      ArraySetAsSeries(atr_arr, true);
      CopyBuffer(h_ATR, 0, 0, 1, atr_arr);
      double atr = atr_arr[0];

      if(posInfo.PositionType() == POSITION_TYPE_BUY)
      {
         double current = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double profit  = current - entry;
         // SL a BE después de TP1
         if(profit >= sl_dist * TP1_Ratio && sl < entry)
            trade.PositionModify(ticket, NormalizeDouble(entry + 5 * _Point, _Digits), tp);
         // Trailing con EMA20 después de TP2
         if(profit >= sl_dist * TP2_Ratio)
         {
            double ema20_arr[];
            ArraySetAsSeries(ema20_arr, true);
            CopyBuffer(h_EMA20, 0, 0, 1, ema20_arr);
            double trail = NormalizeDouble(ema20_arr[0] - atr * 0.5, _Digits);
            if(trail > sl) trade.PositionModify(ticket, trail, tp);
         }
      }
      else if(posInfo.PositionType() == POSITION_TYPE_SELL)
      {
         double current = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double profit  = entry - current;
         if(profit >= sl_dist * TP1_Ratio && sl > entry)
            trade.PositionModify(ticket, NormalizeDouble(entry - 5 * _Point, _Digits), tp);
         if(profit >= sl_dist * TP2_Ratio)
         {
            double ema20_arr[];
            ArraySetAsSeries(ema20_arr, true);
            CopyBuffer(h_EMA20, 0, 0, 1, ema20_arr);
            double trail = NormalizeDouble(ema20_arr[0] + atr * 0.5, _Digits);
            if(trail < sl) trade.PositionModify(ticket, trail, tp);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| ResetDailyCounters                                                |
//+------------------------------------------------------------------+
void ResetDailyCounters()
{
   MqlDateTime now_dt, last_dt;
   TimeToStruct(TimeCurrent(), now_dt);
   TimeToStruct(g_lastDayReset, last_dt);
   if(now_dt.day != last_dt.day || now_dt.mon != last_dt.mon)
   {
      g_dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_dailyTrades = 0;
      g_lastDayReset = TimeCurrent();
      g_asian.sweptHigh  = false;
      g_asian.sweptLow   = false;
      g_asian.breakoutUp   = false;
      g_asian.breakoutDown = false;
   }
}

//+------------------------------------------------------------------+
//| ResetWeeklyCounters                                               |
//+------------------------------------------------------------------+
void ResetWeeklyCounters()
{
   MqlDateTime now_dt, last_dt;
   TimeToStruct(TimeCurrent(), now_dt);
   TimeToStruct(g_lastWeekReset, last_dt);
   if(now_dt.day_of_week == 1 && last_dt.day_of_week != 1)
   {
      g_weeklyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_weeklyTrades = 0;
      g_lastWeekReset = TimeCurrent();
   }
}

int CountMagicPositions()
{
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == MagicNumber && posInfo.Symbol() == _Symbol)
         count++;
   return count;
}
//+------------------------------------------------------------------+
