//+------------------------------------------------------------------+
//| Ruptura_Momento_3H.mq5                                          |
//| Ruptura Momento PRO v3 - XAU/USD                                |
//| Adjuntar en grafico XAUUSD 3H  |  Magic: 200005                 |
//| BUGS CORREGIDOS v3:                                              |
//|  - Sin emojis. Sin INIT_FAILED. PERIOD_CURRENT.                 |
//|  - SuperTrend correcto con estado acumulado por historia.        |
//|  - Handles con inicializacion lazy (no falla en OnInit).         |
//+------------------------------------------------------------------+
#property copyright "FondeoProSuite"
#property version   "3.00"
#property strict

//--------------------------------------------------------------------------
// IDENTIFICACION
//--------------------------------------------------------------------------
#define MAGIC_NUMBER   200005
#define EA_NAME        "Ruptura PRO 3H"

//--------------------------------------------------------------------------
// CONSTANTES DE RIESGO
//--------------------------------------------------------------------------
#define RISK_PCT       0.00166
#define MAX_RISK_USD   170.0

//--------------------------------------------------------------------------
// INPUTS
//--------------------------------------------------------------------------
input group "=== Indicadores Base ==="
input int    InpAdxLen    = 15;    // Periodos ADX
input int    InpAdxThresh = 20;    // Umbral ADX minimo
input int    InpDcLen     = 21;    // Donchian Canal principal
input double InpStFactor  = 5.0;   // Factor SuperTrend
input int    InpStLen     = 17;    // Periodos ATR para SuperTrend

input group "=== Gestion de Riesgo ==="
input double InpRR        = 2.2;   // Risk:Reward ratio
input double InpMinRange  = 0.5;   // Rango minimo de barra (%)

input group "=== Mejoras v3 ==="
input bool   InpUseSession = true;  // Filtrar sesion muerta 22:00-07:00 UTC
input bool   InpUseRsi     = true;  // Filtro RSI minimo
input int    InpRsiLen     = 14;    // Periodos RSI
input int    InpRsiFloor   = 45;    // RSI minimo para entrar
input bool   InpUseFastDC  = true;  // Donchian rapido continuacion
input int    InpDcFastLen  = 10;    // Periodos Donchian rapido

input group "=== Riesgo ==="
input double InpLeverage   = 1.0;  // Apalancamiento (1 = sin)

//--------------------------------------------------------------------------
// HANDLES - Inicializados a INVALID_HANDLE (no a 0)
//--------------------------------------------------------------------------
int g_hADX = INVALID_HANDLE;
int g_hRSI = INVALID_HANDLE;
int g_hATR = INVALID_HANDLE;

//--------------------------------------------------------------------------
// GLOBALES
//--------------------------------------------------------------------------
int      g_losses  = 0;
bool     g_allowed = true;
datetime g_day     = 0;

//--------------------------------------------------------------------------
// INICIALIZACION LAZY DE HANDLES
//--------------------------------------------------------------------------
bool EnsureHandles()
{
   if(g_hADX == INVALID_HANDLE)
      g_hADX = iADX(_Symbol, PERIOD_CURRENT, InpAdxLen);

   if(g_hRSI == INVALID_HANDLE)
      g_hRSI = iRSI(_Symbol, PERIOD_CURRENT, InpRsiLen, PRICE_CLOSE);

   if(g_hATR == INVALID_HANDLE)
      g_hATR = iATR(_Symbol, PERIOD_CURRENT, InpStLen);

   bool ok = (g_hADX != INVALID_HANDLE &&
              g_hRSI != INVALID_HANDLE &&
              g_hATR != INVALID_HANDLE);

   if(!ok) Print(EA_NAME, " Handles no disponibles aun (normal en inicio)");
   return ok;
}

