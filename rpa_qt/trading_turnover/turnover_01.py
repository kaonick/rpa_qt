"""
均線黃金交叉策略
"""

import time
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.animation as animation

BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "SOLUSDT"
INTERVAL = "5m"
LIMIT = 500  # 取200根K線做計算

def get_klines(symbol=SYMBOL, interval=INTERVAL, limit=LIMIT):
    url = f"{BINANCE_API_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close"] = df["close"].astype(float)
    return df

def check_signal(df):
    # EMA
    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA60"] = df["close"].ewm(span=60, adjust=False).mean()
    df["EMA120"] = df["close"].ewm(span=120, adjust=False).mean()

    # 計算SMA
    # SMA
    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["SMA60"] = df["close"].rolling(window=60).mean()
    df["SMA120"] = df["close"].rolling(window=120).mean()



    # ============ 交易訊號 ============
    df["long_signal"] = (
            (df["EMA20"] > df["EMA60"]) & (df["EMA60"] > df["EMA120"]) &
            (df["SMA20"] > df["SMA60"]) & (df["SMA60"] > df["SMA120"])
    )

    df["short_signal"] = (
            (df["EMA20"] < df["EMA60"]) & (df["EMA60"] < df["EMA120"]) &
            (df["SMA20"] < df["SMA60"]) & (df["SMA60"] < df["SMA120"])
    )

    last = df.iloc[-1]

    if last["long_signal"]:
        return "BUY"

    if last["short_signal"]:
        return "SELL"

    return "HOLD"

def animate(i):
    df = get_klines()
    signal = check_signal(df)

    plt.cla()
    plt.plot(df["timestamp"], df["close"], label="Price", color="black")
    # plt.plot(df["timestamp"], df["SMA20"], label="SMA20", color="blue")
    # plt.plot(df["timestamp"], df["SMA60"], label="SMA60", color="orange")
    # plt.plot(df["timestamp"], df["SMA120"], label="SMA120", color="red")

    plt.plot(df["timestamp"], df["EMA20"], label="EMA20", color="green")
    plt.plot(df["timestamp"], df["EMA60"], label="EMA60", color="purple")
    plt.plot(df["timestamp"], df["EMA120"], label="EMA120", color="brown")

    # 標記 BUY / SELL
    last_time = df.iloc[-1]["timestamp"]
    last_price = df.iloc[-1]["close"]
    if signal == "BUY":
        plt.scatter(last_time, last_price, marker="^", color="green", s=150, label="BUY")
    elif signal == "SELL":
        plt.scatter(last_time, last_price, marker="v", color="red", s=150, label="SELL")

    plt.title(f"SOLUSDT 5m Strategy | Signal: {signal}")
    plt.xlabel("Time")
    plt.ylabel("Price (USDT)")
    plt.legend(loc="upper left")
    plt.tight_layout()

def main():
    fig = plt.figure(figsize=(12, 6))
    ani = animation.FuncAnimation(fig, animate, interval=300000)  # 每5分鐘更新
    plt.show()

if __name__ == "__main__":
    main()
