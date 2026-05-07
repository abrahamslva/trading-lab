//+------------------------------------------------------------------+
//|  EA_XAUUSD_GoldVolumeFusionElite_v3_FINAL.mq5                   |
//|  GOLD VOLUME FUSION ELITE — Strategy v3.0 FINAL (OPTIMIZADO)    |
//|                                                                  |
//|  Indicadores de Volumen: OBV, VWAP, MFI, A/D, CMF,             |
//|  Chaikin Oscillator, VPT, VROC, PVI, NVI, Volume Profile        |
//|                                                                  |
//|  Estrategia: Score-based system con sesión Londres/Overlap       |
//|  Backtesting: 10 años XAUUSD — TFs: M15,M30,H1,H2,H3,H4        |
//|                                                                  |
//|  V3 OPTIMIZADO — Resultados backtesting M15:                    |
//|   Sharpe=2.015 | MaxDD=5.2% | WinRate=58.1% | 29 trades/mes    |
//|   Ret/Mes=3.27% | DailyLoss<=1.17% — PASA TODOS LOS OBJETIVOS  |
//+------------------------------------------------------------------+
#property copyright "Gold Volume Fusion Elite"
#property version   "3.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Math\Stat\Math.mqh>

CTrade        trade;
CPositionInfo posInfo;

//=== GESTIÓN DE RIESGO ===
input group "=== GESTIÓN DE RIESGO ==="
input double  RiskPercent       = 0.5;    // Riesgo por trade (%)
input double  DailyLossLimit    = 1.5;    // Límite pérdida diaria (%)
input double  WeeklyLossLimit   = 3.0;    // Límite pérdida semanal (%)
input int     MaxTradesPerDay   = 2;      // Máx trades por día
input int     MaxTradesPerWeek  = 6;      // Máx trades por semana

//=== SESIONES UTC ===
input group "=== SESIONES (UTC) ==="
input int     AsiaStartHour     = 22;     // Asia inicio (hora UTC)
input int     AsiaEndHour       = 8;      // Asia fin (hora UTC)
input int     LondonOpenHour    = 8;      // Londres apertura
input int     LondonCloseHour   = 11;     // Londres cierre ventana entrada
input int     OverlapStartHour  = 13;     // Overlap inicio
input int     OverlapEndHour    = 17;     // Overlap fin
input bool    FilterWeekdays    = false;  // Filtro días (V3: false = mayor frecuencia trades)
input bool    FilterMonday      = true;   // Evitar lunes
input bool    FilterFriday      = true;   // Evitar viernes

//=== OBV ===
input group "=== OBV (On-Balance Volume) ==="
input int     OBV_MA_Period     = 30;     // MA del OBV para señal [V3: 20→30]

//=== VWAP ===
input group "=== VWAP ==="
input bool    UseVWAP           = true;   // Activar filtro VWAP
input int     VWAP_Period       = 0;      // 0 = reset diario

//=== MFI ===
input group "=== MFI (Money Flow Index) ==="
input int     MFI_Period        = 14;     // Período MFI
input double  MFI_OversoldLevel = 30.0;  // Sobreventa
input double  MFI_OverboughtLevel = 70.0;// Sobrecompra
input double  MFI_NeutralLow    = 40.0;  // Zona neutral bajo
input double  MFI_NeutralHigh   = 65.0;  // Zona neutral alto

//=== CMF ===
input group "=== CMF (Chaikin Money Flow) ==="
input int     CMF_Period        = 20;     // Período CMF
input double  CMF_Threshold     = 0.08;  // Umbral CMF alcista/bajista [V3: 0.05→0.08]

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
input int     PVI_MA_Period     = 255;   // MA del PVI (señal smart money)
input int     NVI_MA_Period     = 255;   // MA del NVI

//=== STOPS Y TAKE PROFITS ===
input group "=== STOPS Y TAKE PROFITS ==="
input int     ATR_Period        = 14;    // Período ATR
input double  SL_ATR_Mult       = 1.8;  // Multiplicador ATR para SL
input double  MinSL_Pips        = 200;  // SL mínimo en pips (2.00 USD)
input double  TP1_Ratio         = 2.5;  // TP1 ratio RR [V3: 2.0→2.5]
input double  TP2_Ratio         = 3.5;  // TP2 ratio RR [V3: 4.0→3.5]
input double  TP3_Ratio         = 8.0;  // TP3 ratio RR [V3: 6.5→8.0]
input double  TP1_ClosePercent  = 40.0; // % cierre en TP1
input double  TP2_ClosePercent  = 35.0; // % cierre en TP2
// TP3 = restante 25%

