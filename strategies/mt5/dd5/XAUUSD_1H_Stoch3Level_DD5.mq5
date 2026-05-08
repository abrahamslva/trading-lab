//+------------------------------------------------------------------+
//|  XAUUSD_1H_Stoch3Level_DD5.mq5                                   |
//|  Estrategia 1H DD5 — XAUUSD                                      |
//|                                                                    |
//|  SEÑAL: Stochastic(3) raw K cruza HACIA ABAJO por 30 (long)      |
//|         Stochastic(3) raw K cruza HACIA ARRIBA por 70 (short)    |
//|  FILTRO: EMA200 H1 — long solo si close > EMA200, short si <     |
//|                                                                    |
//|  PARÁMETROS VERIFICADOS vs backtest Python:                        |
//|    SL = 0.2 × ATR14 | TP = SL × 5.0 = 1.0 × ATR14              |
//|    Hold máx = 2 barras H1 | Riesgo = 0.3% balance por trade      |
//|                                                                    |
//|  RESULTADOS BACKTEST PYTHON 2019-2026 (filtro EMA200 H1):         |
//|    Retorno promedio : +7.11%/mes  ✓                               |
//|    Max Drawdown     : -5.90%      ✓                               |
//|    Trades/mes       :  33.9       ✓                               |
//|    Win Rate         :  37%                                         |
//|                                                                    |
//|  BUGS CORREGIDOS vs versiones anteriores:                         |
//|    v1→v3: TP era 5×ATR (correcto: 1×ATR = SL×TPMult = 0.2×5)   |
//|    v1→v3: RSI H4/D1 tenía timing mismatch broker UTC+3 vs Python |
//|           → reemplazado por EMA200 H1 (sin timing gap)           |
//|    v1→v2: Stochastic(3,3,3) suavizaba → InpStochD=1,Slow=1      |
//|    v1→v2: Cruce stoch estaba invertido (saliendo vs entrando)    |
//|    v1→v2: SL activado en barra entry por ruido M1                |
//|           → PositionModify al abrir bar siguiente                 |
//|                                                                    |
//|  INSTRUCCIONES BACKTESTING MT5:                                    |
//|    1. Copiar a MQL5\Experts\ y compilar (F7)                     |
//|    2. Símbolo: XAUUSD | Timeframe: H1 | Periodo: 2019-2026       |
//|    3. Modelo: "OHLC on M1" ← IMPORTANTE                          |
//|    4. Depósito: 10000 USD | Apalancamiento: 1:100                 |
//+------------------------------------------------------------------+
#property copyright "Trading Lab"
#property version   "3.00"
#property description "XAUUSD 1H Stoch3 EMA200 | +7%/mes | DD -5.9%"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//--- Inputs
input group "══ GESTIÓN DE RIESGO ══"
input double InpRiskPct     = 0.3;  // % del balance arriesgado por trade
input double InpSLMult      = 0.2;  // SL = InpSLMult × ATR14
input double InpTPMult      = 5.0;  // TP = SL × InpTPMult = 0.2×5 = 1.0 × ATR14
input int    InpMaxHoldBars = 1;    // HOLD MT5→Python: 1 = Python HOLD 2
                                    //   Entry bar[i+1] → check OHLC bar[i+1] → time exit bar[i+2]
                                    //   MT5 held=iBarShift(g_entryTime): 0=entry bar, 1=next bar
                                    //   held>=1 → time exit al open de bar[i+2] = Python op[i+2]
                                    //   NOTA: InpMaxHoldBars=2 deja SL/TP activos en bar[i+2] también,
                                    //   convirtiendo 30% de time exits en SL perdedores extras → WR 12%!
input int    InpLeverage    = 100;  // Apalancamiento para cálculo de lotes

input group "══ INDICADORES ══"
input int    InpATRPeriod   = 14;
input int    InpStochK      = 3;    // Raw K(3) — sin suavizado, igual que Python
input int    InpStochD      = 1;    // 1 = sin suavizado %D
input int    InpStochSlow   = 1;    // 1 = sin suavizado Slow
input int    InpOSLevel     = 30;   // Sobrevendido (long)
input int    InpOBLevel     = 70;   // Sobrecomprado (short)
input int    InpEMAPeriod   = 200;  // EMA trend filter — close > EMA para long

input group "══ CONFIGURACIÓN ══"
input int    InpMagic       = 150103;
input string InpComment     = "1H_DD5_v3";

//--- Globals
CTrade        trade;
CPositionInfo posInfo;
CAccountInfo  acct;
int      h_atr, h_stoch, h_ema;
datetime g_lastBar   = 0;
datetime g_entryTime = 0;

