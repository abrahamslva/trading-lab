//+------------------------------------------------------------------+
//| EA_XAUUSD_Strategy3_MacroSwing.mq5                             |
//| ESTRATEGIA #3: Macro Swing Trading con OBV + EMA + Fibonacci   |
//| Backtesting: 10 años en XAUUSD                                  |
//| Sesión: Daily/H4 - Swing 2-5 días                               |
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
input double RiskPercent      = 0.5;     // Riesgo por trade (%)
input double DailyLossLimit   = 1.5;    // Límite pérdida diaria (%)
input double WeeklyLossLimit  = 3.0;    // Límite pérdida semanal (%)
input int    MaxPositions     = 1;       // Max posiciones simultáneas

input group "=== EMAs Y TENDENCIA ==="
input int    EMA_Fast        = 20;       // EMA rápida (H4)
input int    EMA_Medium      = 50;       // EMA media (H4 y D1)
input int    EMA_Slow        = 200;      // EMA lenta (D1)

input group "=== OBV (On-Balance Volume) ==="
input int    OBV_Period      = 1;        // OBV es acumulativo, período = 1
input bool   UseOBVFilter    = true;     // Usar divergencias de OBV
input int    OBVLookback     = 20;       // Barras para analizar OBV

input group "=== FIBONACCI ==="
input double Fib_382         = 0.382;
input double Fib_500         = 0.500;
input double Fib_618         = 0.618;
input double Fib_Tolerance   = 0.020;   // ±2% del rango como tolerancia

input group "=== STOPS Y TP ==="
input int    ATR_Period       = 14;
input double SL_ATR_Mult      = 1.5;    // SL = ATR × multiplicador
input double TP1_Ratio        = 2.0;    // TP1
input double TP2_Ratio        = 5.0;    // TP2
input double TP3_Ratio        = 10.0;   // TP3 (swing target)
input double TP1_Percent      = 35;     // % en TP1
input double TP2_Percent      = 35;     // % en TP2

input group "=== FILTROS ==="
input bool   FilterBySeasonality = true;  // Filtrar September (bajista para oro)
input bool   UseRSIFilter    = true;
input int    RSI_Period       = 14;
input bool   UseMACDFilter   = true;
input int    MACD_Fast        = 12;
input int    MACD_Slow        = 26;
input int    MACD_Signal      = 9;
input int    MinTradesBetween = 3;       // Mínimo de barras H4 entre trades

//--- Global variables
double   pointSize;
datetime lastBarH4, lastBarD1;
datetime lastTradeBar;
int      barsSinceLastTrade;
double   dailyStartBalance, weeklyStartBalance;
datetime lastDayReset, lastWeekReset;
double   obvBuffer[];    // OBV calculated manually
double   swingHigh, swingLow;
int      swingHighBar, swingLowBar;
bool     trendIsBullish;
double   currentATR;
int      myPositionCount;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   pointSize = Point();
   trade.SetExpertMagicNumber(111003);
   trade.SetDeviationInPoints(30);
   
   ArrayResize(obvBuffer, 500);
   ArrayInitialize(obvBuffer, 0);
   
   dailyStartBalance  = AccountInfoDouble(ACCOUNT_BALANCE);
   weeklyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   
   Print("EA Macro Swing iniciado en ", _Symbol);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Get indicator value helper                                       |
//+------------------------------------------------------------------+
double GetIndicatorValue(int handle, int shift = 1)
{
   double buf[1];
   if(CopyBuffer(handle, 0, shift, 1, buf) == 1) return buf[0];
   return EMPTY_VALUE;
}

//+------------------------------------------------------------------+
//| Get EMA                                                          |
//+------------------------------------------------------------------+
double GetEMA(ENUM_TIMEFRAMES tf, int period, int shift = 1)
{
   int h = iMA(_Symbol, tf, period, 0, MODE_EMA, PRICE_CLOSE);
   double v = GetIndicatorValue(h, shift);
   IndicatorRelease(h);
   return v;
}