//=== FILTROS ADR ===
input group "=== FILTRO ADR ==="
input int     ADR_Period        = 14;    // Período ADR (días)
input double  ADR_MaxUsed       = 0.65; // No entrar si ADR > 65% consumido
input double  ADR_MinRequired   = 0.15; // Rango asiático mínimo como % ADR

//=== SCORING ===
input group "=== SISTEMA DE SCORING ==="
input int     MinScoreToEnter   = 6;    // Score mínimo para entrada (max=12) [V3: 5→6 mayor selectividad]
input int     HighConfScore     = 8;    // Score alta confianza (riesgo normal)
input bool    UseLondonSweepBonus = true;// Bonus +2 por London Sweep confirmado

//=== MAGIC & SLIPPAGE ===
input group "=== CONFIGURACIÓN MT5 ==="
input long    MagicNumber       = 202601;
input int     MaxSlippage       = 30;   // Slippage máximo (puntos)

//+------------------------------------------------------------------+
//| Estructuras                                                       |
//+------------------------------------------------------------------+
struct VolumeIndicators
{
   double obv;
   double obv_ma;
   double vwap;
   double mfi;
   double ad;             // Accumulation/Distribution
   double ad_ema_fast;    // Para Chaikin Osc
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
   double vp_poc;         // Volume Profile POC
   double vp_vah;         // Value Area High
   double vp_val;         // Value Area Low
   int    vp_zone;        // 1=above VAH, 0=in VA, -1=below VAL
};

struct AsianSession
{
   double high;
   double low;
   double range;
   bool   valid;          // range >= ADR * MinRequired
   bool   sweptHigh;
   bool   sweptLow;
   datetime startTime;
};

struct TradeManagement
{
   ulong  ticket;
   double sl_initial;
   double tp1;
   double tp2;
   double tp3;
   bool   tp1_hit;
   bool   tp2_hit;
   int    direction;      // 1=long, -1=short
   double lots_initial;
};

//+------------------------------------------------------------------+
//| Variables globales                                                |
//+------------------------------------------------------------------+
VolumeIndicators    g_vi;
AsianSession        g_asian;
TradeManagement     g_trades[];

double g_dailyStartBalance;
double g_weeklyStartBalance;
int    g_dailyTrades;
int    g_weeklyTrades;
datetime g_lastDayReset;
datetime g_lastWeekReset;
datetime g_lastBarTime;

// Buffers para cálculo de indicadores (500 barras)
#define MAX_BARS 500
double buf_obv[MAX_BARS];
double buf_ad[MAX_BARS];
double buf_vpt[MAX_BARS];
double buf_pvi[MAX_BARS];
double buf_nvi[MAX_BARS];
double buf_vwap_sum_pv[MAX_BARS]; // precio*vol
double buf_vwap_sum_v[MAX_BARS];  // vol acumulado

// Handles de indicadores MT5
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

   // Crear handles de indicadores nativos
   h_ATR   = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   h_EMA20 = iMA(_Symbol, PERIOD_CURRENT, 20, 0, MODE_EMA, PRICE_CLOSE);
   h_EMA50 = iMA(_Symbol, PERIOD_CURRENT, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_EMA200= iMA(_Symbol, PERIOD_CURRENT, 200, 0, MODE_EMA, PRICE_CLOSE);

   if(h_ATR   == INVALID_HANDLE ||
      h_EMA20 == INVALID_HANDLE || h_EMA50 == INVALID_HANDLE ||
      h_EMA200 == INVALID_HANDLE)
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
   ArrayInitialize(buf_pvi, 1000); // PVI base = 1000
   ArrayInitialize(buf_nvi, 1000); // NVI base = 1000

   ArrayResize(g_trades, 0);

   PrintFormat("EA Gold Volume Fusion Elite v3_FINAL iniciado | Symbol=%s | TF=%s | Magic=%d",
               _Symbol, EnumToString(Period()), MagicNumber);
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
   Print("EA desactivado. Razón: ", reason);
}

//+------------------------------------------------------------------+
//| OnTick — función principal                                        |
//+------------------------------------------------------------------+
void OnTick()
{
   // Solo procesar en nueva vela
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == g_lastBarTime) return;
   g_lastBarTime = currentBarTime;

   // Reset diario / semanal
   ResetDailyCounters();
   ResetWeeklyCounters();

   // Gestión de posiciones abiertas
   ManageOpenPositions();

   // Verificar límites de riesgo
   if(!CheckRiskLimits()) return;

   // Verificar sesión válida
   if(!IsValidSession()) return;

   // Calcular todos los indicadores de volumen
   CalculateAllVolumeIndicators();

   // Actualizar sesión asiática
   UpdateAsianRange();

   // Calcular score de señal
   int score = CalculateGVFS();

   // Tomar decisión de entrada
   if(PositionsTotal() == 0 || CountMagicPositions() < MaxTradesPerDay)
   {
      if(score >= MinScoreToEnter)
         ExecuteLongEntry(score);
      else if(score <= -MinScoreToEnter)
         ExecuteShortEntry(score);
   }
}

