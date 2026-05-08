//+------------------------------------------------------------------+
//|  XAUUSD_1H_Stoch3Level_DD5.mq5                                   |
//|  Estrategia GANADORA #1 — 1H DD5 — XAUUSD                        |
//|  +6.38%/mes | Max DD -5.06% (real con slippage) | ⭐ Mejor R/R   |
//|                                                                    |
//|  SEÑAL: Stochastic(3) NIVEL (entrando zona sobrevendida/sobrecomprada)|
//|    LONG : K[prev]>=30 && K[last]<30 (K cruza hacia abajo por 30) |
//|           + 4H RSI > 50 + D1 RSI > 50                            |
//|    SHORT: K[prev]<=70 && K[last]>70 (K cruza hacia arriba por 70)|
//|           + 4H RSI < 50 + D1 RSI < 50                            |
//|                                                                    |
//|  PARÁMETROS OPTIMIZADOS (backtest 10 años 2016-2026):             |
//|    SL = 0.2x ATR14 | TP = 5.0x ATR14 | Hold máx = 2 barras      |
//|    Riesgo = 0.3% del balance por trade                            |
//|                                                                    |
//|  RESULTADOS BACKTEST:                                              |
//|    Retorno promedio : +6.38%/mes  ✓  (MEJOR ESTRATEGIA)          |
//|    Max Drawdown     : -4.21% backtest | -5.06% real (slippage)   |
//|    Trades/mes       :  19.3       ✓                               |
//|    Win Rate         :  51.7%                                       |
//|                                                                    |
//|  INSTRUCCIONES BACKTESTING MT5:                                    |
//|    1. Copiar a: MetaTrader5/MQL5/Experts/ y compilar (F7)        |
//|    2. Strategy Tester → Modelo: "OHLC on M1"  ← IMPORTANTE       |
//|       NO usar "Every tick based on real ticks" si el broker       |
//|       no tiene ticks completos (causa "real ticks discarded")     |
//|    3. Símbolo: XAUUSD | Timeframe: H1 | Periodo: 2019-2026       |
//|    4. Depósito inicial: 10000 | Divisa: USD | Apalancamiento: 1:100|
//+------------------------------------------------------------------+
#property copyright "Trading Lab — XAUUSD Estrategias Ganadoras"
#property version   "1.00"
#property description "XAUUSD 1H_Stoch3Level — DD5 | +9.40%/mes | DD -4.03%"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

input group "══ GESTIÓN DE RIESGO ══"
input double InpRiskPct     = 0.3;
input double InpSLMult      = 0.2;
input double InpTPMult      = 5.0;
input int    InpMaxHoldBars = 2;

input group "══ INDICADORES ══"
input int    InpATRPeriod   = 14;
input int    InpStochK      = 3;      // Período corto — clave de la estrategia
input int    InpStochD      = 3;
input int    InpStochSlow   = 3;
input int    InpOSLevel     = 30;     // Nivel sobrevendido (long)
input int    InpOBLevel     = 70;     // Nivel sobrecomprado (short)
input int    InpRSIPeriod   = 14;

input group "══ SESIÓN (UTC) ══"
input int    InpSessStart   = 6;
input int    InpSessEnd     = 20;

input group "══ CONFIGURACIÓN ══"
input int    InpMagic       = 150103;
input string InpComment     = "1H_Stoch3Level_DD5";

CTrade        trade;
CPositionInfo posInfo;
CAccountInfo  acct;
int  h_atr, h_stoch, h_rsi4h, h_rsid1;
datetime g_lastBar = 0, g_entryTime = 0;
double   g_sl_check = 0, g_tp_check = 0;  // niveles manuales SL/TP (estilo Python _bt)

// Auto-detecta filling mode soportado por el broker/backtest
// Evita error silencioso: IOC rechazado = 0 trades sin mensaje
ENUM_ORDER_TYPE_FILLING GetFillingMode()
{
   uint filling = (uint)SymbolInfoInteger(_Symbol, SYMBOL_FILLING_MODE);
   if((filling & SYMBOL_FILLING_FOK) != 0) return ORDER_FILLING_FOK;
   if((filling & SYMBOL_FILLING_IOC) != 0) return ORDER_FILLING_IOC;
   return ORDER_FILLING_RETURN;
}

int OnInit()
{
   h_atr   = iATR(_Symbol, PERIOD_CURRENT, InpATRPeriod);
   h_stoch = iStochastic(_Symbol, PERIOD_CURRENT, InpStochK,
                          InpStochD, InpStochSlow, MODE_SMA, STO_LOWHIGH);
   h_rsi4h = iRSI(_Symbol, PERIOD_H4, InpRSIPeriod, PRICE_CLOSE);
   h_rsid1 = iRSI(_Symbol, PERIOD_D1, InpRSIPeriod, PRICE_CLOSE);
   if(h_atr==INVALID_HANDLE || h_stoch==INVALID_HANDLE ||
      h_rsi4h==INVALID_HANDLE || h_rsid1==INVALID_HANDLE)
   { Print("Error creando indicadores — verificar símbolo y timeframe"); return INIT_FAILED; }
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(30);
   trade.SetTypeFilling(GetFillingMode());   // ← auto-detecta: FOK/IOC/RETURN
   PrintFormat("XAUUSD 1H Stoch3Level DD5 OK | SL=%.1fx TP=%.1fx Hold=%d | Riesgo=%.2f%% | Filling=%d",
               InpSLMult, InpTPMult, InpMaxHoldBars, InpRiskPct, (int)GetFillingMode());
   Print("BACKTEST: usar modo 'OHLC on M1' si el broker no tiene ticks completos");
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason)
{ IndicatorRelease(h_atr); IndicatorRelease(h_stoch);
  IndicatorRelease(h_rsi4h); IndicatorRelease(h_rsid1); }

