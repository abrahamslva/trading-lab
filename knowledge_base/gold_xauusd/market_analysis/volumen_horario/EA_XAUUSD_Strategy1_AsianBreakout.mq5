//+------------------------------------------------------------------+
//| EA_XAUUSD_Strategy1_AsianBreakout.mq5                          |
//| ESTRATEGIA #1: Asian Range Breakout + London Confirmation       |
//| Backtesting: 10 años en XAUUSD                                  |
//| Basada en "Biblia del Trading en Oro" + "Investigación XAUUSD"  |
//+------------------------------------------------------------------+
#property copyright "XAUUSD Backtesting"
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade         trade;
CPositionInfo  posInfo;

//--- Input parameters
input group "=== GESTIÓN DE RIESGO ==="
input double   RiskPercent       = 0.5;     // Riesgo por trade (%)
input double   DailyLossLimit    = 1.5;     // Límite pérdida diaria (%)
input int      MaxTradesPerDay   = 2;       // Máx trades por día

input group "=== CONFIGURACIÓN DEL RANGO ASIÁTICO ==="
input int      AsiaStartHour     = 22;     // Inicio sesión asiática (UTC)
input int      AsiaEndHour       = 8;      // Fin sesión asiática (UTC)
input double   MinRangePips      = 150;    // Rango mínimo asiático (pips) - en $4000+ son 150 pips
input double   MaxRangePips      = 800;    // Rango máximo asiático (pips)

input group "=== CONFIGURACIÓN DE ENTRADA ==="
input int      LondonEntryStart  = 8;      // Hora inicio entrada Londres (UTC)
input int      LondonEntryEnd    = 11;     // Hora fin entrada Londres (UTC)
input int      SweepConfirmBars  = 3;      // Velas para confirmar sweep
input bool     ConservativeEntry = true;   // Entrada conservadora (retesteo)

input group "=== ADR Y STOPS ==="
input int      ADRPeriod         = 14;     // Período para calcular ADR
input double   SLMultiplierADR   = 0.15;  // Multiplicador ADR para SL (0.15 × ADR)
input double   MinSLPips         = 200;   // SL mínimo en pips (en $4000+ XAU)
input double   TP1Ratio          = 1.5;   // TP1 ratio (1:1.5)
input double   TP2Ratio          = 2.5;   // TP2 ratio (1:2.5)
input double   TP3Ratio          = 3.5;   // TP3 ratio (1:3.5)
input double   TP1Percent        = 50;    // % posición para TP1
input double   TP2Percent        = 25;    // % posición para TP2

input group "=== FILTROS ==="
input bool     FilterMondayFriday = true; // Evitar lunes y reducir viernes
input int      FridayLastEntry   = 14;    // Última entrada viernes (UTC hora)
input bool     UseVolumeFilter   = true;  // Usar filtro de volumen

input group "=== DXY FILTER (Simulado) ==="
input bool     UseDXYFilter      = false; // Usar filtro DXY (desactivar en backtesting básico)

//--- Global variables
double   asianHigh, asianLow, asianMid;
double   prevDayHigh, prevDayLow;
double   dailyADR;
double   dailyStartBalance;
int      todayTrades;
datetime lastTradeDay;
datetime lastBarTime;
bool     asianRangeSet;
bool     sweepDetected;
bool     sweepDirection;   // true = sweep del high (ruptuta bajista esperada->SELLS), false = sweep del low
bool     alreadyEntered;
double   pointSize;
int      digits;

// TP tracking para gestión escalonada
ulong   ticket1, ticket2, ticket3;
bool    tp1Hit, tp2Hit;
double  initialSL;
double  breakevenPrice;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   pointSize = Point();
   digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   
   Print("EA Asian Range Breakout iniciado en ", _Symbol);
   Print("RiskPercent: ", RiskPercent, "% | SL multiplier ADR: ", SLMultiplierADR);
   
   trade.SetExpertMagicNumber(111001);
   trade.SetDeviationInPoints(30);
   
   ResetDailyVars();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Reset variables daily                                            |
//+------------------------------------------------------------------+
void ResetDailyVars()
{
   asianHigh      = 0;
   asianLow       = 9999999;
   asianMid       = 0;
   asianRangeSet  = false;
   sweepDetected  = false;
   alreadyEntered = false;
   tp1Hit         = false;
   tp2Hit         = false;
   todayTrades    = 0;
   dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
}