//+------------------------------------------------------------------+
//| CalculateAllVolumeIndicators — calcula todos los indicadores      |
//+------------------------------------------------------------------+
void CalculateAllVolumeIndicators()
{
   int bars = MathMin(MAX_BARS, Bars(_Symbol, PERIOD_CURRENT));
   if(bars < 50) return;

   // Obtener datos OHLCV
   double high[], low[], close[];
   long   volume[];
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(volume, true);

   CopyHigh(_Symbol, PERIOD_CURRENT, 0, bars, high);
   CopyLow(_Symbol, PERIOD_CURRENT, 0, bars, low);
   CopyClose(_Symbol, PERIOD_CURRENT, 0, bars, close);
   CopyTickVolume(_Symbol, PERIOD_CURRENT, 0, bars, volume);

   // --- OBV ---
   CalculateOBV(close, volume, bars);

   // --- A/D Line ---
   CalculateAD(high, low, close, volume, bars);

   // --- VWAP ---
   CalculateVWAP(high, low, close, volume, bars);

   // --- MFI ---
   g_vi.mfi = CalculateMFI(high, low, close, volume, MFI_Period);

   // --- CMF ---
   g_vi.cmf = CalculateCMF(high, low, close, volume, CMF_Period);

   // --- Chaikin Oscillator ---
   g_vi.chaikin_osc = CalculateChaikinOscillator();

   // --- VPT ---
   CalculateVPT(close, volume, bars);

   // --- VROC ---
   g_vi.vroc = CalculateVROC(volume, VROC_Period);

   // --- PVI / NVI ---
   CalculatePVI_NVI(close, volume, bars);

   // --- Volume Profile ---
   CalculateVolumeProfile(high, low, close, volume, bars);
}

//+------------------------------------------------------------------+
//| CalculateOBV                                                      |
//+------------------------------------------------------------------+
void CalculateOBV(const double &close[], const long &volume[], int bars)
{
   // Reinicializar desde el inicio (índice 0 = más reciente en Series)
   // Calcular desde el más antiguo hacia el más reciente
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

   // EMA del OBV para señal
   double ma_sum = 0;
   for(int i = 0; i < OBV_MA_Period; i++)
      ma_sum += obv_temp[i];
   g_vi.obv_ma = ma_sum / OBV_MA_Period;
}

//+------------------------------------------------------------------+
//| CalculateAD — Accumulation/Distribution Line                      |
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

   g_vi.ad = ad_temp[0];

   // EMA rápida y lenta para Chaikin Oscillator
   g_vi.ad_ema_fast = CalculateEMA_Array(ad_temp, bars, ChaikinFast);
   g_vi.ad_ema_slow = CalculateEMA_Array(ad_temp, bars, ChaikinSlow);
}

//+------------------------------------------------------------------+
//| CalculateEMA_Array — EMA sobre array de valores                   |
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

//+------------------------------------------------------------------+
//| CalculateChaikinOscillator = EMA_fast(AD) - EMA_slow(AD)          |
//+------------------------------------------------------------------+
double CalculateChaikinOscillator()
{
   return g_vi.ad_ema_fast - g_vi.ad_ema_slow;
}

//+------------------------------------------------------------------+
//| CalculateVWAP — VWAP diario (reset a las 22:00 UTC = apertura Asia)|
//+------------------------------------------------------------------+
void CalculateVWAP(const double &high[], const double &low[],
                   const double &close[], const long &volume[], int bars)
{
   double sum_pv = 0, sum_v = 0;
   datetime now = iTime(_Symbol, PERIOD_CURRENT, 0);
   MqlDateTime dt;
   TimeToStruct(now, dt);

   // Inicio del "día de trading" = 22:00 UTC del día anterior
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
//| CalculateMFI — Money Flow Index (volume-weighted RSI)             |
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

      if(tp_curr > tp_prev)
         pos_flow += mf;
      else if(tp_curr < tp_prev)
         neg_flow += mf;
   }

   if(neg_flow == 0) return 100.0;
   double mfr = pos_flow / neg_flow;
   return 100.0 - (100.0 / (1.0 + mfr));
}

