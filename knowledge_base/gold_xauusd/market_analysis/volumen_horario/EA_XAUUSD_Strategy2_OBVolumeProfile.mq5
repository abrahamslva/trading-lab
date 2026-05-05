//+------------------------------------------------------------------+
//| EA_XAUUSD_Strategy2_OBVolumeProfile.mq5                        |
//| ESTRATEGIA #2: Order Block + Volume Profile Confluence          |
//| Backtesting: 10 años en XAUUSD                                  |
//| Sesión: Overlap Londres-Nueva York (13:00-17:00 UTC)            |
//+------------------------------------------------------------------+
#property copyright "XAUUSD Backtesting"
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade        trade;
CPositionInfo posInfo;

//--- Input parameters
input group "=== GESTIÓN DE RIESGO ==="
input double RiskPercent      = 0.75;    // Riesgo por trade (%)
input double DailyLossLimit   = 1.5;    // Límite pérdida diaria (%)
input int    MaxTradesPerWeek = 4;      // Máx trades por semana

input group "=== SESIÓN OVERLAP ==="
input int    OverlapStartHour = 13;     // Inicio Overlap (UTC)
input int    OverlapEndHour   = 17;     // Fin Overlap (UTC)

input group "=== ORDER BLOCK ==="
input int    OB_LookbackBars  = 50;    // Barras para buscar OBs (H4)
input int    OB_ImpulseMinBars= 3;     // Mínimo de barras en el impulso post-OB
input double OB_ImpulseMinPct = 0.3;   // Impulso mínimo como % del ADR
input bool   OB_MustNotBeMitigated = true; // OB no mitigado obligatorio

input group "=== VOLUME PROFILE (Simulado con Tick Volume) ==="
input int    VP_Period        = 20;    // Período del Volume Profile (D1 bars)
input int    VP_Zones         = 10;   // Número de zonas para el VP

input group "=== FIBONACCI ==="
input bool   UseFiboFilter    = true;  // Filtrar entradas por zonas Fibonacci
input double Fib382           = 0.382;
input double Fib500           = 0.500;
input double Fib618           = 0.618;

input group "=== STOPS Y TP ==="
input int    ATR_Period        = 14;   // Período ATR para stops
input double SL_ATR_Mult       = 1.5;  // Multiplicador ATR para SL
input double TP1_Ratio         = 2.0;  // TP1 ratio
input double TP2_Ratio         = 4.0;  // TP2 ratio
input double TP3_Ratio         = 6.0;  // TP3 ratio
input double TP1_Percent       = 40;   // % posición en TP1
input double TP2_Percent       = 35;   // % posición en TP2

input group "=== FILTROS ==="
input bool   FilterWeekdays   = true;  // Solo miércoles y jueves
input bool   UseRSI_Filter    = true;  // Filtro RSI
input int    RSI_Period        = 14;
input double RSI_OversoldLevel = 50;   // RSI max para compras en tendencia
input double RSI_OverboughtLevel = 60; // RSI min para ventas en tendencia

//--- Structure for Order Block
struct OrderBlock
{
   double   high;
   double   low;
   double   mid;
   bool     isBullish;    // true = bullish OB (last red before impulse up)
   bool     mitigated;
   datetime time;
   double   impulseStrength; // Size of the impulse that followed
};

//--- Global variables
OrderBlock  detectedOBs[];
int         obCount;
double      dailyADR;
datetime    lastBarTimeH4;
datetime    lastBarTimeM15;
bool        positionOpen;
double      dailyStartBalance;
int         weekTrades;
datetime    lastWeekStart;
datetime    lastTradeTime;
double      pointSize;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   pointSize = Point();
   trade.SetExpertMagicNumber(111002);
   trade.SetDeviationInPoints(30);
   
   ArrayResize(detectedOBs, 20);
   obCount = 0;
   
   dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   weekTrades = 0;
   
   Print("EA OB + Volume Profile iniciado en ", _Symbol);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Calculate ADR                                                    |
