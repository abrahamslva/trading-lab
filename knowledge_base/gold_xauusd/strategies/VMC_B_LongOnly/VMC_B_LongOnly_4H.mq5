//+------------------------------------------------------------------+
//| VMC_B_LongOnly_4H.mq5                                           |
//| VuManChu Cipher B - Long Only                                    |
//| Adjuntar en grafico XAUUSD 4H  |  Magic: 100004                 |
//| BUGS CORREGIDOS v3:                                              |
//|  - Sin emojis ni caracteres Unicode especiales                   |
//|  - Siempre INIT_SUCCEEDED (sin INIT_FAILED por handles)          |
//|  - Usa PERIOD_CURRENT (chart define el timeframe)                |
//|  - Comment() es la primera instruccion de OnTick()               |
//+------------------------------------------------------------------+
#property copyright "FondeoProSuite"
#property version   "3.00"
#property strict

//--------------------------------------------------------------------------
// IDENTIFICACION
//--------------------------------------------------------------------------
#define MAGIC_NUMBER   100004
#define EA_NAME        "VMC LongOnly 4H"

//--------------------------------------------------------------------------
// CONSTANTES DE RIESGO (no tocar)
//--------------------------------------------------------------------------
#define RISK_PCT       0.00166    // 0.166% del equity
#define MAX_RISK_USD   170.0      // Techo duro por trade en USD

//--------------------------------------------------------------------------
// INPUTS
//--------------------------------------------------------------------------
input group "=== WaveTrend ==="
input int    InpWtCh    = 9;     // WT Channel Length
input int    InpWtAvg   = 12;    // WT Average Length
input int    InpWtMa    = 3;     // WT MA Length
input int    InpOsLevel = -53;   // Nivel Oversold (ej -53)
input int    InpObLevel = 53;    // Nivel Overbought (ej 53)

input group "=== Estrategia ==="
input double InpSL_Pct  = 1.0;  // Stop Loss porcentaje (1.0 = 1%)
input double InpTP_Pct  = 2.0;  // Take Profit porcentaje (2.0 = 2%)

input group "=== Riesgo ==="
input double InpLeverage= 1.0;  // Apalancamiento (1 = sin apalancamiento)

//--------------------------------------------------------------------------
// GLOBALES - Proteccion diaria
//--------------------------------------------------------------------------
int      g_losses  = 0;
bool     g_allowed = true;
datetime g_day     = 0;

//--------------------------------------------------------------------------
// WAVETREND - Calculo correcto sobre historia
// Pine Script:
//   esa  = ta.ema(src, chLen)
//   de   = ta.ema(math.abs(src - esa), chLen)
//   ci   = (src - esa) / (0.015 * de)
//   wt1  = ta.ema(ci, avgLen)
//   wt2  = ta.sma(wt1, maLen)
//   buySignal = ta.cross(wt1,wt2) and wtCrossUp and wtOversold
//--------------------------------------------------------------------------
bool GetWaveTrend(double &wt1_out, double &wt2_out, bool &prevCrossed)
{
   int warmup = MathMax(InpWtCh * 5 + InpWtAvg * 5, 150);
   int avail  = (int)iBars(_Symbol, PERIOD_CURRENT) - 2;
   int N      = MathMin(warmup, avail);
   if(N < InpWtCh + InpWtAvg + InpWtMa + 20)
   {
      Print(EA_NAME, " [WT] Barras insuficientes: ", N);
      return false;
   }

   double kCh = 2.0 / (InpWtCh + 1);
   double kAv = 2.0 / (InpWtAvg + 1);

   // Arrays dinamicos para el calculo
   double esa[], de[], ci[], wt1[], wt2[];
   ArrayResize(esa, N + 1);
   ArrayResize(de,  N + 1);
   ArrayResize(ci,  N + 1);
   ArrayResize(wt1, N + 1);
   ArrayResize(wt2, N + 1);

   // Iterar de barra mas antigua (shift=N) a mas reciente (shift=1)
   // Indice del array: idx = N - shift  →  idx 0 = barra mas antigua
   for(int shift = N; shift >= 1; shift--)
   {
      int idx = N - shift;
      double h   = iHigh (_Symbol, PERIOD_CURRENT, shift);
      double l   = iLow  (_Symbol, PERIOD_CURRENT, shift);
      double c   = iClose(_Symbol, PERIOD_CURRENT, shift);
      double src = (h + l + c) / 3.0;  // HLC3

      if(idx == 0)
      {
         esa[0] = src;
         de [0] = 0.0;
         ci [0] = 0.0;
         wt1[0] = 0.0;
      }
      else
      {
         esa[idx] = src * kCh + esa[idx-1] * (1.0 - kCh);
         double d  = MathAbs(src - esa[idx]);
         de [idx]  = d * kCh + de[idx-1] * (1.0 - kCh);
         ci [idx]  = de[idx] > 1e-10 ? (src - esa[idx]) / (0.015 * de[idx]) : 0.0;
         wt1[idx]  = ci[idx] * kAv + wt1[idx-1] * (1.0 - kAv);
      }
   }

   // WT2 = SMA(wt1, InpWtMa) - solo necesitamos los ultimos indices
   // idx correspondiente a shift=1 → idx = N-1
   // idx correspondiente a shift=2 → idx = N-2
   int idx1 = N - 1;  // shift=1
   int idx2 = N - 2;  // shift=2

   if(idx1 < InpWtMa || idx2 < InpWtMa)
   {
      Print(EA_NAME, " [WT] idx insuficiente para SMA");
      return false;
   }

   // SMA de wt1 en shift=1
   double sum1 = 0.0;
   for(int k = 0; k < InpWtMa; k++) sum1 += wt1[idx1 - k];
   double wt2_1 = sum1 / InpWtMa;

   // SMA de wt1 en shift=2
   double sum2 = 0.0;
   for(int k = 0; k < InpWtMa; k++) sum2 += wt1[idx2 - k];
   double wt2_2 = sum2 / InpWtMa;

   wt1_out     = wt1[idx1];
   wt2_out     = wt2_1;
   // Hubo cruce en barra anterior (shift=2)?
   prevCrossed = (wt1[idx2] < wt2_2);  // En barra 2, wt1 estaba DEBAJO de wt2

   return true;
}