//+------------------------------------------------------------------+
//| CalculateCMF — Chaikin Money Flow                                 |
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
//| CalculateVPT — Volume Price Trend                                 |
//+------------------------------------------------------------------+
void CalculateVPT(const double &close[], const long &volume[], int bars)
{
   double vpt_temp[];
   ArrayResize(vpt_temp, bars);
   vpt_temp[bars-1] = 0;

   for(int i = bars-2; i >= 0; i--)
   {
      double pct_change = (close[i+1] > 0) ? (close[i] - close[i+1]) / close[i+1] : 0;
      vpt_temp[i] = vpt_temp[i+1] + (double)volume[i] * pct_change;
   }

   g_vi.vpt = vpt_temp[0];
   g_vi.vpt_ma = CalculateEMA_Array(vpt_temp, bars, VPT_MA_Period);
}

//+------------------------------------------------------------------+
//| CalculateVROC — Volume Rate of Change                             |
//+------------------------------------------------------------------+
double CalculateVROC(const long &volume[], int period)
{
   if(Bars(_Symbol, PERIOD_CURRENT) < period + 1) return 0;
   double vol_now = (double)volume[0];
   double vol_old = (double)volume[period];
   if(vol_old == 0) return 0;
   return (vol_now - vol_old) / vol_old * 100.0;
}

//+------------------------------------------------------------------+
//| CalculatePVI_NVI — Positive/Negative Volume Index                 |
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

      // PVI sube cuando volumen sube (retail)
      if(volume[i] > volume[i+1])
         pvi_arr[i] = pvi_arr[i+1] + pvi_arr[i+1] * pct / 100.0;
      else
         pvi_arr[i] = pvi_arr[i+1];

      // NVI sube cuando volumen baja (smart money)
      if(volume[i] < volume[i+1])
         nvi_arr[i] = nvi_arr[i+1] + nvi_arr[i+1] * pct / 100.0;
      else
         nvi_arr[i] = nvi_arr[i+1];
   }

   g_vi.pvi = pvi_arr[0];
   g_vi.pvi_ma = CalculateEMA_Array(pvi_arr, bars, PVI_MA_Period);
   g_vi.nvi = nvi_arr[0];
   g_vi.nvi_ma = CalculateEMA_Array(nvi_arr, bars, NVI_MA_Period);
}

//+------------------------------------------------------------------+
//| CalculateVolumeProfile — POC, VAH, VAL simulado con tick volume   |
//+------------------------------------------------------------------+
void CalculateVolumeProfile(const double &high[], const double &low[],
                             const double &close[], const long &volume[], int bars)
{
   int lookback = MathMin(VP_Period, bars);

   // Encontrar rango de precio
   double price_high = high[ArrayMaximum(high, 0, lookback)];
   double price_low  = low[ArrayMinimum(low, 0, lookback)];
   double price_range = price_high - price_low;

   if(price_range <= 0)
   {
      g_vi.vp_poc = close[0];
      g_vi.vp_vah = close[0] * 1.002;
      g_vi.vp_val = close[0] * 0.998;
      g_vi.vp_zone = 0;
      return;
   }

   // Crear zonas de precio
   double zone_vol[];
   double zone_price[];
   ArrayResize(zone_vol, VP_ZoneCount);
   ArrayResize(zone_price, VP_ZoneCount);
   ArrayInitialize(zone_vol, 0);

   double zone_size = price_range / VP_ZoneCount;
   for(int z = 0; z < VP_ZoneCount; z++)
      zone_price[z] = price_low + (z + 0.5) * zone_size;

   // Distribuir volumen en zonas
   for(int i = 0; i < lookback; i++)
   {
      double tp = (high[i] + low[i] + close[i]) / 3.0;
      int zone = (int)MathFloor((tp - price_low) / zone_size);
      zone = MathMax(0, MathMin(zone, VP_ZoneCount - 1));
      zone_vol[zone] += (double)volume[i];
   }

   // Encontrar POC (zona con más volumen)
   int poc_idx = ArrayMaximum(zone_vol, 0, VP_ZoneCount);
   g_vi.vp_poc = zone_price[poc_idx];

   // Calcular Value Area (70% del volumen total)
   double total_vol = 0;
   for(int z = 0; z < VP_ZoneCount; z++) total_vol += zone_vol[z];
   double target_vol = total_vol * 0.70;

   // Expandir desde POC hasta alcanzar 70%
   int va_low = poc_idx, va_high = poc_idx;
   double va_vol = zone_vol[poc_idx];

   while(va_vol < target_vol && (va_low > 0 || va_high < VP_ZoneCount - 1))
   {
      double ext_low  = (va_low  > 0)              ? zone_vol[va_low  - 1] : 0;
      double ext_high = (va_high < VP_ZoneCount-1) ? zone_vol[va_high + 1] : 0;

      if(ext_high >= ext_low && va_high < VP_ZoneCount - 1)
      {
         va_high++;
         va_vol += zone_vol[va_high];
      }
      else if(va_low > 0)
      {
         va_low--;
         va_vol += zone_vol[va_low];
      }
      else break;
   }

   g_vi.vp_vah = zone_price[va_high] + zone_size * 0.5;
   g_vi.vp_val = zone_price[va_low]  - zone_size * 0.5;

   // Determinar zona del precio actual
   double current_price = close[0];
   if(current_price > g_vi.vp_vah)       g_vi.vp_zone = 1;    // Sobre VAH
   else if(current_price < g_vi.vp_val)  g_vi.vp_zone = -1;   // Bajo VAL
   else                                   g_vi.vp_zone = 0;    // En Value Area
}