//+------------------------------------------------------------------+
double CalculateADR(int period)
{
   double totalRange = 0;
   for(int i = 1; i <= period; i++)
      totalRange += (iHigh(_Symbol, PERIOD_D1, i) - iLow(_Symbol, PERIOD_D1, i));
   return totalRange / period;
}

//+------------------------------------------------------------------+
//| Get ATR value                                                    |
//+------------------------------------------------------------------+
double GetATR(ENUM_TIMEFRAMES tf, int period)
{
   int    handle = iATR(_Symbol, tf, period);
   double buf[1];
   if(CopyBuffer(handle, 0, 1, 1, buf) == 1)
   {
      IndicatorRelease(handle);
      return buf[0];
   }
   IndicatorRelease(handle);
   return 0;
}

//+------------------------------------------------------------------+
//| Get RSI value                                                    |
//+------------------------------------------------------------------+
double GetRSI(ENUM_TIMEFRAMES tf, int period, int shift = 1)
{
   int    handle = iRSI(_Symbol, tf, period, PRICE_CLOSE);
   double buf[1];
   if(CopyBuffer(handle, 0, shift, 1, buf) == 1)
   {
      IndicatorRelease(handle);
      return buf[0];
   }
   IndicatorRelease(handle);
   return 50;
}

//+------------------------------------------------------------------+
//| Get EMA value                                                    |
//+------------------------------------------------------------------+
double GetEMA(ENUM_TIMEFRAMES tf, int period, int shift = 1)
{
   int    handle = iMA(_Symbol, tf, period, 0, MODE_EMA, PRICE_CLOSE);
   double buf[1];
   if(CopyBuffer(handle, 0, shift, 1, buf) == 1)
   {
      IndicatorRelease(handle);
      return buf[0];
   }
   IndicatorRelease(handle);
   return 0;
}