//+------------------------------------------------------------------+
ENUM_ORDER_TYPE_FILLING GetFillingMode()
{
   uint f = (uint)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if(f & SYMBOL_FILLING_FOK) return ORDER_FILLING_FOK;
   if(f & SYMBOL_FILLING_IOC) return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
int OnInit()
{
   h_atr   = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   h_stoch = iStochastic(_Symbol, PERIOD_CURRENT,
                          InpStochK, InpStochD, InpStochSlow,
                          MODE_SMA, STO_LOWHIGH);
   h_ema   = iMA(_Symbol, PERIOD_CURRENT, InpEMAPeriod, 0, MODE_EMA, PRICE_CLOSE);

   if(h_atr==INVALID_HANDLE || h_stoch==INVALID_HANDLE || h_ema==INVALID_HANDLE)
   { Print("ERROR: no se pudieron crear indicadores"); return INIT_FAILED; }

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(30);
   trade.SetTypeFilling(GetFillingMode());

   PrintFormat("DD5 v3 | SL=%.1fxATR TP=%.1fxSL(=%.1fxATR) Hold=%d Risk=%.2f%% Lev=1:%d",
               InpSLMult, InpTPMult, InpSLMult*InpTPMult, InpMaxHoldBars, InpRiskPct, InpLeverage);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(h_atr);
   IndicatorRelease(h_stoch);
   IndicatorRelease(h_ema);
}

//+------------------------------------------------------------------+
bool IsNewBar()
{
   datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(t == g_lastBar) return false;
   g_lastBar = t;
   return true;
}

// Solo filtrar fines de semana (igual que Python: time_ok = dayofweek < 5)
bool IsWeekday()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return(dt.day_of_week >= 1 && dt.day_of_week <= 5);
}

double GetATR()
{
   double buf[1];
   if(CopyBuffer(h_atr, 0, 1, 1, buf) <= 0) return 0;
   return buf[0];
}

// Stochastic(3) raw K NIVEL:
//   CopyBuffer sin ArraySetAsSeries: indice 0 = barra más antigua del rango
//   CopyBuffer(h, 0, 1, 2, k): copia 2 barras comenzando en shift=1
//     k[0] = bar[2] (anterior), k[1] = bar[1] (última cerrada)
//   LONG : k[0]>=30 && k[1]<30  → K cruzó ABAJO por 30 (entró sobrevendido)
//   SHORT: k[0]<=70 && k[1]>70  → K cruzó ARRIBA por 70 (entró sobrecomprado)
//   Equivalente Python: stoch_long = (sk<30) & (sk_prev>=30)
int GetStochLevel()
{
   double k[2];
   if(CopyBuffer(h_stoch, MAIN_LINE, 1, 2, k) <= 0) return 0;
   if(k[0] >= InpOSLevel && k[1] < InpOSLevel) return  1;  // LONG
   if(k[0] <= InpOBLevel && k[1] > InpOBLevel) return -1;  // SHORT
   return 0;
}

// EMA200 trend filter (H1 chart = mismos datos que Python)
// +1 = bullish (close > EMA200) → solo longs
// -1 = bearish (close < EMA200) → solo shorts
// Reemplaza RSI H4/D1 que tenía timing mismatch (broker UTC+3 vs Python UTC)
int GetTrendEMA()
{
   double emaBuf[1], closeBuf[1];
   if(CopyBuffer(h_ema, 0, 1, 1, emaBuf) <= 0) return 0;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 1, 1, closeBuf) <= 0) return 0;
   if(closeBuf[0] > emaBuf[0]) return  1;  // bull
   if(closeBuf[0] < emaBuf[0]) return -1;  // bear
   return 0;
}

double CalcLots(double slDist)
{
   double riskUSD   = acct.Balance() * InpRiskPct / 100.0;
   double tickVal   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double contract  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   if(tickSize<=0||tickVal<=0||slDist<=0||lotStep<=0||contract<=0) return minLot;

   double lots = riskUSD / (slDist / tickSize * tickVal);

   // Límite por apalancamiento (evita error 4756 en tester)
   double ask      = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double maxByLev = (ask * contract > 0) ? (acct.Balance() * InpLeverage) / (ask * contract) : maxLot;
   lots = MathMin(lots, maxByLev);

   int digits = (int)MathRound(-MathLog10(lotStep));
   lots = NormalizeDouble(MathFloor(lots / lotStep) * lotStep, digits);
   return MathMax(minLot, MathMin(maxLot, lots));
}