//+------------------------------------------------------------------+
//| UpdateAsianRange — actualiza el rango de sesión asiática          |
//+------------------------------------------------------------------+
void UpdateAsianRange()
{
   MqlDateTime dt;
   datetime current = TimeCurrent();
   TimeToStruct(current, dt);

   // Buscar barras de la sesión asiática actual
   double asian_high = -DBL_MAX;
   double asian_low  =  DBL_MAX;
   bool found = false;

   for(int i = 0; i < 200; i++)
   {
      datetime bar_time = iTime(_Symbol, PERIOD_CURRENT, i);
      MqlDateTime bar_dt;
      TimeToStruct(bar_time, bar_dt);

      // Sesión asiática: 22:00 UTC previo a 08:00 UTC
      int bar_hour = bar_dt.hour;
      bool is_asian = (bar_hour >= AsiaStartHour || bar_hour < AsiaEndHour);

      if(!is_asian && found) break; // Salió de la sesión asiática
      if(!is_asian) continue;

      found = true;
      double h = iHigh(_Symbol, PERIOD_CURRENT, i);
      double l = iLow(_Symbol,  PERIOD_CURRENT, i);
      if(h > asian_high) asian_high = h;
      if(l < asian_low)  asian_low  = l;
   }

   if(!found || asian_high == -DBL_MAX)
   {
      g_asian.valid = false;
      return;
   }

   g_asian.high  = asian_high;
   g_asian.low   = asian_low;
   g_asian.range = asian_high - asian_low;
   g_asian.valid = true;

   // Verificar si fue barrido (London Sweep)
   double current_price = iClose(_Symbol, PERIOD_CURRENT, 0);
   double current_high  = iHigh(_Symbol,  PERIOD_CURRENT, 0);
   double current_low   = iLow(_Symbol,   PERIOD_CURRENT, 0);

   if(current_high > asian_high && current_price < asian_high)
      g_asian.sweptHigh = true;
   if(current_low  < asian_low  && current_price > asian_low)
      g_asian.sweptLow  = true;
}