//+------------------------------------------------------------------+
//| Detect Order Blocks on H4                                        |
//+------------------------------------------------------------------+
void DetectOrderBlocks()
{
   obCount = 0;
   int bars = (int)MathMin(OB_LookbackBars, iBars(_Symbol, PERIOD_H4) - 10);
   
   for(int i = bars; i >= OB_ImpulseMinBars + 1; i--)
   {
      double open_i  = iOpen(_Symbol,  PERIOD_H4, i);
      double close_i = iClose(_Symbol, PERIOD_H4, i);
      double high_i  = iHigh(_Symbol,  PERIOD_H4, i);
      double low_i   = iLow(_Symbol,   PERIOD_H4, i);
      
      bool isRedBar = (close_i < open_i); // Red = potential bullish OB
      bool isGreenBar = (close_i > open_i); // Green = potential bearish OB
      
      if(!isRedBar && !isGreenBar) continue;
      
      // Check impulse after this bar
      double impulseSize = 0;
      bool   impulseConfirmed = false;
      bool   impulseDirection = false; // true = up (bullish impulse after red OB)
      
      if(isRedBar)
      {
         // Check for bullish impulse after red bar
         double maxClose = close_i;
         int    impulseBars = 0;
         for(int j = i - 1; j >= i - OB_ImpulseMinBars; j--)
         {
            double c = iClose(_Symbol, PERIOD_H4, j);
            if(c > maxClose) { maxClose = c; impulseBars++; }
         }
         impulseSize = maxClose - high_i;
         if(impulseBars >= OB_ImpulseMinBars && impulseSize > dailyADR * OB_ImpulseMinPct)
         {
            impulseConfirmed = true;
            impulseDirection = true;
         }
      }
      else if(isGreenBar)
      {
         // Check for bearish impulse after green bar
         double minClose = close_i;
         int    impulseBars = 0;
         for(int j = i - 1; j >= i - OB_ImpulseMinBars; j--)
         {
            double c = iClose(_Symbol, PERIOD_H4, j);
            if(c < minClose) { minClose = c; impulseBars++; }
         }
         impulseSize = low_i - minClose;
         if(impulseBars >= OB_ImpulseMinBars && impulseSize > dailyADR * OB_ImpulseMinPct)
         {
            impulseConfirmed = true;
            impulseDirection = false;
         }
      }
      
      if(!impulseConfirmed) continue;
      
      // Check if OB has been mitigated (price returned to it after impulse)
      bool mitigated = false;
      if(OB_MustNotBeMitigated)
      {
         for(int j = i - OB_ImpulseMinBars - 1; j >= 1; j--)
         {
            double lo = iLow(_Symbol,  PERIOD_H4, j);
            double hi = iHigh(_Symbol, PERIOD_H4, j);
            if(impulseDirection && lo <= high_i) { mitigated = true; break; }
            if(!impulseDirection && hi >= low_i) { mitigated = true; break; }
         }
         if(mitigated) continue;
      }
      
      // Store the OB
      if(obCount < ArraySize(detectedOBs))
      {
         detectedOBs[obCount].high           = high_i;
         detectedOBs[obCount].low            = low_i;
         detectedOBs[obCount].mid            = (high_i + low_i) / 2.0;
         detectedOBs[obCount].isBullish      = impulseDirection;
         detectedOBs[obCount].mitigated      = mitigated;
         detectedOBs[obCount].time           = iTime(_Symbol, PERIOD_H4, i);
         detectedOBs[obCount].impulseStrength= impulseSize;
         obCount++;
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Volume Profile POC (simplified using tick volume)     |
//+------------------------------------------------------------------+
double CalculatePOC()
{
   // Simplified: find the price level with highest volume over VP_Period days
   // We use the daily bar with highest range*volume ratio as proxy
   double bestScore = 0;
   double pocLevel  = 0;
   
   for(int i = 1; i <= VP_Period; i++)
   {
      double hi  = iHigh(_Symbol, PERIOD_D1, i);
      double lo  = iLow(_Symbol,  PERIOD_D1, i);
      double vol = (double)iVolume(_Symbol, PERIOD_D1, i);
      double mid = (hi + lo) / 2.0;
      double score = (hi - lo) * vol;
      if(score > bestScore) { bestScore = score; pocLevel = mid; }
   }
   return pocLevel;
}

//+------------------------------------------------------------------+
//| Check Fibonacci zone                                             |
//+------------------------------------------------------------------+
bool InFiboZone(double currentPrice, bool isBullishSetup)
{
   if(!UseFiboFilter) return true;
   
   // Find recent swing high and low in H4
   double swingHigh = 0, swingLow = 9999999;
   for(int i = 1; i <= 50; i++)
   {
      double h = iHigh(_Symbol, PERIOD_H4, i);
      double l = iLow(_Symbol,  PERIOD_H4, i);
      if(h > swingHigh) swingHigh = h;
      if(l < swingLow)  swingLow  = l;
   }
   
   if(swingHigh <= swingLow) return true;
   
   double range = swingHigh - swingLow;
   double fib382 = isBullishSetup ? swingHigh - range * Fib382 : swingLow + range * Fib382;
   double fib500 = isBullishSetup ? swingHigh - range * Fib500 : swingLow + range * Fib500;
   double fib618 = isBullishSetup ? swingHigh - range * Fib618 : swingLow + range * Fib618;
   
   double zone = dailyADR * 0.1; // Tolerance zone
   
   bool nearFib = (MathAbs(currentPrice - fib382) < zone ||
                   MathAbs(currentPrice - fib500) < zone ||
                   MathAbs(currentPrice - fib618) < zone);
   return nearFib;
}

//+------------------------------------------------------------------+
//| Count score confluence                                           |
//+------------------------------------------------------------------+
int CountConfluence(int obIdx, double currentPrice, bool isBullish)
{
   if(obIdx < 0 || obIdx >= obCount) return 0;
   
   int score = 0;
   double poc = CalculatePOC();
   
   // 1. OB near POC
   if(MathAbs(detectedOBs[obIdx].mid - poc) < dailyADR * 0.15) score += 3;
   
   // 2. OB near Fibonacci
   if(InFiboZone(detectedOBs[obIdx].mid, isBullish)) score += 3;
   
   // 3. OB near PDH/PDL
   double pdh = iHigh(_Symbol, PERIOD_D1, 1);
   double pdl = iLow(_Symbol,  PERIOD_D1, 1);
   if(MathAbs(detectedOBs[obIdx].high - pdh) < dailyADR * 0.1 ||
      MathAbs(detectedOBs[obIdx].low  - pdl) < dailyADR * 0.1) score += 2;
   
   // 4. Psychological round level
   double rnd = MathRound(detectedOBs[obIdx].mid / 100.0) * 100.0;
   if(MathAbs(detectedOBs[obIdx].mid - rnd) < dailyADR * 0.12) score += 2;
   
   // 5. RSI zone
   double rsi = GetRSI(PERIOD_H4, RSI_Period);
   if(isBullish && rsi >= 40 && rsi <= RSI_OversoldLevel) score += 1;
   if(!isBullish && rsi >= RSI_OverboughtLevel && rsi <= 70) score += 1;
   
   // 6. EMA alignment
   double ema50 = GetEMA(PERIOD_D1, 50);
   double ema200= GetEMA(PERIOD_D1, 200);
   if(isBullish && currentPrice > ema50 && ema50 > ema200) score += 2;
   if(!isBullish && currentPrice < ema50 && ema50 < ema200) score += 2;
   
   return score;
}

//+------------------------------------------------------------------+
//| Check ADR consumed ratio                                        |
//+------------------------------------------------------------------+
double GetADRConsumed()
{
   if(dailyADR <= 0) return 0;
   double dayHigh = iHigh(_Symbol, PERIOD_D1, 0);
   double dayLow  = iLow(_Symbol,  PERIOD_D1, 0);
   return (dayHigh - dayLow) / dailyADR * 100;
}

//+------------------------------------------------------------------+
//| Get lot size                                                    |
//+------------------------------------------------------------------+
double CalcLotSize(double slPips)
{
   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * RiskPercent / 100.0;
   double tickValue  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pipValue   = (tickValue / tickSize) * pointSize;
   if(pipValue <= 0) pipValue = 1.0;
   double lots       = riskAmount / (slPips * pipValue);
   double step       = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lots = MathFloor(lots / step) * step;
   lots = MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                  MathMin(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), lots));
   return lots;
}

//+------------------------------------------------------------------+
//| Check for new week                                               |
//+------------------------------------------------------------------+
bool IsNewWeek()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime weekStart = TimeCurrent() - dt.day_of_week * 86400;
   weekStart -= (weekStart % 86400);
   if(weekStart > lastWeekStart)
   {
      lastWeekStart = weekStart;
      weekTrades = 0;
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Main tick                                                        |
//+------------------------------------------------------------------+
void OnTick()
{
   // New H4 bar
   datetime curH4 = iTime(_Symbol, PERIOD_H4, 0);
   bool newH4Bar  = (curH4 != lastBarTimeH4);
   if(newH4Bar)
   {
      lastBarTimeH4 = curH4;
      dailyADR = CalculateADR(14);
      IsNewWeek();
      DetectOrderBlocks();
   }
   
   // New M15 bar for entries
   datetime curM15 = iTime(_Symbol, PERIOD_M15, 0);
   if(curM15 == lastBarTimeM15) return;
   lastBarTimeM15 = curM15;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   int dow  = dt.day_of_week;
   
   // Weekend filter
   if(dow == 0 || dow == 6) return;
   
   // Day filter: prefer Wed/Thu
   if(FilterWeekdays && (dow == 1)) return; // Skip Monday
   if(dow == 5 && hour >= 14) return; // Skip Friday afternoon
   
   // Overlap window
   if(hour < OverlapStartHour || hour >= OverlapEndHour) return;
   
   // Daily loss limit
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   if(dailyStartBalance > 0)
   {
      double dd = (dailyStartBalance - equity) / dailyStartBalance * 100;
      if(dd >= DailyLossLimit) return;
   }
   
   // Reset daily balance at start of day
   if(hour == 0 && dt.min < 15)
      dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   // Max trades this week
   if(weekTrades >= MaxTradesPerWeek) return;
   
   // ADR filter
   if(GetADRConsumed() > 70) return;
   
   // Check if we already have too many positions
   int myPositions = 0;
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == 111002 && posInfo.Symbol() == _Symbol)
         myPositions++;
   }
   if(myPositions >= 3) // Max 3 partial positions per trade
   {
      ManagePositions();
      return;
   }
   
   ManagePositions();
   
   // No new entry if positions open
   if(myPositions > 0) return;
   
   // Find best OB to trade
   double currentPrice = iClose(_Symbol, PERIOD_M15, 1);
   double atr = GetATR(PERIOD_H4, ATR_Period);
   if(atr <= 0) return;
   
   int    bestOBIdx   = -1;
   int    bestScore   = 0;
   bool   bestIsBull  = true;
   
   for(int i = 0; i < obCount; i++)
   {
      // Is price at/near this OB?
      double obRange = detectedOBs[i].high - detectedOBs[i].low;
      double touchZone = MathMax(obRange, atr * 0.5);
      
      bool priceAtOB = (currentPrice >= detectedOBs[i].low - touchZone * 0.2 &&
                        currentPrice <= detectedOBs[i].high + touchZone * 0.2);
      if(!priceAtOB) continue;
      
      bool isBull = detectedOBs[i].isBullish;
      int  score  = CountConfluence(i, currentPrice, isBull);
      
      if(score >= 4 && score > bestScore)
      {
         bestScore  = score;
         bestOBIdx  = i;
         bestIsBull = isBull;
      }
   }
   
   if(bestOBIdx < 0) return;
   
   // Confirmation candle on M15
   double open1  = iOpen(_Symbol,  PERIOD_M15, 1);
   double close1 = iClose(_Symbol, PERIOD_M15, 1);
   double high1  = iHigh(_Symbol,  PERIOD_M15, 1);
   double low1   = iLow(_Symbol,   PERIOD_M15, 1);
   double body1  = MathAbs(close1 - open1);
   double range1 = high1 - low1;
   
   bool confirmBull = bestIsBull  && (close1 > open1) && (body1 > range1 * 0.4);
   bool confirmBear = !bestIsBull && (close1 < open1) && (body1 > range1 * 0.4);
   
   if(!confirmBull && !confirmBear) return;
   
   // Volume confirmation
   long vol1   = iVolume(_Symbol, PERIOD_M15, 1);
   long avgVol = 0;
   for(int j = 2; j <= 6; j++) avgVol += iVolume(_Symbol, PERIOD_M15, j);
   avgVol /= 5;
   if(vol1 < avgVol) return; // Need above-average volume on confirmation candle
   
   // Calculate stops
   double slPips = atr * SL_ATR_Mult / pointSize;
   double price  = bestIsBull ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   double sl, tp1, tp2, tp3;
   if(bestIsBull)
   {
      sl  = detectedOBs[bestOBIdx].low - atr * 0.3;
      tp1 = price + slPips * TP1_Ratio * pointSize;
      tp2 = price + slPips * TP2_Ratio * pointSize;
      tp3 = price + slPips * TP3_Ratio * pointSize;
   }
   else
   {
      sl  = detectedOBs[bestOBIdx].high + atr * 0.3;
      tp1 = price - slPips * TP1_Ratio * pointSize;
      tp2 = price - slPips * TP2_Ratio * pointSize;
      tp3 = price - slPips * TP3_Ratio * pointSize;
   }
   
   // Verify minimum RR
   double actualSL = MathAbs(price - sl) / pointSize;
   if(actualSL <= 0) return;
   double rr1 = slPips * TP1_Ratio / actualSL;
   if(rr1 < TP1_Ratio * 0.8) return; // Require at least 80% of target RR
   
   double lots = CalcLotSize(actualSL);
   if(lots <= 0) return;
   
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   
   double lot1 = MathMax(minLot, MathFloor(lots * TP1_Percent / 100 / step) * step);
   double lot2 = MathMax(minLot, MathFloor(lots * TP2_Percent / 100 / step) * step);
   double lot3 = MathMax(minLot, MathFloor((lots - lot1 - lot2) / step) * step);
   if(lot3 < minLot) lot3 = minLot;
   
   bool ok = false;
   if(bestIsBull)
   {
      ok |= trade.Buy(lot1, _Symbol, price, sl, tp1, "S2_TP1");
      ok |= trade.Buy(lot2, _Symbol, price, sl, tp2, "S2_TP2");
      ok |= trade.Buy(lot3, _Symbol, price, sl, tp3, "S2_TP3");
   }
   else
   {
      ok |= trade.Sell(lot1, _Symbol, price, sl, tp1, "S2_TP1");
      ok |= trade.Sell(lot2, _Symbol, price, sl, tp2, "S2_TP2");
      ok |= trade.Sell(lot3, _Symbol, price, sl, tp3, "S2_TP3");
   }
   
   if(ok)
   {
      weekTrades++;
      Print("S2 Trade: ", bestIsBull ? "BUY" : "SELL", " | Score:", bestScore, " | OB:", detectedOBs[bestOBIdx].mid, " | SL:", actualSL, " pips | RR:", TP3_Ratio);
   }
}

