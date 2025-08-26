"""
✅ Binance 官方支援的 kline interval
文件：https://binance-docs.github.io/apidocs/spot/en/#kline-candlestick-streams

支援的 interval 有：
1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h,
1d, 3d, 1w, 1M

return format:
{
  "e": "kline",         // Event type
  "E": 123456789,       // Event time
  "s": "BNBBTC",        // Symbol
  "k": {
    "t": 123400000,     // Kline start time (ms)
    "T": 123460000,     // Kline close time (ms)
    "s": "BNBBTC",      // Symbol
    "i": "1m",          // Interval
    "f": 100,           // First trade ID
    "L": 200,           // Last trade ID
    "o": "0.0010",      // Open price
    "c": "0.0020",      // Close price
    "h": "0.0025",      // High price
    "l": "0.0015",      // Low price
    "v": "1000",        // Base asset volume
    "n": 100,           // Number of trades
    "x": false,         // Is this kline closed?
    "q": "1.0000",      // Quote asset volume
    "V": "500",         // Taker buy base asset volume
    "Q": "0.500",       // Taker buy quote asset volume
    "B": "123456"       // Ignore
  }
}


"""
import json
import threading
import pandas as pd
import websocket
from datetime import datetime

from rpa_qt.price_utils.price_binance import get_klines


def resample_to_5s(df_1s):
    # 假設 df_1s 的 index 是 datetime，包含 ohlcv
    df_5s = df_1s.resample("5S").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()
    return df_5s

class KlineWebSocket:
    def __init__(self, symbol="btcusdt", interval="1s",dfs:{}={}):
        self.dfs = dfs  # 儲存不同 interval 的 K 線資料
        self.symbol = symbol.lower()
        self.interval = interval
        self.df = pd.DataFrame(columns=["open","high","low","close","volume"])
        raw_df=get_klines(symbol=self.symbol, interval=self.interval, limit=500)
        self.df= raw_df
        self.latest_price = None
        self.threads = []

    def _create_ws(self, interval):
        url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{interval}"

        def on_message(ws, message):
            data = json.loads(message)
            k = data["k"]
            ts = datetime.fromtimestamp(k["t"] / 1000.0)

            # volume = float(k["v"])
            # print(f"volume: {volume}, type: {type(volume)}")
            new_row = pd.DataFrame({
                "open": [float(k["o"])],
                "high": [float(k["h"])],
                "low": [float(k["l"])],
                "close": [float(k["c"])],
                "volume": [float(k["v"])]
            }, index=[ts])
            self.latest_price = float(k["c"])


            # # 更新對應 interval 的 DataFrame
            # self.df = pd.concat(
            #     [self.df[~self.df.index.isin(new_row.index)], new_row]
            # ).sort_index()
            #
            # self.dfs[interval] = self.df # 改成每次都重設，確保有更新。


            if interval not in self.dfs:
                 self.dfs[interval] = self.df
            self.dfs[interval] = pd.concat(
                [ self.dfs[interval][~ self.dfs[interval].index.isin(new_row.index)], new_row]
            ).sort_index()
            # print("add one row:", new_row)

        def on_error(ws, error):
            print(f"WebSocket {self.symbol} {interval} 錯誤:", error)

        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket {self.symbol} {interval} 關閉")

        # 原作法：若發生異常，會直接停止，不會重連
        # ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
        # ws.run_forever()

        # 新作法：會重新連線。
        # Auto-reconnect loop
        while True:
            try:
                ws = websocket.WebSocketApp(
                    url,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                ws.run_forever(ping_interval=20, ping_timeout=10)  # 可設定 ping 保活
            except Exception as e:
                print(f"[EXCEPTION] WebSocket {self.symbol} {interval} exception: {e}")
            print(f"[RECONNECT] Reconnecting WebSocket {self.symbol} {interval} in 5s...")
            time.sleep(5)

    def start(self):
        """啟動所有 interval 的 WebSocket"""
        t = threading.Thread(target=self._create_ws, args=(self.interval,), daemon=True)
        t.start()
        self.threads.append(t)


    def get_latest_price(self):
        return self.latest_price

    def get_dataframe(self)-> pd.DataFrame:
        return self.df


if __name__ == '__main__':
    # 建立 WebSocket 物件，訂閱 1m & 5m
    kws = KlineWebSocket(symbol="btcusdt", interval="1s")
    kws.start()

    interval_2="1m"
    kws2 = KlineWebSocket(symbol="btcusdt", interval=interval_2)
    kws2.start()

    # 之後可以取資料
    import time
    for i in range(10):
        time.sleep(10)  # 等 10 秒接收資料

        print("1s 最新價格:", kws.get_latest_price())
        print("1s 資料:", kws.get_dataframe().tail())
        print(f"{interval_2} 最新價格:", kws2.get_latest_price())
        print(f"{interval_2} 資料:", kws2.get_dataframe().tail())