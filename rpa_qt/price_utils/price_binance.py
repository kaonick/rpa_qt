import pandas as pd
# query binance price SOLUSDT
import requests
from datetime import datetime

def price_pair(currency_pair: str) -> float:
    """
    Query the current price of a cryptocurrency pair from Binance.

    :param currency_pair: The trading pair symbol (e.g., 'BTCUSDT').
    :return: The current price of the specified trading pair.
    """
    url = f'https://api3.binance.com/api/v3/ticker/price?symbol={currency_pair}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(f"Current price of {currency_pair}: {data['price']}")
        return float(data['price'])
    else:
        raise Exception(f"Error fetching price for {currency_pair}: {response.status_code} - {response.text}")


BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "SOLUSDT"
INTERVAL = "5m"
LIMIT = 500  # 取200根K線做計算

def get_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT):
    symbol=symbol.upper()
    url = f"{BINANCE_API_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()

    raw_df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    # print(raw_df.dtypes)

    # transform to best data types
    raw_df = raw_df.astype({
        "timestamp": "int64",
        "open": "float",
        "high": "float",
        "low": "float",
        "close": "float",
        "volume": "float",
        "close_time": "int64",
        "quote_asset_volume": "float",
        "trades": "int64",
        "taker_buy_base": "float",
        "taker_buy_quote": "float",
        "ignore": "float"
    })

    # raw_df add ts column as datetime from timestamp/1000.0

    raw_df['ts'] = (pd.to_datetime(raw_df['timestamp'], unit='ms', utc=True)
                    .dt.tz_convert("Asia/Taipei") # 轉換到台北時區：確保與binance websocket取的時間一致。
                    .dt.floor('ms') # 去掉毫秒，只留秒
                    .dt.tz_localize(None)  # 去掉時區信息
                    )
    # raw_df['ts'] = pd.to_datetime(raw_df['timestamp'], unit='s')

    # keep only needed columns
    raw_df = raw_df[["ts","open", "high", "low", "close", "volume"]]
    raw_df.set_index('ts', inplace=True)
    raw_df.sort_index(inplace=True)
    print(f"資料:", raw_df.tail())
    return raw_df

if __name__ == '__main__':
    # price_pair("SOLUSDT")

    get_klines(symbol="SOLUSDT", interval="1s", limit=10)
    print("---")
    get_klines(symbol="SOLUSDT", interval="1m", limit=10)