//--------------------------------------------------------------------------
// SUPERTREND CORRECTO - Calculo sobre historia completa
// Logica identica al Pine Script ta.supertrend(factor, len)
// Retorna true si tendencia es alcista (direction < 0 en Pine)
// stLine = nivel del SuperTrend en barra[1] (uso como SL)
//--------------------------------------------------------------------------
bool GetSuperTrend(double &stLine)
{
   if(g_hATR == INVALID_HANDLE) { stLine = 0; return false; }

   // Warmup: necesitamos suficientes barras para que el ATR converja
   int warmup = MathMax(InpStLen * 6, 120);
   int avail  = (int)iBars(_Symbol, PERIOD_CURRENT) - 2;
   int N      = MathMin(warmup, avail);

   if(N < InpStLen + 10)
   {
      Print(EA_NAME, " SuperTrend: barras insuf. (", N, ")");
      stLine = 0;
      return false;
   }

   // Copiar ATR: shifts 1..N → atrBuf[0]=shift1, atrBuf[N-1]=shiftN
   double atrBuf[];
   ArrayResize(atrBuf, N + 1);
   if(CopyBuffer(g_hATR, 0, 1, N, atrBuf) < N)
   {
      Print(EA_NAME, " SuperTrend: CopyBuffer ATR fallo");
      stLine = 0;
      return false;
   }
   // Convenio: atrBuf[k] = ATR en shift (k+1)
   // Para shift s → atrBuf[s-1]

   double upperBand = 0.0;
   double lowerBand = 0.0;
   int    trend     = 0;   // 0=sin init, 1=bearish, -1=bullish
   double prevClose = 0.0;

   // Iterar de barra mas antigua (shift=N) a mas reciente (shift=1)
   for(int s = N; s >= 1; s--)
   {
      double H   = iHigh (_Symbol, PERIOD_CURRENT, s);
      double L   = iLow  (_Symbol, PERIOD_CURRENT, s);
      double C   = iClose(_Symbol, PERIOD_CURRENT, s);
      double atr = atrBuf[s - 1];  // ATR en shift s
      double hl2 = (H + L) * 0.5;

      double rawUpper = hl2 + InpStFactor * atr;
      double rawLower = hl2 - InpStFactor * atr;

      if(trend == 0)
      {
         // Inicializacion: primera barra
         upperBand = rawUpper;
         lowerBand = rawLower;
         trend     = (C > lowerBand) ? -1 : 1;
      }
      else
      {
         // Ajuste de bandas (solo se mueven en una direccion)
         // Upper: solo baja, y se reinicia si prevClose rompio hacia arriba
         if(rawUpper < upperBand || prevClose > upperBand)
            upperBand = rawUpper;

         // Lower: solo sube, y se reinicia si prevClose rompio hacia abajo
         if(rawLower > lowerBand || prevClose < lowerBand)
            lowerBand = rawLower;

         // Cambio de tendencia
         if(C > upperBand)      trend = -1;  // Precio rompe upper → bullish
         else if(C < lowerBand) trend = 1;   // Precio rompe lower → bearish
         // else: tendencia se mantiene
      }
      prevClose = C;
   }

   // Resultado en barra[1] (ya calculado al final del loop con s=1)
   stLine = (trend == -1) ? lowerBand : upperBand;
   return (trend == -1);  // true = bullish, coincide con st_direction<0 en Pine
}

//--------------------------------------------------------------------------
// DONCHIAN CHANNEL - Maximo/minimo de N barras cerradas
//--------------------------------------------------------------------------
double DcHighest(int len, int startShift = 1)
{
   double hi = -DBL_MAX;
   for(int i = startShift; i < startShift + len; i++)
      hi = MathMax(hi, iHigh(_Symbol, PERIOD_CURRENT, i));
   return hi;
}

double DcLowest(int len, int startShift = 1)
{
   double lo = DBL_MAX;
   for(int i = startShift; i < startShift + len; i++)
      lo = MathMin(lo, iLow(_Symbol, PERIOD_CURRENT, i));
   return lo;
}

//--------------------------------------------------------------------------
// GESTION DE RIESGO
//--------------------------------------------------------------------------
double CalcLots(double slDist)
{
   if(slDist <= 0.0) return 0.0;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk   = MathMin(equity * RISK_PCT * InpLeverage, MAX_RISK_USD);

   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0.0 || ts <= 0.0) { Print(EA_NAME, " tv/ts=0"); return 0.0; }

   double lots   = risk / (slDist / ts * tv);
   double lotMin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotMax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStp = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lots = MathFloor(lots / lotStp) * lotStp;
   return MathMax(lotMin, MathMin(lotMax, lots));
}

//--------------------------------------------------------------------------
// PROTECCION DIARIA - 3 STRIKES
//--------------------------------------------------------------------------
void ResetDaily()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",
                                               dt.year, dt.mon, dt.day));
   if(today == g_day) return;
   g_day = today; g_losses = 0; g_allowed = true;
   Print(EA_NAME, " Reset diario");
}

void CountDailyLosses()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",
                                               dt.year, dt.mon, dt.day));
   HistorySelect(today, TimeCurrent());
   int n = 0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong tk = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(tk, DEAL_MAGIC) != MAGIC_NUMBER) continue;
      if(HistoryDealGetInteger(tk, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;
      double pnl = HistoryDealGetDouble(tk, DEAL_PROFIT)
                 + HistoryDealGetDouble(tk, DEAL_SWAP)
                 + HistoryDealGetDouble(tk, DEAL_COMMISSION);
      if(pnl < 0.0) n++;
   }
   g_losses = n;
}

void ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;
   MqlTradeRequest req; MqlTradeResult res;
   ZeroMemory(req); ZeroMemory(res);
   req.action    = TRADE_ACTION_DEAL;
   req.symbol    = _Symbol;
   req.volume    = PositionGetDouble(POSITION_VOLUME);
   req.type      = ORDER_TYPE_SELL;
   req.price     = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   req.deviation = 50;
   req.magic     = MAGIC_NUMBER;
   req.position  = ticket;
   if(!OrderSend(req, res)) Print(EA_NAME, " ClosePos err: ", GetLastError());
}

void SetSLTP(ulong ticket, double sl, double tp)
{
   if(!PositionSelectByTicket(ticket)) return;
   MqlTradeRequest req; MqlTradeResult res;
   ZeroMemory(req); ZeroMemory(res);
   req.action   = TRADE_ACTION_SLTP;
   req.symbol   = _Symbol;
   req.sl       = sl;
   req.tp       = tp;
   req.position = ticket;
   OrderSend(req, res);
}

void ApplyStrikes()
{
   CountDailyLosses();
   if(g_losses >= 3)
   {
      g_allowed = false;
      Print(EA_NAME, " BLOQUEO total: 3 perdidas");
      for(int i = PositionsTotal()-1; i >= 0; i--)
         if(PositionGetSymbol(i)==_Symbol &&
            PositionGetInteger(POSITION_MAGIC)==MAGIC_NUMBER)
            ClosePosition((ulong)PositionGetInteger(POSITION_TICKET));
      return;
   }
   if(g_losses == 2)
   {
      g_allowed = false;
      Print(EA_NAME, " ALERTA: 2a perdida");
      for(int i = PositionsTotal()-1; i >= 0; i--)
      {
         if(PositionGetSymbol(i)!=_Symbol ||
            PositionGetInteger(POSITION_MAGIC)!=MAGIC_NUMBER) continue;
         ulong  tk    = (ulong)PositionGetInteger(POSITION_TICKET);
         double entry = PositionGetDouble(POSITION_PRICE_OPEN);
         double tp    = PositionGetDouble(POSITION_TP);
         if(PositionGetDouble(POSITION_PROFIT) >= 0.0) SetSLTP(tk, entry, tp);
         else ClosePosition(tk);
      }
   }
}

//--------------------------------------------------------------------------
// DASHBOARD - Solo ASCII
//--------------------------------------------------------------------------
void Dashboard()
{
   double eq   = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk = MathMin(eq * RISK_PCT * InpLeverage, MAX_RISK_USD);
   string est  = g_allowed ? "[ACTIVO]" : "[BLOQUEADO - Drawdown]";

   Comment(EA_NAME + " | " + _Symbol + " | Losses: " +
           IntegerToString(g_losses) + "/3" +
           "\nEstado: " + est +
           "\nRiesgo/Trade: $" + DoubleToString(risk, 2) +
           "\nApalancamiento: x" + DoubleToString(InpLeverage, 1) +
           "\nEquity: $" + DoubleToString(eq, 2));
}

//--------------------------------------------------------------------------
// EVENTOS
//--------------------------------------------------------------------------
int OnInit()
{
   Print("=== ", EA_NAME, " INICIADO ===");
   Print("   Symbol : ", _Symbol);
   Print("   Magic  : ", MAGIC_NUMBER);
   Print("   Periodo: ", Period());
   Comment(EA_NAME + " iniciando...");
   return INIT_SUCCEEDED;  // SIEMPRE - handles se crean lazy en OnTick
}

void OnDeinit(const int reason)
{
   if(g_hADX != INVALID_HANDLE) { IndicatorRelease(g_hADX); g_hADX = INVALID_HANDLE; }
   if(g_hRSI != INVALID_HANDLE) { IndicatorRelease(g_hRSI); g_hRSI = INVALID_HANDLE; }
   if(g_hATR != INVALID_HANDLE) { IndicatorRelease(g_hATR); g_hATR = INVALID_HANDLE; }
   Comment("");
   Print(EA_NAME, " detenido");
}