//+------------------------------------------------------------------+
//| Calculate ADR                                                    |
//+------------------------------------------------------------------+
double CalculateADR(int period)
{
   double totalRange = 0;
   for(int i = 1; i <= period; i++)
   {
      double hi = iHigh(_Symbol, PERIOD_D1, i);
      double lo = iLow(_Symbol, PERIOD_D1, i);
      totalRange += (hi - lo);
   }
   return totalRange / period;
}

//+------------------------------------------------------------------+
//| Check if new day                                                 |
//+------------------------------------------------------------------+
bool IsNewDay()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   MqlDateTime last;
   TimeToStruct(lastBarTime, last);
   return (dt.day != last.day);
}

//+------------------------------------------------------------------+
//| Get current UTC hour                                             |
//+------------------------------------------------------------------+
int GetUTCHour()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.hour;
}

//+------------------------------------------------------------------+
//| Get day of week                                                  |
//+------------------------------------------------------------------+
int GetDayOfWeek()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.day_of_week; // 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
}

//+------------------------------------------------------------------+
//| Check daily loss limit                                           |
//+------------------------------------------------------------------+
bool DailyLossExceeded()
{
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   double drawdown = (dailyStartBalance - equity) / dailyStartBalance * 100;
   return (drawdown >= DailyLossLimit);
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk %                              |
//+------------------------------------------------------------------+
double CalcLotSize(double slPips)
{
   double balance   = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount= balance * RiskPercent / 100.0;
   
   // Value per pip for XAUUSD
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pipValue  = (tickValue / tickSize) * pointSize;
   
   if(pipValue <= 0) pipValue = 1.0;
   
   double lots = riskAmount / (slPips * pipValue);
   
   // Clamp to broker limits
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   
   lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));
   
   return lots;
}

//+------------------------------------------------------------------+
//| Check if in Asian session                                        |
//+------------------------------------------------------------------+
bool InAsianSession()
{
   int h = GetUTCHour();
   // Asia: 22:00 – 08:00 UTC (crosses midnight)
   return (h >= AsiaStartHour || h < AsiaEndHour);
}

//+------------------------------------------------------------------+
//| Check if in London entry window                                  |
//+------------------------------------------------------------------+
bool InLondonWindow()
{
   int h = GetUTCHour();
   return (h >= LondonEntryStart && h < LondonEntryEnd);
}

//+------------------------------------------------------------------+
//| Update Asian range                                               |
//+------------------------------------------------------------------+
void UpdateAsianRange()
{
   if(!InAsianSession()) return;
   
   double high = iHigh(_Symbol, PERIOD_M15, 0);
   double low  = iLow(_Symbol,  PERIOD_M15, 0);
   
   if(high > asianHigh) asianHigh = high;
   if(low  < asianLow)  asianLow  = low;
}

//+------------------------------------------------------------------+
//| Detect London Sweep                                              |
//+------------------------------------------------------------------+
bool DetectSweep(bool &direction)
{
   if(!asianRangeSet) return false;
   
   double currentHigh = iHigh(_Symbol, PERIOD_M15, 0);
   double currentLow  = iLow(_Symbol,  PERIOD_M15, 0);
   double currentClose= iClose(_Symbol, PERIOD_M15, 0);
   
   // Sweep of Asian High: price spiked above then closed below
   if(currentHigh > asianHigh + MinSLPips * 0.3 * pointSize && 
      currentClose < asianHigh)
   {
      direction = true;  // Swept high → expect downward move
      return true;
   }
   
   // Sweep of Asian Low: price spiked below then closed above
   if(currentLow < asianLow - MinSLPips * 0.3 * pointSize && 
      currentClose > asianLow)
   {
      direction = false; // Swept low → expect upward move
      return true;
   }
   
   return false;
}

