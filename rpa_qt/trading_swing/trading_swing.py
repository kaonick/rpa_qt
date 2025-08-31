"""
🌀 波段操作的流程
包含：
yfinance 抓日線資料
指標：SMA(20/60/120)、EMA(20/60)、RSI(14)、KD(14,3)、ATR(14)
進出邏輯（長多）：趨勢濾網 + KD/RSI 動能、跌破均線或訊號反轉出場
風控：每筆固定風險、ATR 停損、停利與移動停損、手續費
回測績效指標：CAGR、Sharpe、最大回撤、勝率、盈虧比、交易次數
圖表輸出：價格+均線、KD、權益曲線
Screener：一次掃多檔的最新買賣訊號
快速用法（本機執行）：
# 單檔回測（會輸出交易清單與三張圖）
python swing_trader.py backtest --ticker 2330.TW --start 2015-01-01 --end 2025-08-30 --output 2330_backtest

# 多檔掃描（最後一天是否出現買/賣訊號）
python swing_trader.py screen --tickers 2330.TW 2317.TW 0050.TW --start 2022-01-01 --end 2025-08-30 --output screen.csv

"""
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import argparse
from datetime import datetime

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

    # ATR(TR=max(high_low, high_close, low_close)
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    return df


# --------------------------
# 回測交易策略
# --------------------------
def backtest(df, init_cash=1_000_000, risk_per_trade=0.01, atr_mult=2, fee=0.0015):
    """
    df: 包含技術指標的 DataFrame
    init_cash: 初始資金
    risk_per_trade: 每筆交易風險比例
    atr_mult: ATR 停損倍數 (平均波動：Average True Range，計算每日的波動TR，再取14日平均)
    fee: 手續費比例

    回測策略：
    1. 多頭進場條件：EMA20 > EMA60，RSI > 50，K > D
    2. 多頭出場條件：價格跌破停損價（入場價 - ATR*2），或EMA20 < EMA60，或RSI < 45
    3. 每筆交易風險控制在初始資金的 1%
    4. 手續費 0.15%
    5. 回傳交易紀錄與權益曲線
    6. 假設無法放空，僅做多單
    7. 假設無法加減碼，單一時間點僅能有一筆持倉
    8. 假設無法隔日沖
    9. 假設無法交易零股
    10. 假設無法融資融券
    11. 假設無法交易停牌或漲跌停的股票
    12. 假設無法交易除權息的股票
    13. 假設無法交易股本過小的股票（如：股本小於 10 億）
    14. 假設無法交易流動性過低的股票（如：日均量小於 1000 萬）

    風險控管：(損失上限)
    * risk_amount = init_cash * risk_per_trade
    * 每筆交易風險金額 = 初始資金 * 每筆交易風險比例

    風險控管：(計算部位大小、買進數量)
    * qty = risk_amount // (atr * atr_mult) = 計算可以承受風險的安全持股數量。
    * atr = 平均真實波動幅度 (Average True Range)，衡量每日平均波動。
    * atr_mult = 你設定的停損倍數，例如 2 倍 ATR。
    * atr * atr_mult = 預設停損幅度 (每股可能虧損)。
    👉 意思是「依照停損位置反推，最多能買多少股才不會超過風險承受範圍」

    """
    cash = init_cash
    pos = 0
    entry_price = 0
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        date, close, atr = row.name, row["Close"], row["ATR"]

        # 開倉條件（多頭）
        if pos == 0:
            if (row["EMA20"] > row["EMA60"]) and (row["RSI"] > 50) and (row["K"] > row["D"]):
                risk_amount = init_cash * risk_per_trade
                qty = risk_amount // (atr * atr_mult)
                if qty > 0:
                    entry_price = close
                    stop_loss = close - atr * atr_mult # 停損取平均振幅兩倍
                    pos = qty
                    trades.append({"date": date, "type": "BUY", "price": close, "qty": qty})
                    cash -= qty * close * (1 + fee)

        # 平倉條件
        elif pos > 0:
            stop_loss = entry_price - atr * atr_mult
            if close < stop_loss or row["EMA20"] < row["EMA60"] or row["RSI"] < 45:
                trades.append({"date": date, "type": "SELL", "price": close, "qty": pos})
                cash += pos * close * (1 - fee)
                pos = 0
                entry_price = 0

        equity = cash + pos * close
        equity_curve.append({"date": date, "equity": equity})

    df_equity = pd.DataFrame(equity_curve).set_index("date")
    df_trades = pd.DataFrame(trades)
    return df_trades, df_equity

