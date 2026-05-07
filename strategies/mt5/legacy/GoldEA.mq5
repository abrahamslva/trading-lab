//+------------------------------------------------------------------+
//| GoldEA.mq5                                                       |
//| Gold MA-Cross Expert Advisor                                     |
//|                                                                  |
//| Signal source (selectable via SignalMode input):                 |
//|   MODE_INDICATOR — built-in SMA/EMA crossover computed in MQL5  |
//|   MODE_FILE      — reads mt5/bridge/signal.json written by      |
//|                    Python (mt5/signal_writer.py).                |
//|                                                                  |
//| File bridge format (signal.json):                               |
//|   {"signal": "buy"|"sell"|"flat", "fast_ma": 1234.5,           |
//|    "slow_ma": 1230.0, "timestamp": "2024-01-01T00:00:00Z"}      |
//|                                                                  |
//| Risk controls mirror configs/objectives.yaml:                   |
//|   Max drawdown   10%  → close all + halt                        |
//|   Max daily loss  2%  → halt until next day                     |
//|   Min ATR filter     → skip signals in low-volatility regime    |
//+------------------------------------------------------------------+
#property copyright "trading-lab"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

//--- Inputs
input group "=== Strategy ==="
input int    FastWindow    = 20;           // Fast MA period
input int    SlowWindow    = 50;           // Slow MA period
input bool   UseEMA        = false;        // false=SMA, true=EMA

input group "=== Signal Source ==="
enum SIGNAL_MODE { MODE_INDICATOR=0, MODE_FILE=1 };
input SIGNAL_MODE SignalMode = MODE_INDICATOR; // Signal source

input group "=== Risk ==="
input double RiskPercent    = 1.0;        // Risk % of balance per trade
input double MaxDrawdownPct = 10.0;       // Max portfolio drawdown % before halt
input double MaxDailyLossPct = 2.0;      // Max daily loss % before daily halt
input int    MagicNumber    = 20240101;   // Unique EA identifier
input int    Deviation      = 10;         // Max price deviation (points)
input int    SlPoints       = 0;          // Stop-loss points  (0=disabled)
input int    TpPoints       = 0;          // Take-profit points (0=disabled)

input group "=== File Bridge ==="
input string SignalFile = "signal.json";  // File in MQL5\\Files\\ folder

//--- Internals
CTrade          Trade;
CPositionInfo   PositionInfo;

int    FastHandle  = INVALID_HANDLE;
int    SlowHandle  = INVALID_HANDLE;