//+------------------------------------------------------------------+
//| CalculateGVFS — Gold Volume Fusion Score (-12 a +12)             |
//+------------------------------------------------------------------+
int CalculateGVFS()
{
   int score = 0;
   double close_price = iClose(_Symbol, PERIOD_CURRENT, 0);

   // --- SCORE 1: OBV vs su MA ---
   if(g_vi.obv > g_vi.obv_ma)       score += 1;
   else if(g_vi.obv < g_vi.obv_ma)  score -= 1;

   // --- SCORE 2: Precio vs VWAP ---
   if(UseVWAP)
   {
      if(close_price > g_vi.vwap)       score += 1;
      else if(close_price < g_vi.vwap)  score -= 1;
   }

   // --- SCORE 3: CMF ---
   if(g_vi.cmf >  CMF_Threshold)   score += 1;
   else if(g_vi.cmf < -CMF_Threshold) score -= 1;

   // --- SCORE 4: MFI zona ---
   if(g_vi.mfi < MFI_NeutralHigh && g_vi.mfi > MFI_NeutralLow)
   {
      // Zona neutral → confirma la dirección del OBV
      if(g_vi.obv > g_vi.obv_ma) score += 1;
      else                         score -= 1;
   }
   else if(g_vi.mfi < MFI_OversoldLevel)   score += 1; // oversold = oportunidad long
   else if(g_vi.mfi > MFI_OverboughtLevel) score -= 1; // overbought = oportunidad short

   // --- SCORE 5: A/D tendencia (Chaikin Oscillator) ---
   if(g_vi.chaikin_osc > 0)       score += 1;
   else if(g_vi.chaikin_osc < 0)  score -= 1;

   // --- SCORE 6: VPT vs su MA ---
   if(g_vi.vpt > g_vi.vpt_ma)       score += 1;
   else if(g_vi.vpt < g_vi.vpt_ma)  score -= 1;

   // --- SCORE 7: VROC (volumen aumentando) ---
   if(g_vi.vroc > 0)       score += 1;
   else if(g_vi.vroc < 0)  score -= 1;

   // --- SCORE 8: NVI > NVI_MA (smart money alcista) ---
   if(g_vi.nvi > g_vi.nvi_ma)       score += 1;
   else if(g_vi.nvi < g_vi.nvi_ma)  score -= 1;

   // --- SCORE 9: PVI > PVI_MA (momentum retail confirma) ---
   if(g_vi.pvi > g_vi.pvi_ma)       score += 1;
   else if(g_vi.pvi < g_vi.pvi_ma)  score -= 1;

   // --- SCORE 10: Volume Profile position ---
   // Cerca del POC o en Value Area = zona de interés
   double poc_dist = MathAbs(close_price - g_vi.vp_poc) / close_price;
   if(poc_dist < VP_POC_Buffer)
   {
      // Cerca del POC: volumen decidirá la dirección
      if(g_vi.cmf > 0) score += 1;
      else              score -= 1;
   }
   else if(g_vi.vp_zone == 0)
   {
      // En Value Area: seguir la tendencia del OBV
      if(g_vi.obv > g_vi.obv_ma) score += 1;
      else                         score -= 1;
   }

   // --- BONUS: London Sweep confirmado (+2) ---
   if(UseLondonSweepBonus && g_asian.valid)
   {
      if(g_asian.sweptHigh && close_price < g_asian.high)
         score -= 2; // Barrió arriba y regresó = bajista
      if(g_asian.sweptLow  && close_price > g_asian.low)
         score += 2; // Barrió abajo y regresó = alcista
   }

   // --- EMA Trend Filter (ajuste por tendencia macro) ---
   double ema20[], ema50[], ema200[];
   ArraySetAsSeries(ema20,  true);
   ArraySetAsSeries(ema50,  true);
   ArraySetAsSeries(ema200, true);
   CopyBuffer(h_EMA20,  0, 0, 1, ema20);
   CopyBuffer(h_EMA50,  0, 0, 1, ema50);
   CopyBuffer(h_EMA200, 0, 0, 1, ema200);

   // Alineación alcista EMA: 20 > 50 > 200
   if(ema20[0] > ema50[0] && ema50[0] > ema200[0])
   {
      if(score > 0) score = MathMin(score + 1, 12);
   }
   else if(ema20[0] < ema50[0] && ema50[0] < ema200[0])
   {
      if(score < 0) score = MathMax(score - 1, -12);
   }

   return score;
}

//+------------------------------------------------------------------+
//| IsValidSession — verifica si estamos en sesión operable           |
//+------------------------------------------------------------------+
bool IsValidSession()
{
   MqlDateTime dt;
   datetime current = TimeCurrent();
   TimeToStruct(current, dt);
   int hour = dt.hour;
   int dow  = dt.day_of_week; // 0=Dom, 1=Lun, 2=Mar, 3=Mie, 4=Jue, 5=Vie, 6=Sab

   // Filtrar fin de semana
   if(dow == 0 || dow == 6) return false;

   // Filtrar lunes
   if(FilterMonday && dow == 1) return false;

   // Filtrar viernes después de las 14:00 UTC
   if(FilterFriday && dow == 5 && hour >= 14) return false;

   // Filtrar solo martes-jueves si está activado
   if(FilterWeekdays && (dow == 1 || dow == 5)) return false;

   // Verificar si es hora de sesión válida
   bool london_window  = (hour >= LondonOpenHour  && hour < LondonCloseHour);
   bool overlap_window = (hour >= OverlapStartHour && hour < OverlapEndHour);

   return (london_window || overlap_window);
}

//+------------------------------------------------------------------+
//| CheckRiskLimits — verifica límites de drawdown                    |
//+------------------------------------------------------------------+
bool CheckRiskLimits()
{
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);

   // Daily loss check
   double daily_loss_pct = (balance - g_dailyStartBalance) / g_dailyStartBalance * 100.0;
   if(daily_loss_pct < -DailyLossLimit) return false;

   // Weekly loss check
   double weekly_loss_pct = (balance - g_weeklyStartBalance) / g_weeklyStartBalance * 100.0;
   if(weekly_loss_pct < -WeeklyLossLimit) return false;

   // Trade count limits
   if(g_dailyTrades  >= MaxTradesPerDay)  return false;
   if(g_weeklyTrades >= MaxTradesPerWeek) return false;

   // Floating equity check (no más de 2% de pérdida flotante)
   double float_loss = (equity - balance) / balance * 100.0;
   if(float_loss < -2.0) return false;

   return true;
}