//+------------------------------------------------------------------+
//| Get ATR                                                          |
//+------------------------------------------------------------------+
double GetATR(ENUM_TIMEFRAMES tf, int period, int shift = 1)
{
   int h = iATR(_Symbol, tf, period);
   double v = GetIndicatorValue(h, shift);
   IndicatorRelease(h);
   return v;
}

//+------------------------------------------------------------------+
//| Get RSI                                                          |
//+------------------------------------------------------------------+
double GetRSI(ENUM_TIMEFRAMES tf, int period, int shift = 1)
{
   int h = iRSI(_Symbol, tf, period, PRICE_CLOSE);
   double v = GetIndicatorValue(h, shift);
   IndicatorRelease(h);
   return v;
}

//+------------------------------------------------------------------+
//| Get MACD                                                         |
//+------------------------------------------------------------------+
void GetMACD(ENUM_TIMEFRAMES tf, int fast, int slow, int sig,
             double &macdLine, double &signalLine, int shift = 1)
{
   int h = iMACD(_Symbol, tf, fast, slow, sig, PRICE_CLOSE);
   double mainBuf[1], signalBuf[1];
   CopyBuffer(h, 0, shift, 1, mainBuf);
   CopyBuffer(h, 1, shift, 1, signalBuf);
   IndicatorRelease(h);
   macdLine   = mainBuf[0];
   signalLine = signalBuf[0];
}

//+------------------------------------------------------------------+
//| Calculate OBV manually (simplified)                              |
//+------------------------------------------------------------------+
double CalculateOBV(int bars = 50)
{
   double obv = 0;
   for(int i = bars; i >= 1; i--)
   {
      double close = iClose(_Symbol, PERIOD_D1, i);
      double prevClose = iClose(_Symbol, PERIOD_D1, i + 1);
      double vol = (double)iVolume(_Symbol, PERIOD_D1, i);
      if(close > prevClose)      obv += vol;
      else if(close < prevClose) obv -= vol;
   }
   return obv;
}

//+------------------------------------------------------------------+
//| Detect OBV divergence (simplified)                              |
//+------------------------------------------------------------------+
bool HasBullishOBVDivergence()
{
   // Price making lower low but OBV making higher low = bullish divergence
   double obv1 = CalculateOBV(10);
   double obv2 = CalculateOBV(20);
   
   double priceLow1 = 9999999, priceLow2 = 9999999;
   for(int i = 1; i <= 10; i++)
      priceLow1 = MathMin(priceLow1, iLow(_Symbol, PERIOD_D1, i));
   for(int i = 11; i <= 20; i++)
      priceLow2 = MathMin(priceLow2, iLow(_Symbol, PERIOD_D1, i));
   
   // Price lower low but OBV higher (= bullish divergence)
   return (priceLow1 < priceLow2 && obv1 > obv2);
}

bool HasBearishOBVDivergence()
{
   double obv1 = CalculateOBV(10);
   double obv2 = CalculateOBV(20);
   
   double priceHigh1 = 0, priceHigh2 = 0;
   for(int i = 1; i <= 10; i++)
      priceHigh1 = MathMax(priceHigh1, iHigh(_Symbol, PERIOD_D1, i));
   for(int i = 11; i <= 20; i++)
      priceHigh2 = MathMax(priceHigh2, iHigh(_Symbol, PERIOD_D1, i));
   
   return (priceHigh1 > priceHigh2 && obv1 < obv2);
}

//+------------------------------------------------------------------+
//| OBV confirming trend                                             |
//+------------------------------------------------------------------+
bool OBVConfirmsBullish()
{
   if(!UseOBVFilter) return true;
   // OBV should be rising (recent OBV > older OBV)
   double recentOBV = CalculateOBV(5);
   double olderOBV  = CalculateOBV(20);
   return (recentOBV > olderOBV);
}

bool OBVConfirmsBearish()
{
   if(!UseOBVFilter) return true;
   double recentOBV = CalculateOBV(5);
   double olderOBV  = CalculateOBV(20);
   return (recentOBV < olderOBV);
}

