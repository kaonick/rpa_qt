import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import argparse
import os

# ----------------------------
# 技術指標計算
# ----------------------------
def compute_indicators(df):
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA60"] = df["Close"].rolling(60).mean()
    df["SMA120"] = df["Close"].rolling(120).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA60"] = df["Close"].ewm(span=60).mean()

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    # KD
    low14 = df["Low"].rolling(14).min()
    high14 = df["High"].rolling(14).max()
    rsv = (df["Close"] - low14) / (high14 - low14 + 1e-9) * 100
    df["K"] = rsv.ewm(com=2).mean()
    df["D"] = df["K"].ewm(com=2).mean()

    # ATR
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    return df

# ----------------------------
# 交易策略邏輯
# ----------------------------
def backtest(df, init_capital=1000000, fee=0.001425, risk_per_trade=0.01):
    df = compute_indicators(df).dropna()
    cash = init_capital
    position = 0
    entry_price = 0
    equity_curve = []
    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        date = row.name
        close = row["Close"]

        # 持有部位檢查停損 / 停利
        if position > 0:
            atr = row["ATR"]
            stop_loss = entry_price - 2 * atr
            take_profit = entry_price + 4 * atr
            if close < stop_loss or close > take_profit:
                cash += position * close * (1 - fee)
                trades.append((date, "SELL", close, position))
                position = 0
                entry_price = 0

        # 開倉訊號
        if position == 0:
            if (
                row["SMA20"] > row["SMA60"] > row["SMA120"]
                and row["K"] > row["D"]
                and row["RSI"] > 50
            ):
                atr = row["ATR"]
                risk_amount = init_capital * risk_per_trade
                position_size = int(risk_amount / (2 * atr))
                if position_size > 0:
                    position = position_size
                    entry_price = close
                    cash -= position * close * (1 + fee)
                    trades.append((date, "BUY", close, position))

        equity = cash + position * close
        equity_curve.append(equity)

    df["Equity"] = equity_curve
    return df, trades

# ----------------------------
# 繪圖
# ----------------------------
def plot_results(df, trades, ticker, output_prefix):
    # 畫製
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Close"], label="Close")
    plt.plot(df.index, df["SMA20"], label="SMA20")
    plt.plot(df.index, df["SMA60"], label="SMA60")
    plt.plot(df.index, df["SMA120"], label="SMA120")
    for t in trades:
        if t[1] == "BUY":
            plt.scatter(t[0], t[2], marker="^", color="g")
        else:
            plt.scatter(t[0], t[2], marker="v", color="r")
    plt.legend()
    plt.title(f"{ticker} Price & Trades")
    plt.savefig(f"{output_prefix}_price.png")
    plt.close()

    # KD 指標
    plt.figure(figsize=(12, 4))
    plt.plot(df.index, df["K"], label="K")
    plt.plot(df.index, df["D"], label="D")
    plt.legend()
    plt.title(f"{ticker} KD Indicator")
    plt.savefig(f"{output_prefix}_kd.png")
    plt.close()

    # 權益曲線
    plt.figure(figsize=(12, 4))
    plt.plot(df.index, df["Equity"], label="Equity")
    plt.legend()
    plt.title(f"{ticker} Equity Curve")
    plt.savefig(f"{output_prefix}_equity.png")
    plt.close()

# ----------------------------
# CLI
# ----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="backtest", choices=["backtest", "screen"])
    parser.add_argument("--ticker", default="2330.TW", help="股票代號")
    parser.add_argument("--tickers", nargs="+", help="多檔股票代號")
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2025-01-01")
    parser.add_argument("--output", default="output")
    args = parser.parse_args()

    if args.mode == "backtest":
        df = yf.download(args.ticker, start=args.start, end=args.end)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df, trades = backtest(df)
        plot_results(df, trades, args.ticker, args.output)
        df.to_csv(f"{args.output}_equity.csv")
        print("回測完成，結果已輸出")

    elif args.mode == "screen":
        results = []
        for t in args.tickers:
            df = yf.download(t, start=args.start, end=args.end)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df = compute_indicators(df).dropna()
            last = df.iloc[-1]
            signal = "NONE"
            if last["SMA20"] > last["SMA60"] > last["SMA120"] and last["K"] > last["D"] and last["RSI"] > 50:
                signal = "BUY"
            elif last["K"] < last["D"] and last["RSI"] < 40:
                signal = "SELL"
            results.append((t, last.name, signal, last["Close"]))
        out = pd.DataFrame(results, columns=["Ticker", "Date", "Signal", "Close"])
        out.to_csv(args.output, index=False)
        print("掃描完成，結果已輸出")

if __name__ == "__main__":
    main()