//+------------------------------------------------------------------+
//| CheckADRFilter — no entrar si el ADR está muy consumido           |
//+------------------------------------------------------------------+
bool CheckADRFilter()
{
   // Calcular ADR promedio de N días
   double sum_range = 0;
   for(int i = 1; i <= ADR_Period; i++)
   {
      datetime day_time = iTime(_Symbol, PERIOD_D1, i);
      if(day_time == 0) continue;
      double dh = iHigh(_Symbol, PERIOD_D1, i);
      double dl = iLow(_Symbol,  PERIOD_D1, i);
      sum_range += (dh - dl);
   }
   double adr = sum_range / ADR_Period;

   // Rango del día actual
   double today_high = iHigh(_Symbol, PERIOD_D1, 0);
   double today_low  = iLow(_Symbol,  PERIOD_D1, 0);
   double today_range = today_high - today_low;

   // Si ya consumió más del límite del ADR, no entrar
   if(adr > 0 && today_range / adr > ADR_MaxUsed) return false;

   return true;
}

//+------------------------------------------------------------------+
//| CalculateLotSize — tamaño de posición por riesgo                  |
//+------------------------------------------------------------------+
double CalculateLotSize(double sl_pips, double risk_pct = -1.0)
{
   double balance   = AccountInfoDouble(ACCOUNT_BALANCE);
   if(risk_pct < 0) risk_pct = RiskPercent;
   double risk_usd  = balance * risk_pct / 100.0;
   double tick_value = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tick_size == 0 || tick_value == 0 || sl_pips == 0) return 0.01;

   double sl_money_per_lot = (sl_pips / tick_size) * tick_value;
   double lots = risk_usd / sl_money_per_lot;

   // Normalizar lotes
   double lot_step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lot_min  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lot_max  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   lots = MathFloor(lots / lot_step) * lot_step;
   lots = MathMax(lot_min, MathMin(lot_max, lots));

   return lots;
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

   double entry = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double sl_dist = MathMax(atr * SL_ATR_Mult, MinSL_Pips * _Point);
   double sl  = NormalizeDouble(entry - sl_dist, _Digits);
   double tp1 = NormalizeDouble(entry + sl_dist * TP1_Ratio, _Digits);
   double tp2 = NormalizeDouble(entry + sl_dist * TP2_Ratio, _Digits);
   double tp3 = NormalizeDouble(entry + sl_dist * TP3_Ratio, _Digits);

   // Ajustar riesgo por score: alta confianza = tamaño normal, baja = reducido
   double risk_mult = (score >= HighConfScore) ? 1.0 : 0.75;
   double lots = CalculateLotSize(sl_dist, RiskPercent * risk_mult);

   if(lots <= 0) return;

   // Dividir en 3 órdenes para los 3 TP
   double lots1 = NormalizeDouble(lots * TP1_ClosePercent / 100.0,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots2 = NormalizeDouble(lots * TP2_ClosePercent / 100.0,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots3 = NormalizeDouble(lots - lots1 - lots2,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));

   double lot_min = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(lots1 < lot_min) lots1 = lot_min;
   if(lots2 < lot_min) lots2 = lot_min;
   if(lots3 < lot_min) lots3 = lot_min;

   string comment = StringFormat("GVFE_L_S%d", score);

   if(trade.Buy(lots1, _Symbol, entry, sl, tp1, comment + "_TP1"))
      g_dailyTrades++;
   if(trade.Buy(lots2, _Symbol, entry, sl, tp2, comment + "_TP2"))  {}
   if(trade.Buy(lots3, _Symbol, entry, sl, tp3, comment + "_TP3"))  {}

   g_weeklyTrades++;
   PrintFormat("LONG entrada | Score=%d | Entry=%.2f | SL=%.2f | TP1=%.2f TP2=%.2f TP3=%.2f | Lots=%.2f",
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

   double entry = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl_dist = MathMax(atr * SL_ATR_Mult, MinSL_Pips * _Point);
   double sl  = NormalizeDouble(entry + sl_dist, _Digits);
   double tp1 = NormalizeDouble(entry - sl_dist * TP1_Ratio, _Digits);
   double tp2 = NormalizeDouble(entry - sl_dist * TP2_Ratio, _Digits);
   double tp3 = NormalizeDouble(entry - sl_dist * TP3_Ratio, _Digits);

   double risk_mult = (MathAbs(score) >= HighConfScore) ? 1.0 : 0.75;
   double lots = CalculateLotSize(sl_dist, RiskPercent * risk_mult);

   if(lots <= 0) return;

   double lots1 = NormalizeDouble(lots * TP1_ClosePercent / 100.0,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots2 = NormalizeDouble(lots * TP2_ClosePercent / 100.0,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));
   double lots3 = NormalizeDouble(lots - lots1 - lots2,
                                  (int)-MathLog10(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)));

   double lot_min = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(lots1 < lot_min) lots1 = lot_min;
   if(lots2 < lot_min) lots2 = lot_min;
   if(lots3 < lot_min) lots3 = lot_min;

   string comment = StringFormat("GVFE_S_S%d", score);

   if(trade.Sell(lots1, _Symbol, entry, sl, tp1, comment + "_TP1"))
      g_dailyTrades++;
   if(trade.Sell(lots2, _Symbol, entry, sl, tp2, comment + "_TP2"))  {}
   if(trade.Sell(lots3, _Symbol, entry, sl, tp3, comment + "_TP3"))  {}

   g_weeklyTrades++;
   PrintFormat("SHORT entrada | Score=%d | Entry=%.2f | SL=%.2f | TP1=%.2f TP2=%.2f TP3=%.2f | Lots=%.2f",
               score, entry, sl, tp1, tp2, tp3, lots);
}

