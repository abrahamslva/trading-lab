//+------------------------------------------------------------------+
//| MACD_Ribbon_1H.mq5                                              |
//| MACD Bands + Ribbon FONDEO PRO                                  |
//| Adjuntar en grafico XAUUSD H1  |  Magic: 300001                 |
//| BUGS CORREGIDOS v3:                                              |
//|  - Sin emojis. Sin INIT_FAILED. PERIOD_CURRENT.                 |
//|  - iMACD nativo (no calculo manual). Handles lazy.              |
//|  - Sin variables globales no usadas. Arrays bien dimensionados.  |
//+------------------------------------------------------------------+
#property copyright "FondeoProSuite"
#property version   "3.00"
#property strict

//--------------------------------------------------------------------------
// IDENTIFICACION
//--------------------------------------------------------------------------
#define MAGIC_NUMBER   300001
#define EA_NAME        "MACD Ribbon 1H"

//--------------------------------------------------------------------------
// CONSTANTES DE RIESGO
//--------------------------------------------------------------------------
#define RISK_PCT       0.00166
#define MAX_RISK_USD   170.0

//--------------------------------------------------------------------------
// INPUTS
//--------------------------------------------------------------------------
input group "=== MACD ==="
input int    InpFast    = 21;   // EMA Rapida MACD
input int    InpSlow    = 35;   // EMA Lenta MACD
input int    InpSignal  = 14;   // EMA Senal MACD

input group "=== Ribbon ==="
input int    InpRibbLen = 14;   // EMA del Ribbon
input int    InpRibbSmth= 6;    // SMA del Ribbon (suavizado)

input group "=== Riesgo ==="
input int    InpSwingLen= 10;   // Barras para calcular SL swing low
input double InpLeverage= 1.0;  // Apalancamiento (1 = sin)

//--------------------------------------------------------------------------
// HANDLES - INVALID_HANDLE hasta que se creen en OnTick
//--------------------------------------------------------------------------
int g_hMACD  = INVALID_HANDLE;   // iMACD: buf0=MACDline, buf1=Senal
int g_hRibb  = INVALID_HANDLE;   // iMA EMA para el Ribbon
int g_hATR   = INVALID_HANDLE;   // iATR para filtro y SL

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
   if(g_hMACD == INVALID_HANDLE)
      g_hMACD = iMACD(_Symbol, PERIOD_CURRENT, InpFast, InpSlow, InpSignal, PRICE_CLOSE);

   if(g_hRibb == INVALID_HANDLE)
      g_hRibb = iMA(_Symbol, PERIOD_CURRENT, InpRibbLen, 0, MODE_EMA, PRICE_CLOSE);

   if(g_hATR == INVALID_HANDLE)
      g_hATR = iATR(_Symbol, PERIOD_CURRENT, 14);

   bool ok = (g_hMACD != INVALID_HANDLE &&
              g_hRibb != INVALID_HANDLE &&
              g_hATR  != INVALID_HANDLE);

   if(!ok) Print(EA_NAME, " Handles no listos aun");
   return ok;
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
      Print(EA_NAME, " BLOQUEO: 3 perdidas");
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
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_hMACD != INVALID_HANDLE) { IndicatorRelease(g_hMACD); g_hMACD = INVALID_HANDLE; }
   if(g_hRibb != INVALID_HANDLE) { IndicatorRelease(g_hRibb); g_hRibb = INVALID_HANDLE; }
   if(g_hATR  != INVALID_HANDLE) { IndicatorRelease(g_hATR);  g_hATR  = INVALID_HANDLE; }
   Comment("");
   Print(EA_NAME, " detenido");
}