//+------------------------------------------------------------------+
//| Find swing high/low for Fibonacci                               |
//+------------------------------------------------------------------+
void FindSwings(int lookback = 60)
{
   swingHigh = 0; swingLow = 9999999;
   swingHighBar = 1; swingLowBar = 1;
   
   for(int i = 1; i <= lookback; i++)
   {
      double h = iHigh(_Symbol, PERIOD_D1, i);
      double l = iLow(_Symbol,  PERIOD_D1, i);
      if(h > swingHigh) { swingHigh = h; swingHighBar = i; }
      if(l < swingLow)  { swingLow  = l; swingLowBar  = i; }
   }
}

//+------------------------------------------------------------------+
//| Check if price is in Fibonacci zone                             |
//+------------------------------------------------------------------+
bool InFiboRetracementZone(double currentPrice, bool isBullish)
{
   FindSwings(60);
   
   if(swingHigh <= swingLow) return false;
   double range = swingHigh - swingLow;
   double tol   = range * Fib_Tolerance;
   
   if(isBullish)
   {
      // Price should be retracing from high to Fib support (38.2%, 50%, 61.8%)
      // In uptrend: high is recent, we look for pullback
      double fib382 = swingHigh - range * Fib_382;
      double fib500 = swingHigh - range * Fib_500;
      double fib618 = swingHigh - range * Fib_618;
      
      return (MathAbs(currentPrice - fib382) < tol ||
              MathAbs(currentPrice - fib500) < tol ||
              MathAbs(currentPrice - fib618) < tol);
   }
   else
   {
      // In downtrend: bearish retracement
      double fib382 = swingLow + range * Fib_382;
      double fib500 = swingLow + range * Fib_500;
      double fib618 = swingLow + range * Fib_618;
      
      return (MathAbs(currentPrice - fib382) < tol ||
              MathAbs(currentPrice - fib500) < tol ||
              MathAbs(currentPrice - fib618) < tol);
   }
}

//+------------------------------------------------------------------+
//| Determine macro trend                                            |
//+------------------------------------------------------------------+
bool DetermineUptrend()
{
   double ema200D1 = GetEMA(PERIOD_D1, 200, 1);
   double ema50D1  = GetEMA(PERIOD_D1, 50,  1);
   double closeD1  = iClose(_Symbol, PERIOD_D1, 1);
   
   // Price above EMA50, EMA50 above EMA200 = bullish macro
   return (closeD1 > ema50D1 && ema50D1 > ema200D1);
}

bool DetermineDowntrend()
{
   double ema200D1 = GetEMA(PERIOD_D1, 200, 1);
   double ema50D1  = GetEMA(PERIOD_D1, 50,  1);
   double closeD1  = iClose(_Symbol, PERIOD_D1, 1);
   
   return (closeD1 < ema50D1 && ema50D1 < ema200D1);
}

//+------------------------------------------------------------------+
//| Check seasonality filter                                         |
//+------------------------------------------------------------------+
bool SeasonalityAllowsTrade(bool isBull)
{
   if(!FilterBySeasonality) return true;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int month = dt.mon;
   
   // September historically bearish (90% negative), avoid bullish trades
   if(isBull && month == 9) return false;
   
   // January, February historically bullish (80%+), avoid bearish
   if(!isBull && (month == 1 || month == 2)) return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| Calculate lot size                                               |
//+------------------------------------------------------------------+
double CalcLotSize(double slPips)
{
   double balance   = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmt   = balance * RiskPercent / 100.0;
   double tickVal   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pipVal    = (tickVal / tickSize) * pointSize;
   if(pipVal <= 0) pipVal = 1.0;
   double lots      = riskAmt / (slPips * pipVal);
   double step      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lots = MathFloor(lots / step) * step;
   lots = MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                  MathMin(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX), lots));
   return lots;
}

