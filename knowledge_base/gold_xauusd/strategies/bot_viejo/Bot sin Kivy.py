import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from binance import Client
import decimal, math
import warnings, os

warnings.filterwarnings('ignore')

class TradingStrategy:
    def __init__(self, token, api_key, api_secret):
        self.token = token
        self.api_key = os.environ.get('BINANCE_API_KEY', '')
        self.api_secret = os.environ.get('BINANCE_API_SECRET', '')
        self.client = Client(self.api_key, self.api_secret)
        self.saldo_money = 0
        self.saldo_monedas = 0
        self.status = ''
        self.ultimo_precio = 1
        self.sma_20_anterior = 1
        self.precio_anterior = 1
        self.df = pd.DataFrame([])
        self.precision = 5

    def cargar_ordenes(self):      
        start = pd.to_datetime(dt.datetime.now() - pd.Timedelta(days=60))
        end = dt.datetime.now()
        interval = '1h'

        klines = self.client.get_historical_klines(
            str(self.token),
            interval,
            int(dt.datetime.timestamp(start) * 1000),
            int(dt.datetime.timestamp(end) * 1000),
            limit=1000
        )
        self.df_order = pd.DataFrame(klines)
        self.df_order.columns = [
            'OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime',
            'QuoteAssetVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'
        ]
        self.df_order['Date'] = pd.to_datetime(self.df_order.OpenTime, unit='ms')
        self.df_order['Close'] = self.df_order['Close'].apply(lambda x: float(x))
        self.df_order['SMA_20'] = self.df_order['Close'].rolling(window=20).mean()
        minimo = self.df_order['Close'][0]
        maximo = self.df_order['Close'][0]
        for index, row in self.df_order.sort_values(by=['Date'], ascending=True).iterrows():
            minimo = (row['Close'] if row['Close'] < minimo else minimo)
            maximo = (row['Close'] if row['Close'] > maximo else maximo)
            self.df_order.at[index, 'Minimo'] = minimo
            self.df_order.at[index, 'Maximo'] = maximo
        self.df_order = self.df_order[['Date', 'Close', 'Minimo', 'Maximo', 'SMA_20']]
        print(self.df_order.tail())

    def compra_venta(self):
        self.saldo_money, self.monedas = self.devolver_balances()
        fecha = self.df_order['Date'].iloc[-1]
        precio = self.df_order['Close'].iloc[-1]
        self.precio_anterior = self.df_order['Close'].iloc[-2]
        minimo = self.df_order['Minimo'].iloc[-1]
        maximo = self.df_order['Maximo'].iloc[-1]
        sma_20 = self.df_order['SMA_20'].iloc[-1]
        self.sma_20_anterior = self.df_order['SMA_20'].iloc[-2]     
        media = (minimo + maximo) / 2
        baja = True if (maximo / minimo > 1.1 and precio / media < 0.965) else False

        if (self.status == '' or self.status == 'venta') and int(self.saldo_money) > 0:
            cantidad = decimal.Decimal(self.saldo_money) / decimal.Decimal(precio)
            cantidad = decimal.Decimal(cantidad).quantize(decimal.Decimal('.00001'), rounding=decimal.ROUND_DOWN)
            if cantidad > 0:
                try:
                    self.client.create_order(
                        symbol=str(self.token),
                        side='SELL',
                        type='MARKET',
                        quantity=float(cantidad)
                    )
                    self.status = 'compra'
                    self.saldo_monedas = decimal.Decimal(self.saldo_money) / decimal.Decimal(precio)
                    self.saldo_monedas = decimal.Decimal(self.saldo_monedas).quantize(decimal.Decimal('.00001'), rounding=decimal.ROUND_DOWN)
                    self.saldo_money = 0
                    print(fecha, " Compra:", self.saldo_monedas, "Precio:", precio, "Minimo:", minimo, "Maximo:", maximo, "SMA_20:", sma_20)
                except:
                    pass
        elif self.status == 'compra' and self.saldo_monedas > 0:
            if baja or (self.precio_anterior < self.sma_20_anterior and precio >= sma_20):
                try:
                    self.client.create_order(
                        symbol=str(self.token),
                        side='BUY',
                        type='MARKET',
                        quantity=float(self.saldo_monedas)
                    )
                    self.status = 'venta'
                    self.saldo_money, self.saldo_monedas = self.devolver_balances()
                    print(fecha, " Venta:", self.saldo_monedas, "Precio:", precio, "Minimo:", minimo, "Maximo:", maximo, "SMA_20:", sma_20)
                except:
                    pass

               
        if (self.status == '' or self.status == 'venta') and int(self.saldo_money) > 0:
            cantidad = decimal.Decimal(self.saldo_money) / decimal.Decimal(precio)
            cantidad = decimal.Decimal(cantidad).quantize(decimal.Decimal('.00001'), rounding=decimal.ROUND_DOWN)
            if cantidad > 0:
               
                try:
                    self.client.create_order(
                        symbol=str(self.token),
                        side='SELL',
                        type='MARKET',
                        quantity=float(cantidad)
                    )
                    self.status = 'compra'
                    self.saldo_monedas = decimal.Decimal(self.saldo_money) / decimal.Decimal(precio)
                    self.saldo_monedas = decimal.Decimal(self.saldo_monedas).quantize(decimal.Decimal('.00001'), rounding=decimal.ROUND_DOWN)
                    self.saldo_money = 0
                    print(fecha, " Compra:", self.saldo_monedas, "Precio:", precio, "Minimo:", minimo, "Maximo:", maximo, "SMA_20:", sma_20)
                except:
                    pass

        elif self.status == 'compra' and self.saldo_monedas > 0:
            if baja or (self.precio_anterior < self.sma_20_anterior and precio >= sma_20):
                try:
                    self.client.create_order(
                        symbol=str(self.token),
                        side='BUY',
                        type='MARKET',
                        quantity=float(self.saldo_monedas)
                    )
                    self.status = 'venta'
                    self.saldo_money, self.saldo_monedas = self.devolver_balances()
                    print(fecha, " Venta:", self.saldo_monedas, "Precio:", precio, "Minimo:", minimo, "Maximo:", maximo, "SMA_20:", sma_20)
                except:
                    pass

    def devolver_balances(self):
        try:
            account_info = self.client.get_account()
            balances = account_info['balances']
            for balance in balances:
                if balance['asset'] == 'USDT':
                    saldo_money = balance['free']
                elif balance['asset'] == str(self.token):
                    saldo_monedas = balance['free']
            return saldo_money, saldo_monedas
        except:
            return 0, 0

if __name__ == '__main__':
    token = 'BTCUSDT'
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'

    strategy = TradingStrategy(token, api_key, api_secret)
    strategy.cargar_ordenes()
    while True:
        strategy.compra_venta()