//--------------------------------------------------------------------------
// GESTION DE RIESGO
//--------------------------------------------------------------------------
double CalcLots(double slDistPoints)
{
   if(slDistPoints <= 0.0) return 0.0;

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk   = MathMin(equity * RISK_PCT * InpLeverage, MAX_RISK_USD);

   double tv = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double ts = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0.0 || ts <= 0.0) { Print(EA_NAME, " tv/ts=0, revisar simbolo"); return 0.0; }

   double lots   = risk / (slDistPoints / ts * tv);
   double lotMin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotMax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStp = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lots = MathFloor(lots / lotStp) * lotStp;
   lots = MathMax(lotMin, MathMin(lotMax, lots));
   return lots;
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
   g_day     = today;
   g_losses  = 0;
   g_allowed = true;
   Print(EA_NAME, " Reset diario - nuevo dia");
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
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != MAGIC_NUMBER) continue;
      if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT) continue;
      double pnl = HistoryDealGetDouble(ticket, DEAL_PROFIT)
                 + HistoryDealGetDouble(ticket, DEAL_SWAP)
                 + HistoryDealGetDouble(ticket, DEAL_COMMISSION);
      if(pnl < 0.0) n++;
   }
   g_losses = n;
}

void ClosePosition(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;
   MqlTradeRequest req;
   MqlTradeResult  res;
   ZeroMemory(req);
   ZeroMemory(res);
   req.action   = TRADE_ACTION_DEAL;
   req.symbol   = _Symbol;
   req.volume   = PositionGetDouble(POSITION_VOLUME);
   req.type     = ORDER_TYPE_SELL;
   req.price    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   req.deviation= 50;
   req.magic    = MAGIC_NUMBER;
   req.position = ticket;
   if(!OrderSend(req, res))
      Print(EA_NAME, " ClosePos error: ", GetLastError());
}

void SetBreakEven(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;
   MqlTradeRequest req;
   MqlTradeResult  res;
   ZeroMemory(req);
   ZeroMemory(res);
   req.action   = TRADE_ACTION_SLTP;
   req.symbol   = _Symbol;
   req.sl       = PositionGetDouble(POSITION_PRICE_OPEN);
   req.tp       = PositionGetDouble(POSITION_TP);
   req.position = ticket;
   OrderSend(req, res);
}

void ApplyStrikes()
{
   CountDailyLosses();

   if(g_losses >= 3)
   {
      g_allowed = false;
      Print(EA_NAME, " BLOQUEO: 3 perdidas en el dia");
      for(int i = PositionsTotal() - 1; i >= 0; i--)
         if(PositionGetSymbol(i) == _Symbol &&
            PositionGetInteger(POSITION_MAGIC) == MAGIC_NUMBER)
            ClosePosition((ulong)PositionGetInteger(POSITION_TICKET));
      return;
   }

   if(g_losses == 2)
   {
      g_allowed = false;
      Print(EA_NAME, " ALERTA: 2a perdida - gestionando posiciones");
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) != _Symbol ||
            PositionGetInteger(POSITION_MAGIC) != MAGIC_NUMBER) continue;
         ulong tk = (ulong)PositionGetInteger(POSITION_TICKET);
         if(PositionGetDouble(POSITION_PROFIT) >= 0.0) SetBreakEven(tk);
         else ClosePosition(tk);
      }
   }
}