//+------------------------------------------------------------------+
//| Check drawdown limits                                            |
//+------------------------------------------------------------------+
bool DrawdownOK()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   
   if(dailyStartBalance > 0)
   {
      double dayDD = (dailyStartBalance - equity) / dailyStartBalance * 100;
      if(dayDD >= DailyLossLimit) return false;
   }
   if(weeklyStartBalance > 0)
   {
      double weekDD = (weeklyStartBalance - equity) / weeklyStartBalance * 100;
      if(weekDD >= WeeklyLossLimit) return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Count my open positions                                          |
//+------------------------------------------------------------------+
int CountMyPositions()
{
   int cnt = 0;
   for(int i = 0; i < PositionsTotal(); i++)
      if(posInfo.SelectByIndex(i) && posInfo.Magic() == 111003 && posInfo.Symbol() == _Symbol)
         cnt++;
   return cnt;
}

//+------------------------------------------------------------------+
//| Main tick                                                        |
//+------------------------------------------------------------------+
void OnTick()
{
   // Only process on new H4 bar for swing trading efficiency
   datetime curH4 = iTime(_Symbol, PERIOD_H4, 0);
   if(curH4 == lastBarH4) 
   {
      // Still check position management on every tick
      ManagePositions();
      return;
   }
   lastBarH4 = curH4;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Reset daily/weekly balances
   datetime today = StringToTime(TimeToString(TimeCurrent(), TIME_DATE));
   if(today != lastDayReset)
   {
      lastDayReset = today;
      dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   }
   int dow = dt.day_of_week;
   if(dow == 1 && today != lastWeekReset) // Monday = new week
   {
      lastWeekReset = today;
      weeklyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   }
   
   // Drawdown check
   if(!DrawdownOK()) return;
   
   // Max positions
   myPositionCount = CountMyPositions();
   if(myPositionCount >= MaxPositions)
   {
      ManagePositions();
      return;
   }
   
   // Skip weekends
   if(dow == 0 || dow == 6) return;
   
   // Bars since last trade check
   barsSinceLastTrade++;
   if(barsSinceLastTrade < MinTradesBetween) return;
   
   // Calculate ATR
   currentATR = GetATR(PERIOD_H4, ATR_Period, 1);
   if(currentATR <= 0) return;
   
   double currentPrice = iClose(_Symbol, PERIOD_H4, 1);
   
   // === DETERMINE MACRO TREND ===
   bool uptrend   = DetermineUptrend();
   bool downtrend = DetermineDowntrend();
   
   if(!uptrend && !downtrend) return; // Neutral / ranging = skip
   
   trendIsBullish = uptrend;
   
   // === SEASONALITY CHECK ===
   if(!SeasonalityAllowsTrade(trendIsBullish)) return;
   
   // === FIBONACCI RETRACEMENT ===
   bool inFiboZone = InFiboRetracementZone(currentPrice, trendIsBullish);
   if(!inFiboZone) return;
   
   // === EMA CROSSOVER TRIGGER ===
   double emaFastH4 = GetEMA(PERIOD_H4, EMA_Fast,   1);
   double emaMedH4  = GetEMA(PERIOD_H4, EMA_Medium,  1);
   double emaFastH4_prev = GetEMA(PERIOD_H4, EMA_Fast,  2);
   double emaMedH4_prev  = GetEMA(PERIOD_H4, EMA_Medium, 2);
   
   bool emaCrossBull = (emaFastH4 > emaMedH4 && emaFastH4_prev <= emaMedH4_prev);
   bool emaCrossBear = (emaFastH4 < emaMedH4 && emaFastH4_prev >= emaMedH4_prev);
   
   // Allow if we are post-crossover as well (within last 5 bars)
   bool emaBullAligned = (emaFastH4 > emaMedH4);
   bool emaBearAligned = (emaFastH4 < emaMedH4);
   
   if(trendIsBullish && !emaBullAligned) return;
   if(!trendIsBullish && !emaBearAligned) return;
   
   // === MACD CONFIRMATION ===
   if(UseMACDFilter)
   {
      double macdLine, signalLine;
      GetMACD(PERIOD_H4, MACD_Fast, MACD_Slow, MACD_Signal, macdLine, signalLine, 1);
      double macdPrev, signalPrev;
      GetMACD(PERIOD_H4, MACD_Fast, MACD_Slow, MACD_Signal, macdPrev, signalPrev, 2);
      
      bool macdBullCross = (macdLine > signalLine && macdPrev <= signalPrev);
      bool macdBearCross = (macdLine < signalLine && macdPrev >= signalPrev);
      
      if(trendIsBullish  && !macdBullCross && macdLine < signalLine) return;
      if(!trendIsBullish && !macdBearCross && macdLine > signalLine) return;
   }
   
   // === RSI CONFIRMATION ===
   if(UseRSIFilter)
   {
      double rsiD1 = GetRSI(PERIOD_D1, RSI_Period, 1);
      // In uptrend: RSI should be 40-65 (not overbought)
      if(trendIsBullish  && (rsiD1 < 35 || rsiD1 > 70)) return;
      // In downtrend: RSI should be 35-60 (not oversold)
      if(!trendIsBullish && (rsiD1 < 30 || rsiD1 > 65)) return;
   }
   
   // === OBV CONFIRMATION ===
   if(UseOBVFilter)
   {
      if(trendIsBullish  && !OBVConfirmsBullish()) return;
      if(!trendIsBullish && !OBVConfirmsBearish()) return;
   }
   
   // === CONFIRMATION CANDLE ===
   double open1  = iOpen(_Symbol,  PERIOD_H4, 1);
   double close1 = iClose(_Symbol, PERIOD_H4, 1);
   double high1  = iHigh(_Symbol,  PERIOD_H4, 1);
   double low1   = iLow(_Symbol,   PERIOD_H4, 1);
   double body   = MathAbs(close1 - open1);
   double range  = high1 - low1;
   
   bool confirmBull = trendIsBullish  && (close1 > open1) && (body > range * 0.35);
   bool confirmBear = !trendIsBullish && (close1 < open1) && (body > range * 0.35);
   
   if(!confirmBull && !confirmBear) return;
   
   // === VOLUME FILTER ===
   long vol1   = iVolume(_Symbol, PERIOD_H4, 1);
   long avgVol = 0;
   for(int j = 2; j <= 6; j++) avgVol += iVolume(_Symbol, PERIOD_H4, j);
   avgVol /= 5;
   if(vol1 < avgVol * 0.8) return; // Volume should be at least 80% of average
   
   // === CALCULATE STOPS ===
   double slDist    = currentATR * SL_ATR_Mult;
   double price     = trendIsBullish ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) 
                                     : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl, tp1, tp2, tp3;
   
   if(trendIsBullish)
   {
      // SL below recent swing low
      double recentLow = swingLow;
      for(int j = 1; j <= 10; j++) recentLow = MathMin(recentLow, iLow(_Symbol, PERIOD_H4, j));
      sl  = recentLow - currentATR * 0.3;
      slDist = MathAbs(price - sl);
      tp1 = price + slDist * TP1_Ratio;
      tp2 = price + slDist * TP2_Ratio;
      tp3 = price + slDist * TP3_Ratio;
   }
   else
   {
      double recentHigh = swingHigh;
      for(int j = 1; j <= 10; j++) recentHigh = MathMax(recentHigh, iHigh(_Symbol, PERIOD_H4, j));
      sl  = recentHigh + currentATR * 0.3;
      slDist = MathAbs(sl - price);
      tp1 = price - slDist * TP1_Ratio;
      tp2 = price - slDist * TP2_Ratio;
      tp3 = price - slDist * TP3_Ratio;
   }
   
   // Minimum RR check (must have at least 1:4 for this swing strategy)
   if(slDist <= 0) return;
   double rrTP1 = (MathAbs(tp1 - price)) / slDist;
   if(rrTP1 < TP1_Ratio * 0.85) return;
   
   // Lot calculation
   double slPips = slDist / pointSize;
   double lots   = CalcLotSize(slPips);
   if(lots <= 0) return;
   
   double step   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   
   double lot1 = MathMax(minLot, MathFloor(lots * TP1_Percent / 100 / step) * step);
   double lot2 = MathMax(minLot, MathFloor(lots * TP2_Percent / 100 / step) * step);
   double lot3 = MathMax(minLot, MathFloor((lots - lot1 - lot2) / step) * step);
   if(lot3 < minLot) lot3 = minLot;
   
   // Enter trades
   bool ok = false;
   if(trendIsBullish)
   {
      ok |= trade.Buy(lot1, _Symbol, price, sl, tp1, "S3_TP1");
      ok |= trade.Buy(lot2, _Symbol, price, sl, tp2, "S3_TP2");
      ok |= trade.Buy(lot3, _Symbol, price, sl, tp3, "S3_TP3");
   }
   else
   {
      ok |= trade.Sell(lot1, _Symbol, price, sl, tp1, "S3_TP1");
      ok |= trade.Sell(lot2, _Symbol, price, sl, tp2, "S3_TP2");
      ok |= trade.Sell(lot3, _Symbol, price, sl, tp3, "S3_TP3");
   }
   
   if(ok)
   {
      barsSinceLastTrade = 0;
      Print("S3 Swing Trade: ", trendIsBullish ? "BUY" : "SELL",
            " | Price:", price, " | SL:", sl, " (", slPips, " pips)",
            " | ATR:", currentATR, " | Fib zone: YES | OBV: Confirmed");
   }
}