bool HasPosition()
{
   for(int i = PositionsTotal()-1; i >= 0; i--)
      if(posInfo.SelectByIndex(i) && posInfo.Symbol()==_Symbol && posInfo.Magic()==InpMagic)
         return true;
   return false;
}

//+------------------------------------------------------------------+
// ManagePosition — time exit a las InpMaxHoldBars barras
//
//  SL y TP se ponen DIRECTAMENTE en la orden de entrada (trade.Buy/Sell).
//  No se usa PositionModify — esto eliminaba 1 barra de delay crítico.
//
//  Lógica de salida:
//    - SL/TP: MT5 los ejecuta automáticamente via ticks M1 desde bar[i+1]
//    - Time exit: si la posición sigue abierta al abrir bar[i+2], cerrar
//
//  held = barras transcurridas desde la barra de entry
//    held=1: la barra de chequeo (bar[i+1]) ya cerró pero SL/TP no tocó
//    held≥2: time exit
//+------------------------------------------------------------------+
void ManagePosition()
{
   if(!HasPosition()) { g_entryTime=0; return; }
   if(g_entryTime == 0) return;

   int held = iBarShift(_Symbol, PERIOD_CURRENT, g_entryTime, false);

   // Time exit cuando se cumple el hold máximo
   if(held >= InpMaxHoldBars)
   {
      for(int i = PositionsTotal()-1; i >= 0; i--)
      {
         if(!posInfo.SelectByIndex(i)) continue;
         if(posInfo.Symbol()!=_Symbol || posInfo.Magic()!=InpMagic) continue;
         if(trade.PositionClose(posInfo.Ticket()))
         {
            PrintFormat("EXIT TIME held=%d pnl=%.2f", held, posInfo.Profit());
            g_entryTime=0;
         }
         else PrintFormat("Error time-exit: %d", GetLastError());
         break;
      }
   }
}

//+------------------------------------------------------------------+
void OnTick()
{
   if(!IsNewBar()) return;
   ManagePosition();
   if(HasPosition()) return;

   static long cBars=0, cWday=0, cATR=0, cEMA=0, cStoch=0, cFilt=0, cTrades=0;
   cBars++;

   if(!IsWeekday()) { cWday++; return; }

   double atr = GetATR();
   if(atr <= 0) { cATR++; return; }

   int trend = GetTrendEMA();
   if(trend == 0) { cEMA++; return; }

   int level = GetStochLevel();
   if(level == 0) { cStoch++; return; }

   bool longOK  = (level ==  1 && trend ==  1);  // K sobrevendido + bull trend
   bool shortOK = (level == -1 && trend == -1);  // K sobrecomprado + bear trend
   if(!longOK && !shortOK) { cFilt++; return; }

   // Resumen diagnóstico cada ~30 días (~720 barras H1)
   if(cBars % 720 == 0)
      PrintFormat("DIAG bars=%d wday=%d atr=%d ema=%d stoch=%d filt=%d trades=%d",
                  cBars, cWday, cATR, cEMA, cStoch, cFilt, cTrades);

   double slDist = InpSLMult * atr;        // 0.2 × ATR
   double tpDist = slDist * InpTPMult;     // 0.2 × ATR × 5.0 = 1.0 × ATR  ← CORRECTO
   double lots   = CalcLots(slDist);
   if(lots <= 0) { Print("CalcLots=0, skip"); return; }

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   if(longOK)
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double sl  = NormalizeDouble(ask - slDist, digits);  // 0.2×ATR — activo desde bar[i+1]
      double tp  = NormalizeDouble(ask + tpDist, digits);  // 1.0×ATR — activo desde bar[i+1]
      if(trade.Buy(lots, _Symbol, ask, sl, tp, InpComment))
      {
         g_entryTime = TimeCurrent();
         cTrades++;
         PrintFormat("▲ BUY  %.2f | ask=%.2f SL=%.2f TP=%.2f ATR=%.2f",
                     lots, ask, sl, tp, atr);
      }
      else PrintFormat("Error BUY: %d", GetLastError());
   }
   else
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double sl  = NormalizeDouble(bid + slDist, digits);  // 0.2×ATR
      double tp  = NormalizeDouble(bid - tpDist, digits);  // 1.0×ATR
      if(trade.Sell(lots, _Symbol, bid, sl, tp, InpComment))
      {
         g_entryTime = TimeCurrent();
         cTrades++;
         PrintFormat("▼ SELL %.2f | bid=%.2f SL=%.2f TP=%.2f ATR=%.2f",
                     lots, bid, sl, tp, atr);
      }
      else PrintFormat("Error SELL: %d", GetLastError());
   }
}
//+------------------------------------------------------------------+