//--------------------------------------------------------------------------
// DASHBOARD - Solo caracteres ASCII seguros
//--------------------------------------------------------------------------
void Dashboard()
{
   double eq   = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk = MathMin(eq * RISK_PCT * InpLeverage, MAX_RISK_USD);
   string estado = g_allowed ? "[ACTIVO]" : "[BLOQUEADO - Drawdown]";

   string msg = EA_NAME + " | " + _Symbol + " | Losses hoy: " +
                IntegerToString(g_losses) + "/3" +
                "\nEstado: " + estado +
                "\nRiesgo por trade: $" + DoubleToString(risk, 2) +
                "\nApalancamiento: x" + DoubleToString(InpLeverage, 1) +
                "\nEquity: $" + DoubleToString(eq, 2);
   Comment(msg);
}

//--------------------------------------------------------------------------
// EVENTOS
//--------------------------------------------------------------------------
int OnInit()
{
   // SIEMPRE retornar INIT_SUCCEEDED - nunca bloquear el EA en init
   Print("=== ", EA_NAME, " INICIADO ===");
   Print("   Symbol : ", _Symbol);
   Print("   Magic  : ", MAGIC_NUMBER);
   Print("   Periodo: ", Period());
   Print("   Equity : $", AccountInfoDouble(ACCOUNT_EQUITY));
   // Mostrar dashboard inmediatamente
   Comment(EA_NAME + " iniciando...");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   Comment("");
   Print(EA_NAME, " detenido. Razon: ", reason);
}

void OnTick()
{
   // *** DASHBOARD PRIMERO - siempre visible, sin condiciones ***
   Dashboard();

   // Logica solo en barra nueva para evitar recalculos innecesarios
   static datetime s_lastBar = 0;
   datetime curBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBarTime == s_lastBar) return;
   s_lastBar = curBarTime;

   Print(EA_NAME, " Nueva barra: ", TimeToString(curBarTime));

   // 1. Reset diario y conteo de perdidas
   ResetDaily();
   ApplyStrikes();

   // 2. Calcular WaveTrend
   double wt1 = 0.0, wt2 = 0.0;
   bool   prevCrossedBelow = false;
   if(!GetWaveTrend(wt1, wt2, prevCrossedBelow))
   {
      Print(EA_NAME, " WaveTrend no disponible todavia");
      return;
   }

   Print(EA_NAME, " WT1=", DoubleToString(wt1,2),
         " WT2=", DoubleToString(wt2,2),
         " prevBelow=", prevCrossedBelow);

   // 3. Senales
   // buySignal  = wt1 cruza wt2 hacia arriba (en barra 1) + wt2 <= osLevel
   //   wt1[1] >= wt2[1]  &&  wt1[2] < wt2[2]  &&  wt2[1] <= osLevel
   bool crossUpNow = (wt1 >= wt2) && prevCrossedBelow;
   bool isOversold = (wt2 <= (double)InpOsLevel);
   bool buySignal  = crossUpNow && isOversold;

   // redDot = wt1 cruza wt2 hacia abajo + wt2 >= obLevel
   bool crossDnNow = (wt1 < wt2) && !prevCrossedBelow;
   bool isOverbought=(wt2 >= (double)InpObLevel);
   bool redDot     = crossDnNow && isOverbought;

   Print(EA_NAME, " crossUp=", buySignal, " redDot=", redDot,
         " allowed=", g_allowed);

   // 4. Cerrar posiciones abiertas si hay senal roja
   if(redDot)
   {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
         if(PositionGetSymbol(i) == _Symbol &&
            PositionGetInteger(POSITION_MAGIC) == MAGIC_NUMBER)
            ClosePosition((ulong)PositionGetInteger(POSITION_TICKET));
   }

   // 5. Abrir nueva posicion long si hay senal y trading permitido
   if(buySignal && g_allowed && PositionsTotal() == 0)
   {
      double ask     = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double slPrice = NormalizeDouble(ask * (1.0 - InpSL_Pct / 100.0), _Digits);
      double tpPrice = NormalizeDouble(ask * (1.0 + InpTP_Pct / 100.0), _Digits);
      double slDist  = ask - slPrice;

      double lots = CalcLots(slDist);
      if(lots <= 0.0)
      {
         Print(EA_NAME, " Lotaje=0, trade no enviado");
         Dashboard();
         return;
      }

      MqlTradeRequest req;
      MqlTradeResult  res;
      ZeroMemory(req);
      ZeroMemory(res);
      req.action    = TRADE_ACTION_DEAL;
      req.symbol    = _Symbol;
      req.volume    = lots;
      req.type      = ORDER_TYPE_BUY;
      req.price     = ask;
      req.sl        = slPrice;
      req.tp        = tpPrice;
      req.deviation = 50;
      req.magic     = MAGIC_NUMBER;
      req.comment   = EA_NAME;

      if(OrderSend(req, res))
         Print(EA_NAME, " ORDEN ENVIADA | lots=", lots,
               " SL=", slPrice, " TP=", tpPrice);
      else
         Print(EA_NAME, " ERROR OrderSend: ", GetLastError(),
               " | retcode=", res.retcode);
   }

   Dashboard(); // Actualizar tras logica
}