//+------------------------------------------------------------------+
//| Volume confirmation (using tick volume as proxy)                |
//+------------------------------------------------------------------+
bool ConfirmVolume(bool highIsGood)
{
   if(!UseVolumeFilter) return true;
   
   long vol = iVolume(_Symbol, PERIOD_M15, 0);
   long avgVol = 0;
   for(int i = 1; i <= 10; i++)
      avgVol += iVolume(_Symbol, PERIOD_M15, i);
   avgVol /= 10;
   
   if(highIsGood)
      return (vol >= avgVol); // Volume high or medium = valid sweep
   else
      return (vol < avgVol * 1.5); // Volume should NOT be excessively high
}

//+------------------------------------------------------------------+
//| Main tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check for new bar on M15
   datetime currentBarTime = iTime(_Symbol, PERIOD_M15, 0);
   if(currentBarTime == lastBarTime) return;
   lastBarTime = currentBarTime;
   
   // Check for new day and reset
   if(IsNewDay())
   {
      ResetDailyVars();
      // Get previous day levels
      prevDayHigh = iHigh(_Symbol, PERIOD_D1, 1);
      prevDayLow  = iLow(_Symbol,  PERIOD_D1, 1);
      // Calculate ADR
      dailyADR = CalculateADR(ADRPeriod);
   }
   
   // Day of week filter
   int dow = GetDayOfWeek();
   if(FilterMondayFriday)
   {
      if(dow == 1) return; // Skip Monday
      if(dow == 5 && GetUTCHour() >= FridayLastEntry) return; // Skip Friday afternoon
      if(dow == 0 || dow == 6) return; // Skip weekend
   }
   
   // Daily loss limit
   if(DailyLossExceeded()) return;
   
   // Max trades per day
   if(todayTrades >= MaxTradesPerDay) return;
   
   // === PHASE 1: Build Asian Range ===
   if(InAsianSession())
   {
      UpdateAsianRange();
      asianRangeSet = false; // Will be finalized at Asia end
      return;
   }
   
   // === Finalize Asian Range at 08:00 UTC ===
   if(GetUTCHour() == AsiaEndHour && !asianRangeSet)
   {
      double rangePips = (asianHigh - asianLow) / pointSize;
      
      if(rangePips < MinRangePips || rangePips > MaxRangePips)
      {
         // Range not valid, skip today
         alreadyEntered = true; // Prevent entry
         return;
      }
      
      asianMid = (asianHigh + asianLow) / 2.0;
      asianRangeSet = true;
      Print("Asian Range set: High=", asianHigh, " Low=", asianLow, " Range=", rangePips, " pips");
      
      // Check ADR already consumed
      double dayOpen = iOpen(_Symbol, PERIOD_D1, 0);
      double currentPrice = iClose(_Symbol, PERIOD_M15, 0);
      if(dailyADR > 0)
      {
         double consumed = MathAbs(currentPrice - dayOpen) / dailyADR * 100;
         if(consumed > 70.0)
         {
            Print("ADR already consumed ", consumed, "% - skipping today");
            alreadyEntered = true;
         }
      }
   }
   
   // === PHASE 2: London Window - Detect Sweep and Enter ===
   if(!InLondonWindow() || !asianRangeSet || alreadyEntered) return;
   
   // Manage existing positions (breakeven, trailing)
   ManagePositions();
   
   // Detect sweep
   if(!sweepDetected)
   {
      bool dir;
      if(DetectSweep(dir))
      {
         sweepDetected  = true;
         sweepDirection = dir;
         Print("Sweep detected! Direction: ", dir ? "HIGH (expect sell)" : "LOW (expect buy)");
      }
      return;
   }
   
   // After sweep detected, wait for entry confirmation
   if(sweepDetected && !alreadyEntered)
   {
      bool isBuy = !sweepDirection; // Swept low → buy
      
      // Calculate SL
      double slPips = MathMax(MinSLPips, dailyADR / pointSize * SLMultiplierADR);
      double price  = isBuy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl, tp1, tp2, tp3;
      
      if(isBuy)
      {
         sl  = price - slPips * pointSize;
         tp1 = price + slPips * TP1Ratio * pointSize;
         tp2 = price + slPips * TP2Ratio * pointSize;
         tp3 = price + slPips * TP3Ratio * pointSize;
         
         // Conservative entry: wait for retest of Asian Low
         if(ConservativeEntry)
         {
            double currentPrice = iClose(_Symbol, PERIOD_M15, 0);
            // For buy after low sweep, wait for price to be near Asian Low zone
            if(currentPrice > asianLow + slPips * 0.5 * pointSize)
               return; // Not at retest zone yet
         }
      }
      else
      {
         sl  = price + slPips * pointSize;
         tp1 = price - slPips * TP1Ratio * pointSize;
         tp2 = price - slPips * TP2Ratio * pointSize;
         tp3 = price - slPips * TP3Ratio * pointSize;
         
         // Conservative entry: wait for retest of Asian High
         if(ConservativeEntry)
         {
            double currentPrice = iClose(_Symbol, PERIOD_M15, 0);
            if(currentPrice < asianHigh - slPips * 0.5 * pointSize)
               return;
         }
      }
      
      // Volume filter - sweep should have been with medium/low volume (stop hunt)
      if(!ConfirmVolume(false)) return;
      
      // CHoCH confirmation: price must break structure in expected direction
      // Simplified: Check if current bar is a confirmation candle
      double open  = iOpen(_Symbol,  PERIOD_M15, 0);
      double close = iClose(_Symbol, PERIOD_M15, 0);
      bool confirmCandle = isBuy ? (close > open) : (close < open);
      if(!confirmCandle) return;
      
      double lots = CalcLotSize(slPips);
      if(lots <= 0) return;
      
      // Split into 3 positions for tiered TP
      double lot1 = MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), 
                           MathFloor(lots * TP1Percent / 100 / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * 
                           SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP));
      double lot2 = MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                           MathFloor(lots * TP2Percent / 100 / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * 
                           SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP));
      double lot3 = MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                           MathFloor((lots - lot1 - lot2) / SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP)) * 
                           SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP));
      
      if(lot3 < SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN)) lot3 = lot2;
      
      bool result1, result2, result3;
      
      if(isBuy)
      {
         result1 = trade.Buy(lot1, _Symbol, 0, sl, tp1, "S1_TP1");
         result2 = trade.Buy(lot2, _Symbol, 0, sl, tp2, "S1_TP2");
         result3 = trade.Buy(lot3, _Symbol, 0, sl, tp3, "S1_TP3");
      }
      else
      {
         result1 = trade.Sell(lot1, _Symbol, 0, sl, tp1, "S1_TP1");
         result2 = trade.Sell(lot2, _Symbol, 0, sl, tp2, "S1_TP2");
         result3 = trade.Sell(lot3, _Symbol, 0, sl, tp3, "S1_TP3");
      }
      
      if(result1)
      {
         todayTrades++;
         alreadyEntered = true;
         initialSL      = slPips;
         breakevenPrice = price;
         Print("Trade opened: ", isBuy ? "BUY" : "SELL", " | Lots:", lots, " | SL:", slPips, " pips | TP1:", TP1Ratio, "R | TP2:", TP2Ratio, "R");
      }
   }
}

