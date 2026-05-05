import pandas as pd
import unicorn_binance_websocket_api as uni

bwsam= uni.BinanceWebSocketApiManager (exchange="binance.com")

bwsam.create_stream(kiline_1m, "BTCUSDT", output="UnicornFy")
def obtener_precio(data):
    return

    data = bwsam.pop_stream_data_from_stream_buffer()
    print(data)