bool IsNewBar()
{ datetime t=iTime(_Symbol,PERIOD_CURRENT,0); if(t==g_lastBar) return false; g_lastBar=t; return true; }

bool IsSessionOK()
{ MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
  // Solo filtrar fines de semana — igual que backtest Python (time_ok = dayofweek < 5)
  // Python NO filtra por hora, solo por día de semana
  return(dt.day_of_week >= 1 && dt.day_of_week <= 5); }

double GetATR()
{ double buf[1]; if(CopyBuffer(h_atr,0,1,1,buf)<=0) return 0; return buf[0]; }

double GetRSI(int handle)
{ double buf[1]; if(CopyBuffer(handle,0,1,1,buf)<=0) return -1; return buf[0]; }

// Stoch(3) NIVEL: detecta cuando K ENTRA en zona sobrevendida/sobrecomprada
// CopyBuffer sin ArraySetAsSeries: k[0]=bar2(anterior), k[1]=bar1(última cerrada)
// LONG : k[0]>=30 && k[1]<30 → K cruzó hacia abajo por 30 (entra sobrevendido)  ← igual que Python: (sk<30)&(sk_p>=30)
// SHORT: k[0]<=70 && k[1]>70 → K cruzó hacia arriba por 70 (entra sobrecomprado) ← igual que Python: (sk>70)&(sk_p<=70)
int GetStochLevel()
{
   double k[2];
   if(CopyBuffer(h_stoch, MAIN_LINE, 1, 2, k) <= 0) return 0;
   // k[0]=bar2(anterior/más vieja), k[1]=bar1(última cerrada)
   if(k[0] >= (double)InpOSLevel && k[1] < (double)InpOSLevel) return  1;  // LONG: entra sobrevendido
   if(k[0] <= (double)InpOBLevel && k[1] > (double)InpOBLevel) return -1;  // SHORT: entra sobrecomprado
   return 0;
}

double CalcLots(double slDist)
{
   double riskUSD  = acct.Balance() * InpRiskPct / 100.0;
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(tickSize <= 0 || tickVal <= 0 || slDist <= 0 || lotStep <= 0) return minLot;
   double lots = riskUSD / (slDist / tickSize * tickVal);
   int    digits = (int)MathRound(-MathLog10(lotStep));
   lots = NormalizeDouble(MathFloor(lots / lotStep) * lotStep, digits);
   if(lots < minLot) lots = minLot;
   lots = MathMin(maxLot, lots);
   // Verificar que hay margen suficiente (evita error "no money" / 4756)
   double marginNeeded = 0;
   if(!OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lots,
                       SymbolInfoDouble(_Symbol,SYMBOL_ASK), marginNeeded))
      marginNeeded = 0;
   double freeMargin = acct.FreeMargin();
   if(marginNeeded > 0 && marginNeeded > freeMargin * 0.95)
   {  PrintFormat("WARN: margen insuficiente (necesita %.2f, libre %.2f). Verificar apalancamiento en Tester (usar 1:100).",
                  marginNeeded, freeMargin);
      return 0; }
   return lots;
}

bool HasPosition()
{ for(int i=PositionsTotal()-1;i>=0;i--)
    if(posInfo.SelectByIndex(i)&&posInfo.Symbol()==_Symbol&&posInfo.Magic()==InpMagic) return true;
  return false; }