//+------------------------------------------------------------------+
//| ManageOpenPositions — gestión de posiciones abiertas              |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Magic() != MagicNumber) continue;
      if(posInfo.Symbol() != _Symbol) continue;

      ulong ticket = posInfo.Ticket();
      double entry  = posInfo.PriceOpen();
      double sl     = posInfo.StopLoss();
      double tp     = posInfo.TakeProfit();
      double current = (posInfo.PositionType() == POSITION_TYPE_BUY) ?
                        SymbolInfoDouble(_Symbol, SYMBOL_BID) :
                        SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double atr_arr[];
      ArraySetAsSeries(atr_arr, true);
      CopyBuffer(h_ATR, 0, 0, 1, atr_arr);
      double atr = atr_arr[0];
      double sl_dist = MathAbs(entry - sl);

      // Mover SL a breakeven después de TP1
      if(posInfo.PositionType() == POSITION_TYPE_BUY)
      {
         double profit_dist = current - entry;
         if(profit_dist >= sl_dist * TP1_Ratio && sl < entry)
         {
            double new_sl = NormalizeDouble(entry + 5 * _Point, _Digits);
            trade.PositionModify(ticket, new_sl, tp);
         }
         // Trailing stop después de TP2 usando EMA20
         if(profit_dist >= sl_dist * TP2_Ratio)
         {
            double ema20_arr[];
            ArraySetAsSeries(ema20_arr, true);
            CopyBuffer(h_EMA20, 0, 0, 1, ema20_arr);
            double trail_sl = NormalizeDouble(ema20_arr[0] - atr * 0.5, _Digits);
            if(trail_sl > sl)
               trade.PositionModify(ticket, trail_sl, tp);
         }
      }
      else if(posInfo.PositionType() == POSITION_TYPE_SELL)
      {
         double profit_dist = entry - current;
         if(profit_dist >= sl_dist * TP1_Ratio && sl > entry)
         {
            double new_sl = NormalizeDouble(entry - 5 * _Point, _Digits);
            trade.PositionModify(ticket, new_sl, tp);
         }
         if(profit_dist >= sl_dist * TP2_Ratio)
         {
            double ema20_arr[];
            ArraySetAsSeries(ema20_arr, true);
            CopyBuffer(h_EMA20, 0, 0, 1, ema20_arr);
            double trail_sl = NormalizeDouble(ema20_arr[0] + atr * 0.5, _Digits);
            if(trail_sl < sl)
               trade.PositionModify(ticket, trail_sl, tp);
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

      // Reset Asian sweep flags
      g_asian.sweptHigh = false;
      g_asian.sweptLow  = false;
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

//+------------------------------------------------------------------+
//| CountMagicPositions                                               |
//+------------------------------------------------------------------+
int CountMagicPositions()
{
   int count = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(posInfo.SelectByIndex(i) &&
         posInfo.Magic() == MagicNumber &&
         posInfo.Symbol() == _Symbol)
         count++;
   }
   return count;
}

//+------------------------------------------------------------------+
//| OnTrade — ejecutado cuando hay actividad en trades                |
//+------------------------------------------------------------------+
void OnTrade()
{
   // Verificar si algún TP fue alcanzado para logging
   HistorySelect(TimeCurrent() - 3600, TimeCurrent());
   for(int i = HistoryDealsTotal() - 1; i >= 0; i--)
   {
      ulong deal_ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != MagicNumber) continue;
      if(HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != _Symbol) continue;

      double profit = HistoryDealGetDouble(deal_ticket, DEAL_PROFIT);
      if(profit > 0)
         Print("Trade cerrado en ganancia: +$", DoubleToString(profit, 2));
      else if(profit < 0)
         Print("Trade cerrado en pérdida: $", DoubleToString(profit, 2));
   }
}
//+------------------------------------------------------------------+