# ----------------------------
# 繪圖
# ----------------------------
def plot_results(df, df_trades, df_equity, ticker, output_prefix):
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Close"], label="Close")
    plt.plot(df.index, df["SMA20"], label="SMA20")
    plt.plot(df.index, df["SMA60"], label="SMA60")
    plt.plot(df.index, df["SMA120"], label="SMA120")

    # trades.append({"date": date, "type": "BUY", "price": close, "qty": qty})
    # for t in trades:
    #     if t["type"] == "BUY":
    #         plt.scatter(t["date"], t["price"], marker="^", color="g")
    #     else:
    #         plt.scatter(t["date"], t["price"], marker="v", color="r")

    for i in range(len(df_trades)):
        row = df_trades.iloc[i]
        if row["type"] == "BUY":
            plt.scatter(row["date"], row["price"], marker="^", color="g", s=100, label="BUY" if i == 0 else "")
        else:
            plt.scatter(row["date"], row["price"], marker="v", color="r", s=100, label="SELL" if i == 0 else "")

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
    # equity_curve.append({"date": date, "equity": equity})
    # dates = [datetime.strptime(d["date"], '%Y-%m-%d') for d in equity]
    # values = [d["equity"] for d in equity]

    plt.figure(figsize=(12, 4))
    plt.plot(df_equity.index, df_equity["equity"], label="Equity")
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.legend()
    plt.title(f"{ticker} Equity Curve")
    plt.savefig(f"{output_prefix}_equity.png")
    plt.close()

# --------------------------
# 績效分析
# --------------------------
def performance(trades, equity, init_cash):
    if equity.empty:
        return {}

    total_return = equity["equity"].iloc[-1] / init_cash - 1
    years = (equity.index[-1] - equity.index[0]).days / 365
    cagr = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

    equity["daily_ret"] = equity["equity"].pct_change()
    sharpe = np.sqrt(252) * equity["daily_ret"].mean() / equity["daily_ret"].std()

    rolling_max = equity["equity"].cummax()
    drawdown = equity["equity"] / rolling_max - 1
    max_dd = drawdown.min()

    if not trades.empty:
        buy_trades = trades[trades["type"] == "BUY"]
        sell_trades = trades[trades["type"] == "SELL"]
        merged = pd.merge(buy_trades, sell_trades, left_index=True, right_index=True, suffixes=("_buy", "_sell"))
        merged["pnl"] = (merged["price_sell"] - merged["price_buy"]) * merged["qty_buy"]
        win_rate = (merged["pnl"] > 0).mean()
        avg_win = merged.loc[merged["pnl"] > 0, "pnl"].mean()
        avg_loss = merged.loc[merged["pnl"] <= 0, "pnl"].mean()
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
    else:
        win_rate = 0
        profit_factor = 0

    return {
        "Total Return": total_return,
        "CAGR": cagr,
        "Sharpe": sharpe,
        "Max Drawdown": max_dd,
        "Win Rate": win_rate,
        "Profit Factor": profit_factor,
        "Trades": len(trades) // 2
    }

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
        # 下載資料
        df = yf.download(args.ticker, start=args.start, end=args.end)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # 計算技術指標
        df = compute_indicators(df)

        # 回測
        df_trades, df_equity = backtest(df)
        if not df_trades.empty:
            df_trades.to_csv(f"{args.ticker}_trades.csv", index=False)
            df_equity.to_csv(f"{args.ticker}_equity.csv")

        # 計算績效
        stats = performance(df_trades, df_equity, 1_000_000)
        print("\n=== 回測績效 ===")
        for k, v in stats.items():
            print(f"{k:15}: {v:.2%}" if isinstance(v, float) else f"{k:15}: {v}")

        # 繪圖
        plot_results(df, df_trades, df_equity, args.ticker, args.output)
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