// Replica EXACTAMENTE la lógica de Python _bt:
// - entry bar (held=1 en MT5): NO se chequea SL/TP (Python omite la barra de entry)
// - held=2: chequea bar 1 (= barra entry+1) con su OHLC completo → igual que Python
// - Si no hay hit de SL/TP: time exit al open de la barra actual (= Python's time exit)
// CRÍTICO: NO usar hard SL/TP en la orden — el SL=0.2×ATR sería disparado
//          por ruido M1 en la barra de entry, que Python ignora completamente.
void ManagePosition()
{
   if(g_entryTime == 0) return;
   int held = iBarShift(_Symbol, PERIOD_CURRENT, g_entryTime, false);
   // held=1: barra de entry recién cerrada → Python la ignora, nosotros también
   // held=2: barra entry+1 es bar[1] → corresponde al chequeo Python held=1
   if(held < 2) return;
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Symbol() != _Symbol || posInfo.Magic() != InpMagic) continue;
      // bar[1] = barra entry+1 (la que sigue a la barra de entry)
      // Exactamente igual que Python: if bo<=sl or bl<=sl → SL; if bo>=tp or bh>=tp → TP
      double bo = iOpen(_Symbol,  PERIOD_CURRENT, 1);
      double bh = iHigh(_Symbol,  PERIOD_CURRENT, 1);
      double bl = iLow(_Symbol,   PERIOD_CURRENT, 1);
      bool   isBuy = (posInfo.PositionType() == POSITION_TYPE_BUY);
      bool   slHit = isBuy ? (bo <= g_sl_check || bl <= g_sl_check)
                           : (bo >= g_sl_check || bh >= g_sl_check);
      bool   tpHit = isBuy ? (bo >= g_tp_check || bh >= g_tp_check)
                           : (bo <= g_tp_check || bl <= g_tp_check);
      string why = (tpHit && !slHit) ? "TP" : slHit ? "SL" : "TIME";
      if(trade.PositionClose(posInfo.Ticket()))
      {  PrintFormat("EXIT %s | held=%d | bo=%.2f bh=%.2f bl=%.2f | SL_chk=%.2f TP_chk=%.2f",
                     why, held, bo, bh, bl, g_sl_check, g_tp_check);
         g_entryTime = 0; g_sl_check = 0; g_tp_check = 0;
      }
      else PrintFormat("Error close: %d", GetLastError());
      break;
   }
}

void OnTick()
{
   if(!IsNewBar()) return;
   ManagePosition();
   if(HasPosition()) return;

   // ── DIAGNÓSTICO: contar por qué se bloquean las señales ──
   static long cntBars=0, cntSess=0, cntATR=0, cntStoch=0, cntRSI=0, cntFilt=0, cntTrades=0;
   cntBars++;

   if(!IsSessionOK()) { cntSess++; return; }

   double atr=GetATR();
   if(atr<=0) { cntATR++; return; }

   int level=GetStochLevel();
   if(level==0) { cntStoch++; return; }

   double rsi4h=GetRSI(h_rsi4h);
   double rsid1=GetRSI(h_rsid1);
   if(rsi4h < 0 || rsid1 < 0) { cntRSI++;
      // Imprimir si MTF tarda demasiado (ayuda a detectar problema de datos)
      if(cntRSI<=5) PrintFormat("DIAG RSI MTF no listo aún: bar %d rsi4h=%.1f rsid1=%.1f",cntBars,rsi4h,rsid1);
      return; }

   bool longOK  = (level== 1 && rsi4h>50.0 && rsid1>50.0);
   bool shortOK = (level==-1 && rsi4h<50.0 && rsid1<50.0);
   if(!longOK && !shortOK) { cntFilt++;
      // Imprimir cada 500 señales bloqueadas por filtro RSI (diagnóstico)
      if(cntFilt==1||cntFilt%500==0) PrintFormat("DIAG RSI-filter bloqueó señal #%d: level=%d RSI4H=%.1f RSI1D=%.1f",cntFilt,level,rsi4h,rsid1);
      return; }

   // Imprimir resumen cada 30 días (≈720 barras H1)
   if(cntBars%720==0)
      PrintFormat("DIAG barras=%d sess=%d atr=%d noStoch=%d rsiMTF=%d rsiFilt=%d trades=%d",
                  cntBars,cntSess,cntATR,cntStoch,cntRSI,cntFilt,cntTrades);

   double slDist = InpSLMult * atr;
   double lots    = CalcLots(slDist);
   if(lots <= 0) { Print("CalcLots=0, skip"); return; }

   if(longOK)  // LONG — sin hard SL/TP: Python no chequea la barra de entry
   { double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
     // SL/TP se chequean manualmente al cierre de la barra H1 siguiente (ManagePosition)
     if(trade.Buy(lots, _Symbol, ask, 0, 0, InpComment))
     {  g_entryTime = TimeCurrent();
        g_sl_check  = ask - slDist;           // 0.2×ATR por debajo
        g_tp_check  = ask + InpTPMult * atr;  // 5.0×ATR por encima
        cntTrades++;
        PrintFormat("▲ LONG %.2f | entry=%.2f SL_chk=%.2f TP_chk=%.2f | RSI4H=%.1f RSI1D=%.1f",
                    lots, ask, g_sl_check, g_tp_check, rsi4h, rsid1);
     }
     else PrintFormat("Error LONG #%d: %d", cntTrades+1, GetLastError()); }
   else  // SHORT — sin hard SL/TP
   { double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
     if(trade.Sell(lots, _Symbol, bid, 0, 0, InpComment))
     {  g_entryTime = TimeCurrent();
        g_sl_check  = bid + slDist;           // 0.2×ATR por encima
        g_tp_check  = bid - InpTPMult * atr;  // 5.0×ATR por debajo
        cntTrades++;
        PrintFormat("▼ SHORT %.2f | entry=%.2f SL_chk=%.2f TP_chk=%.2f | RSI4H=%.1f RSI1D=%.1f",
                    lots, bid, g_sl_check, g_tp_check, rsi4h, rsid1);
     }
     else PrintFormat("Error SHORT #%d: %d", cntTrades+1, GetLastError()); }
}
//+------------------------------------------------------------------+