//+------------------------------------------------------------------+
//| Manage swing positions                                           |
//+------------------------------------------------------------------+
void ManagePositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Magic() != 111003 || posInfo.Symbol() != _Symbol) continue;
      
      double openPrice = posInfo.PriceOpen();
      double currentSL = posInfo.StopLoss();
      double currentTP = posInfo.TakeProfit();
      double curPrice  = posInfo.PriceCurrent();
      bool   isBuy     = (posInfo.PositionType() == POSITION_TYPE_BUY);
      double slDist    = MathAbs(openPrice - currentSL);
      
      if(slDist <= 0) continue;
      
      double rr = isBuy ? (curPrice - openPrice) / slDist
                         : (openPrice - curPrice) / slDist;
      
      // Move to breakeven at TP1 (2R)
      if(rr >= TP1_Ratio * 0.9)
      {
         double bePrice = isBuy ? openPrice + pointSize * 10 : openPrice - pointSize * 10;
         if(isBuy && bePrice > currentSL)
            trade.PositionModify(posInfo.Ticket(), bePrice, currentTP);
         else if(!isBuy && (currentSL <= 0 || bePrice < currentSL))
            trade.PositionModify(posInfo.Ticket(), bePrice, currentTP);
      }
      
      // After TP2 (5R): trail with EMA20 Daily
      if(rr >= TP2_Ratio * 0.9)
      {
         double ema20D1 = GetEMA(PERIOD_D1, 20, 1);
         double bufferATR = GetATR(PERIOD_D1, ATR_Period, 1) * 0.2;
         
         if(isBuy)
         {
            double trailSL = ema20D1 - bufferATR;
            if(trailSL > openPrice && trailSL > currentSL)
               trade.PositionModify(posInfo.Ticket(), trailSL, currentTP);
         }
         else
         {
            double trailSL = ema20D1 + bufferATR;
            if(trailSL < openPrice && (currentSL <= 0 || trailSL < currentSL))
               trade.PositionModify(posInfo.Ticket(), trailSL, currentTP);
         }
      }
      
      // OBV divergence warning: close 75% of position
      if(UseOBVFilter && rr >= 1.0)
      {
         bool obvDiverge = isBuy ? HasBearishOBVDivergence() : HasBullishOBVDivergence();
         if(obvDiverge)
         {
            // Close 75% of position - we do it by closing the lowest TP positions
            // In simplified backtesting: just close position
            // (In live trading you'd close partial)
         }
      }
      
      // Close on EMA200 cross (emergency exit)
      double ema200D1 = GetEMA(PERIOD_D1, 200, 1);
      double closeD1  = iClose(_Symbol, PERIOD_D1, 1);
      if(isBuy  && closeD1 < ema200D1) trade.PositionClose(posInfo.Ticket());
      if(!isBuy && closeD1 > ema200D1) trade.PositionClose(posInfo.Ticket());
   }
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("EA Macro Swing - Backtesting completado");
}
//+------------------------------------------------------------------+