//+------------------------------------------------------------------+
//| Manage existing positions                                        |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Magic() != 111002 || posInfo.Symbol() != _Symbol) continue;
      
      double openPrice = posInfo.PriceOpen();
      double currentSL = posInfo.StopLoss();
      double currentTP = posInfo.TakeProfit();
      double curPrice  = posInfo.PriceCurrent();
      bool   isBuy     = (posInfo.PositionType() == POSITION_TYPE_BUY);
      double atr       = GetATR(PERIOD_H4, ATR_Period);
      
      // Move to breakeven after TP1 is reached
      double rrAchieved = isBuy ? (curPrice - openPrice) / (atr > 0 ? atr : 1)
                                : (openPrice - curPrice) / (atr > 0 ? atr : 1);
      
      if(rrAchieved >= TP1_Ratio * 0.9) // Near TP1
      {
         double newSL = isBuy ? openPrice + pointSize * 5 : openPrice - pointSize * 5;
         if(isBuy && newSL > currentSL)
            trade.PositionModify(posInfo.Ticket(), newSL, currentTP);
         else if(!isBuy && (currentSL <= 0 || newSL < currentSL))
            trade.PositionModify(posInfo.Ticket(), newSL, currentTP);
      }
      
      // Trailing with EMA 20 on H1
      if(rrAchieved >= TP2_Ratio * 0.9)
      {
         double ema20H1 = GetEMA(PERIOD_H1, 20, 1);
         if(isBuy && ema20H1 > openPrice && ema20H1 > currentSL)
            trade.PositionModify(posInfo.Ticket(), ema20H1 - atr * 0.2, currentTP);
         else if(!isBuy && ema20H1 < openPrice && (currentSL <= 0 || ema20H1 < currentSL))
            trade.PositionModify(posInfo.Ticket(), ema20H1 + atr * 0.2, currentTP);
      }
   }
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("EA OB + Volume Profile - Backtesting completado");
}
//+------------------------------------------------------------------+