//+------------------------------------------------------------------+
//| Manage open positions (breakeven, trailing)                      |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Magic() != 111001) continue;
      if(posInfo.Symbol() != _Symbol) continue;
      
      double openPrice = posInfo.PriceOpen();
      double currentSL = posInfo.StopLoss();
      double currentTP = posInfo.TakeProfit();
      double curPrice  = posInfo.PriceCurrent();
      bool   isBuyPos  = (posInfo.PositionType() == POSITION_TYPE_BUY);
      
      // Move to breakeven when TP1 range is achieved (1.5R)
      if(!tp1Hit && initialSL > 0)
      {
         double tp1Level = isBuyPos ? openPrice + initialSL * TP1Ratio * pointSize
                                    : openPrice - initialSL * TP1Ratio * pointSize;
         bool atTP1 = isBuyPos ? (curPrice >= tp1Level) : (curPrice <= tp1Level);
         
         if(atTP1)
         {
            // Move SL to breakeven
            double newSL = openPrice + (isBuyPos ? 2 : -2) * pointSize;
            if(isBuyPos && newSL > currentSL)
               trade.PositionModify(posInfo.Ticket(), newSL, currentTP);
            else if(!isBuyPos && newSL < currentSL)
               trade.PositionModify(posInfo.Ticket(), newSL, currentTP);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Deinit                                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("EA Asian Range Breakout - Backtesting completado");
}
//+------------------------------------------------------------------+