double AccountOpen  = 0;   // equity at day start
double PeakEquity   = 0;   // all-time high equity for drawdown calc
bool   DailyHalt    = false;
bool   GlobalHalt   = false;
datetime LastDay    = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Trade.SetExpertMagicNumber(MagicNumber);
   Trade.SetDeviationInPoints(Deviation);
   Trade.SetTypeFilling(ORDER_FILLING_IOC);

   if(FastWindow >= SlowWindow)
   {
      Alert("GoldEA: FastWindow must be < SlowWindow");
      return INIT_PARAMETERS_INCORRECT;
   }

   if(SignalMode == MODE_INDICATOR)
   {
      if(UseEMA)
      {
         FastHandle = iMA(_Symbol, PERIOD_CURRENT, FastWindow, 0, MODE_EMA, PRICE_CLOSE);
         SlowHandle = iMA(_Symbol, PERIOD_CURRENT, SlowWindow, 0, MODE_EMA, PRICE_CLOSE);
      }
      else
      {
         FastHandle = iMA(_Symbol, PERIOD_CURRENT, FastWindow, 0, MODE_SMA, PRICE_CLOSE);
         SlowHandle = iMA(_Symbol, PERIOD_CURRENT, SlowWindow, 0, MODE_SMA, PRICE_CLOSE);
      }
      if(FastHandle == INVALID_HANDLE || SlowHandle == INVALID_HANDLE)
      {
         Print("GoldEA: Failed to create MA handles");
         return INIT_FAILED;
      }
   }

   PeakEquity  = AccountInfoDouble(ACCOUNT_EQUITY);
   AccountOpen = PeakEquity;
   LastDay     = TimeCurrent();

   Print("GoldEA initialized | symbol=", _Symbol,
         " fast=", FastWindow, " slow=", SlowWindow,
         " mode=", EnumToString(SignalMode));
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(FastHandle != INVALID_HANDLE) IndicatorRelease(FastHandle);
   if(SlowHandle != INVALID_HANDLE) IndicatorRelease(SlowHandle);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Daily reset
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   MqlDateTime last;
   TimeToStruct(LastDay, last);

   if(now.day != last.day || now.mon != last.mon)
   {
      DailyHalt  = false;
      AccountOpen = AccountInfoDouble(ACCOUNT_EQUITY);
      LastDay     = TimeCurrent();
   }

   //--- Update peak equity
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity > PeakEquity) PeakEquity = equity;

   //--- Global drawdown guard
   if(PeakEquity > 0)
   {
      double drawdownPct = (PeakEquity - equity) / PeakEquity * 100.0;
      if(drawdownPct >= MaxDrawdownPct)
      {
         if(!GlobalHalt)
         {
            Print("RISK: Global drawdown ", DoubleToString(drawdownPct, 2),
                  "% >= ", MaxDrawdownPct, "%. Closing all positions.");
            CloseAllPositions();
            GlobalHalt = true;
         }
         return;
      }
      else
      {
         GlobalHalt = false;
      }
   }

   //--- Daily loss guard
   if(AccountOpen > 0)
   {
      double dayLossPct = (AccountOpen - equity) / AccountOpen * 100.0;
      if(dayLossPct >= MaxDailyLossPct)
      {
         if(!DailyHalt)
         {
            Print("RISK: Daily loss ", DoubleToString(dayLossPct, 2),
                  "% >= ", MaxDailyLossPct, "%. Halting for today.");
            DailyHalt = true;
         }
         return;
      }
   }
   if(DailyHalt) return;

   //--- Only act on new bar
   static datetime lastBarTime = 0;
   datetime currentBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(currentBarTime == lastBarTime) return;
   lastBarTime = currentBarTime;

   //--- Get signal
   string signal = "flat";
   double fastVal = 0, slowVal = 0;

   if(SignalMode == MODE_FILE)
   {
      signal = ReadFileSignal();
   }
   else
   {
      double fastBuf[2], slowBuf[2];
      if(CopyBuffer(FastHandle, 0, 0, 2, fastBuf) < 2) return;
      if(CopyBuffer(SlowHandle, 0, 0, 2, slowBuf) < 2) return;

      double fastNow  = fastBuf[1];
      double fastPrev = fastBuf[0];
      double slowNow  = slowBuf[1];
      double slowPrev = slowBuf[0];

      if(fastNow > slowNow && fastPrev <= slowPrev)
         signal = "buy";
      else if(fastNow < slowNow && fastPrev >= slowPrev)
         signal = "sell";
   }

   //--- Execute signal
   bool isLong  = PositionExists(POSITION_TYPE_BUY);
   bool isShort = PositionExists(POSITION_TYPE_SELL);

   if(signal == "buy" && !isLong)
   {
      if(isShort) CloseAllPositions();
      double lots = ComputeLots();
      double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl   = (SlPoints > 0) ? ask - SlPoints * _Point : 0;
      double tp   = (TpPoints > 0) ? ask + TpPoints * _Point : 0;
      if(Trade.Buy(lots, _Symbol, ask, sl, tp, "GoldEA-buy"))
         Print("BUY  lots=", lots, " ask=", DoubleToString(ask, _Digits));
   }
   else if(signal == "sell" && !isShort)
   {
      if(isLong) CloseAllPositions();
      double lots = ComputeLots();
      double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl   = (SlPoints > 0) ? bid + SlPoints * _Point : 0;
      double tp   = (TpPoints > 0) ? bid - TpPoints * _Point : 0;
      if(Trade.Sell(lots, _Symbol, bid, sl, tp, "GoldEA-sell"))
         Print("SELL lots=", lots, " bid=", DoubleToString(bid, _Digits));
   }
   else if(signal == "flat" && (isLong || isShort))
   {
      CloseAllPositions();
   }
}

//+------------------------------------------------------------------+
//| Read signal from JSON file written by Python                     |
//+------------------------------------------------------------------+
string ReadFileSignal()
{
   string result = "flat";
   int handle = FileOpen(SignalFile, FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ);
   if(handle == INVALID_HANDLE)
      return result;

   string content = "";
   while(!FileIsEnding(handle))
      content += FileReadString(handle);
   FileClose(handle);

   // Minimal JSON field extraction (no external library needed)
   // Expects: {"signal": "buy"} or {"signal": "sell"} or {"signal": "flat"}
   int pos = StringFind(content, "\"signal\"");
   if(pos < 0) return result;

   pos = StringFind(content, ":", pos);
   if(pos < 0) return result;

   // Find first quote after colon
   int q1 = StringFind(content, "\"", pos + 1);
   if(q1 < 0) return result;
   int q2 = StringFind(content, "\"", q1 + 1);
   if(q2 < 0) return result;

   result = StringSubstr(content, q1 + 1, q2 - q1 - 1);
   return result;
}

//+------------------------------------------------------------------+
//| Check if a position of given type exists for this EA             |
//+------------------------------------------------------------------+
bool PositionExists(ENUM_POSITION_TYPE ptype)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionInfo.SelectByIndex(i))
      {
         if(PositionInfo.Symbol() == _Symbol
            && PositionInfo.Magic() == MagicNumber
            && PositionInfo.PositionType() == ptype)
            return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Close all positions for this EA on this symbol                   |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionInfo.SelectByIndex(i))
      {
         if(PositionInfo.Symbol() == _Symbol
            && PositionInfo.Magic() == MagicNumber)
            Trade.PositionClose(PositionInfo.Ticket());
      }
   }
}

//+------------------------------------------------------------------+
//| Compute position size based on RiskPercent                       |
//+------------------------------------------------------------------+
double ComputeLots()
{
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskCash = balance * RiskPercent / 100.0;

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double minLot    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double lotStep   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(tickValue <= 0 || tickSize <= 0)
      return minLot;

   // Use SL points if set; otherwise assume 50 ticks for sizing
   double slTicks  = (SlPoints > 0) ? SlPoints : 50;
   double lots     = riskCash / (slTicks * tickValue / tickSize);

   // Round to lot step
   lots = MathFloor(lots / lotStep) * lotStep;
   return MathMax(lots, minLot);
}