void OnTick()
{
   // *** DASHBOARD PRIMERO ***
   Dashboard();

   // Crear handles lazy si faltan
   if(!EnsureHandles()) return;

   // Solo logica en barra nueva
   static datetime s_lastBar = 0;
   datetime curBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBarTime == s_lastBar) return;
   s_lastBar = curBarTime;

   Print(EA_NAME, " Nueva barra: ", TimeToString(curBarTime));

   ResetDaily();
   ApplyStrikes();

   //--- MACD
   // iMACD buffer 0 = MACD line (fast EMA - slow EMA)
   // iMACD buffer 1 = Signal line (EMA of MACD line)
   // Necesitamos barras 1 y 2 para detectar crossover → copiar 3 valores desde shift=1
   double macdLine[3], signalLine[3];
   if(CopyBuffer(g_hMACD, 0, 1, 3, macdLine)   < 3) { Print(EA_NAME, " MACD line no listo"); return; }
   if(CopyBuffer(g_hMACD, 1, 1, 3, signalLine) < 3) { Print(EA_NAME, " Signal no listo"); return; }

   // Los arrays de CopyBuffer se llenan en orden CRONOLOGICO:
   //   [0] = dato en shift=1 (barra mas reciente cerrada)
   //   [1] = dato en shift=2
   //   [2] = dato en shift=3
   double macd1   = macdLine[0],   macd2   = macdLine[1];
   double signal1 = signalLine[0], signal2 = signalLine[1];

   // bull_dot = crossover(macdLine, signalLine) en barra[1]
   // En barra[1]: macd1 >= signal1    En barra[2]: macd2 < signal2
   bool bullDot = (macd1 >= signal1) && (macd2 < signal2);

   //--- Ribbon: EMA(close, 14) > SMA(EMA(close,14), 6)
   // Copiar los ultimos InpRibbSmth valores de EMA para calcular su SMA
   double ribbArr[];
   ArrayResize(ribbArr, InpRibbSmth + 2);
   if(CopyBuffer(g_hRibb, 0, 1, InpRibbSmth, ribbArr) < InpRibbSmth)
   { Print(EA_NAME, " Ribbon no listo"); return; }

   double trBase    = ribbArr[0];  // EMA en barra[1]
   double smoothSum = 0.0;
   for(int k = 0; k < InpRibbSmth; k++) smoothSum += ribbArr[k];
   double trSmooth  = smoothSum / InpRibbSmth;
   bool ribbonGreen = trBase > trSmooth;

   //--- Estructura: close[1] > close[2]
   bool estructura = iClose(_Symbol, PERIOD_CURRENT, 1) > iClose(_Symbol, PERIOD_CURRENT, 2);

   //--- Filtro volatilidad: ATR[1] > SMA(ATR, 20)
   double atrArr[];
   ArrayResize(atrArr, 22);
   if(CopyBuffer(g_hATR, 0, 1, 22, atrArr) < 22) { Print(EA_NAME, " ATR no listo"); return; }
   double atrNow = atrArr[0];
   double atrSma = 0.0;
   for(int k = 0; k < 20; k++) atrSma += atrArr[k];
   atrSma /= 20.0;
   bool filtroVol = atrNow > atrSma;

   bool compra = bullDot && ribbonGreen && estructura && filtroVol;

   Print(EA_NAME,
         " bullDot=", bullDot,
         " ribbon=", ribbonGreen,
         " estr=", estructura,
         " vol=", filtroVol,
         " compra=", compra,
         " allowed=", g_allowed);

   //--- Abrir posicion
   if(compra && g_allowed && PositionsTotal() == 0)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      // SL = minimo swing de las ultimas InpSwingLen barras cerradas
      double slVal = DBL_MAX;
      for(int i = 1; i <= InpSwingLen; i++)
         slVal = MathMin(slVal, iLow(_Symbol, PERIOD_CURRENT, i));

      double riesgo = ask - slVal;
      if(riesgo <= 0.0) riesgo = atrNow;  // Fallback: usar ATR

      // RR dinamico segun ATR vs su media de 50 barras
      double atrArr50[];
      ArrayResize(atrArr50, 52);
      double rr = 1.3;
      if(CopyBuffer(g_hATR, 0, 1, 52, atrArr50) >= 52)
      {
         double atr50sum = 0.0;
         for(int k = 0; k < 50; k++) atr50sum += atrArr50[k];
         double atr50 = atr50sum / 50.0;
         rr = (atrNow > atr50) ? 1.8 : 1.3;
      }

      double tp  = NormalizeDouble(ask + riesgo * rr, _Digits);
      double sl  = NormalizeDouble(slVal, _Digits);
      double lot = CalcLots(riesgo);
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
         Print(EA_NAME, " ORDEN ENVIADA lot=", lot, " SL=", sl, " TP=", tp, " RR=", rr);
      else
         Print(EA_NAME, " ERROR OrderSend: ", GetLastError(), " retcode=", res.retcode);
   }

   //--- Break Even: mover SL a precio de entrada cuando precio = entrada + riesgo inicial
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) != _Symbol ||
         PositionGetInteger(POSITION_MAGIC) != MAGIC_NUMBER) continue;

      ulong  tk      = (ulong)PositionGetInteger(POSITION_TICKET);
      double entry   = PositionGetDouble(POSITION_PRICE_OPEN);
      double posSL   = PositionGetDouble(POSITION_SL);
      double posTP   = PositionGetDouble(POSITION_TP);
      double bid     = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double riskIni = entry - posSL;

      if(riskIni > 0.0 && bid >= entry + riskIni && posSL < entry)
         SetSLTP(tk, entry, posTP);
   }

   Dashboard();
}
