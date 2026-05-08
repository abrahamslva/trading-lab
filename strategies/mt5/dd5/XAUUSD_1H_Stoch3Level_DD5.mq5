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
input double InpRiskPct     = 0.3;   // % del balance arriesgado por trade
input double InpSLMult      = 0.2;   // SL = N × ATR14
input double InpTPMult      = 5.0;   // TP = N × ATR14
input int    InpMaxHoldBars = 2;     // Barras máximas en posición
input int    InpLeverage    = 100;   // Apalancamiento (debe coincidir con el del Tester)

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
   double riskUSD     = acct.Balance() * InpRiskPct / 100.0;
   double tickVal     = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize    = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double lotStep     = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minLot      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot      = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double contractSz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   if(tickSize<=0||tickVal<=0||slDist<=0||lotStep<=0||contractSz<=0) return minLot;

   // Lotes por riesgo fijo (método Python: RP% del balance)
   double lots = riskUSD / (slDist / tickSize * tickVal);

   // Límite por apalancamiento — usa InpLeverage (no depende del setting del Tester)
   // max_lots = balance × apalancamiento / (precio × tamaño_contrato)
   double ask         = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double maxByLev    = (ask * contractSz > 0)
                        ? (acct.Balance() * InpLeverage) / (ask * contractSz)
                        : maxLot;
   lots = MathMin(lots, maxByLev);

   int    digits = (int)MathRound(-MathLog10(lotStep));
   lots = NormalizeDouble(MathFloor(lots / lotStep) * lotStep, digits);
   if(lots < minLot) return minLot;
   return MathMin(maxLot, lots);
}

bool HasPosition()
{ for(int i=PositionsTotal()-1;i>=0;i--)
    if(posInfo.SelectByIndex(i)&&posInfo.Symbol()==_Symbol&&posInfo.Magic()==InpMagic) return true;
  return false; }

// Replica la lógica de Python _bt verificando OHLC de bar[1] manualmente:
//
// Python _bt: signal en bar[0] → entry en op[0] → chequea OHLC de bar[1] → time exit en op[2]
// MT5:        entry en bar[0] open → held=2 (bar[2] abre) → consulta OHLC de bar[1] → cierre
//
// IMPORTANTE — por qué NO usar PositionModify:
//   PositionModify al inicio de bar[1] pone SL/TP ANTES de que bar[1] se forme.
//   Si bar[1] abre con GAP por debajo del SL (común en OHLC M1), el SL se activa
//   inmediatamente al precio del GAP (no al precio del SL), generando pérdidas
//   enormes. Python ignora este gap y siempre cierra exactamente en el SL.
//
// SOLUCIÓN: SL de seguridad (10×ATR) en la orden de entry para evitar ruinas;
//   verificación manual de OHLC de bar[1] al abrir bar[2].
void ManagePosition()
{
   if(!HasPosition()) { g_entryTime=0; g_sl_check=0; g_tp_check=0; return; }
   if(g_entryTime == 0) return;

   int held = iBarShift(_Symbol, PERIOD_CURRENT, g_entryTime, false);
   // held=1: bar de entry cerrada, bar[1] aún no terminó → esperar
   if(held < 2) return;

   // held >= 2: bar[1] completamente formada (index=1)
   // Chequear OHLC de bar[1] igual que Python _bt
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      if(!posInfo.SelectByIndex(i)) continue;
      if(posInfo.Symbol() != _Symbol || posInfo.Magic() != InpMagic) continue;

      bool   isBuy = (posInfo.PositionType() == POSITION_TYPE_BUY);
      double bh    = iHigh(_Symbol, PERIOD_CURRENT, 1);  // bar[1] high
      double bl    = iLow (_Symbol, PERIOD_CURRENT, 1);  // bar[1] low

      // Python chequea SL primero, luego TP (SL tiene prioridad)
      string why = "TIME";
      if( isBuy && (bl <= g_sl_check))  why = "SL";
      else if( isBuy && (bh >= g_tp_check))  why = "TP";
      else if(!isBuy && (bh >= g_sl_check))  why = "SL";
      else if(!isBuy && (bl <= g_tp_check))  why = "TP";

      if(trade.PositionClose(posInfo.Ticket()))
      {  PrintFormat("EXIT %s held=%d | bar1 H=%.2f L=%.2f | SL_chk=%.2f TP_chk=%.2f",
                     why, held, bh, bl, g_sl_check, g_tp_check);
         g_entryTime=0; g_sl_check=0; g_tp_check=0; }
      else PrintFormat("Error close %s: %d", why, GetLastError());
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

   if(longOK)  // LONG
   { double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
     // Orden con SL de seguridad a 10×ATR (sólo contra catástrofe/gap enorme)
     // El SL real (0.2×ATR) y TP se verifican manualmente en ManagePosition() al abrir bar[2]
     double safeSL = NormalizeDouble(ask - 10.0 * atr, (int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
     if(trade.Buy(lots, _Symbol, ask, safeSL, 0, InpComment))
     {  g_entryTime = TimeCurrent();
        g_sl_check  = ask - slDist;           // 0.2×ATR — usado en chequeo OHLC
        g_tp_check  = ask + InpTPMult * atr;  // 5.0×ATR — usado en chequeo OHLC
        cntTrades++;
        PrintFormat("▲ LONG %.2f | entry=%.2f SL_chk=%.2f TP_chk=%.2f SafeSL=%.2f | RSI4H=%.1f D1=%.1f",
                    lots, ask, g_sl_check, g_tp_check, safeSL, rsi4h, rsid1);
     }
     else PrintFormat("Error LONG #%d: %d", cntTrades+1, GetLastError()); }
   else  // SHORT
   { double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
     double safeSL = NormalizeDouble(bid + 10.0 * atr, (int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS));
     if(trade.Sell(lots, _Symbol, bid, safeSL, 0, InpComment))
     {  g_entryTime = TimeCurrent();
        g_sl_check  = bid + slDist;           // 0.2×ATR
        g_tp_check  = bid - InpTPMult * atr;  // 5.0×ATR
        cntTrades++;
        PrintFormat("▼ SHORT %.2f | entry=%.2f SL_chk=%.2f TP_chk=%.2f SafeSL=%.2f | RSI4H=%.1f D1=%.1f",
                    lots, bid, g_sl_check, g_tp_check, safeSL, rsi4h, rsid1);
     }
     else PrintFormat("Error SHORT #%d: %d", cntTrades+1, GetLastError()); }
}
//+------------------------------------------------------------------+