void OnTick()
{
   // *** DASHBOARD PRIMERO - visible inmediatamente ***
   Dashboard();

   // Crear handles si aun no existen (lazy init)
   if(!EnsureHandles()) return;

   // Logica solo en barra nueva cerrada
   static datetime s_lastBar = 0;
   datetime curBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBarTime == s_lastBar) return;
   s_lastBar = curBarTime;

   Print(EA_NAME, " Nueva barra: ", TimeToString(curBarTime));

   ResetDaily();
   ApplyStrikes();

   //--- Leer ADX (shift=1 = barra cerrada)
   double adxBuf[3];
   if(CopyBuffer(g_hADX, 0, 1, 3, adxBuf) < 3)
   { Print(EA_NAME, " ADX buffer no listo"); return; }
   double adxVal = adxBuf[0];

   //--- Leer RSI
   double rsiBuf[2];
   if(CopyBuffer(g_hRSI, 0, 1, 2, rsiBuf) < 2)
   { Print(EA_NAME, " RSI buffer no listo"); return; }
   double rsiVal = rsiBuf[0];

   //--- SuperTrend
   double stLevel = 0.0;
   bool   stBull  = GetSuperTrend(stLevel);

   Print(EA_NAME, " ADX=", DoubleToString(adxVal,1),
         " RSI=", DoubleToString(rsiVal,1),
         " ST_Bull=", stBull,
         " ST_Lvl=", DoubleToString(stLevel,2));

   //--- Donchian
   double dcHigh     = DcHighest(InpDcLen, 1);
   double dcLow      = DcLowest (InpDcLen, 1);
   double dcFastHigh = InpUseFastDC ? DcHighest(InpDcFastLen, 1) : dcHigh;
   double dcMid      = (dcHigh + dcLow) * 0.5;

   double h1 = iHigh (_Symbol, PERIOD_CURRENT, 1);
   double h2 = iHigh (_Symbol, PERIOD_CURRENT, 2);
   double c1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double c2 = iClose(_Symbol, PERIOD_CURRENT, 2);
   double l1 = iLow  (_Symbol, PERIOD_CURRENT, 1);

   //--- Filtros
   bool rangeOk   = ((h1 - l1) / c1) > (InpMinRange / 100.0);
   bool momentumOk= adxVal > InpAdxThresh;
   bool trendLong = stBull;

   // Sesion UTC
   MqlDateTime dtg; TimeToStruct(TimeGMT(), dtg);
   bool inSession = !InpUseSession || (dtg.hour >= 7 && dtg.hour < 22);

   // RSI
   bool rsiOk = !InpUseRsi || (rsiVal > InpRsiFloor);

   // Crossovers Donchian (barra 1 rompe maximo de barras 2..N)
   bool crossDC    = (h1 > dcHigh)     && (h2 <= dcHigh);
   bool crossFast  = (h1 > dcFastHigh) && (h2 <= dcFastHigh);
   bool pullback   = (c1 > dcHigh)     && (c2 <= dcHigh) && trendLong;

   // Condicion base (Pine: breakout_long or pullback_long)
   bool baseLong      = rangeOk && momentumOk && trendLong && (crossDC || pullback);
   // Condicion rapida (continuacion)
   bool fastBreakLong = InpUseFastDC && crossFast && !crossDC &&
                        c1 > dcMid && trendLong && momentumOk && rangeOk;

   bool longCond = (baseLong || fastBreakLong) && inSession && rsiOk;

   Print(EA_NAME, " rangeOk=", rangeOk, " momOk=", momentumOk,
         " trend=", trendLong, " session=", inSession,
         " rsiOk=", rsiOk, " crossDC=", crossDC,
         " longCond=", longCond, " allowed=", g_allowed);

   //--- Abrir posicion
   if(longCond && g_allowed && PositionsTotal() == 0)
   {
      double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double slDist= MathAbs(ask - stLevel);
      if(slDist <= 0.0 || stLevel <= 0.0)
      { Print(EA_NAME, " SL invalido (stLevel=", stLevel, ")"); return; }

      double sl  = NormalizeDouble(stLevel, _Digits);
      double tp  = NormalizeDouble(ask + slDist * InpRR, _Digits);
      double lot = CalcLots(slDist);
      if(lot <= 0.0) { Print(EA_NAME, " lot=0"); return; }

      MqlTradeRequest req; MqlTradeResult res;
      ZeroMemory(req); ZeroMemory(res);
      req.action    = TRADE_ACTION_DEAL;
      req.symbol    = _Symbol;
      req.volume    = lot;
      req.type      = ORDER_TYPE_BUY;
      req.price     = ask;
      req.sl        = sl;
      req.tp        = tp;
      req.deviation = 50;
      req.magic     = MAGIC_NUMBER;
      req.comment   = EA_NAME;

      if(OrderSend(req, res))
         Print(EA_NAME, " ORDEN ENVIADA lot=", lot, " SL=", sl, " TP=", tp);
      else
         Print(EA_NAME, " ERROR OrderSend: ", GetLastError(), " retcode=", res.retcode);
   }

   //--- Trailing SuperTrend (sube el SL si ST sube)
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) != _Symbol ||
         PositionGetInteger(POSITION_MAGIC) != MAGIC_NUMBER) continue;

      ulong  tk  = (ulong)PositionGetInteger(POSITION_TICKET);
      double csl = PositionGetDouble(POSITION_SL);
      double ctp = PositionGetDouble(POSITION_TP);

      if(stBull && stLevel > csl && stLevel > 0.0)
         SetSLTP(tk, NormalizeDouble(stLevel, _Digits), ctp);
   }

   Dashboard();
}
