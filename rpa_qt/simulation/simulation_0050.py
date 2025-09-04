from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

def get_current_price():
    # 即時抓取股價的程式碼, 使用 yfinance API
    import yfinance as yf
    ticker = "0050.TW"
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return data['Close'].iloc[-1]
    else:
        # raise ValueError("無法取得股價資料")
        print("無法取得股價資料，使用預設價格 52.0")
        return 52.0








def simulate_0050(
        months=120, # 模擬月數
        annual_return=0.06,  # 年化報酬率
        dividend_yield=0.025,  # 股利殖利率
        dividend_growth=0.0,  # 股利成長率
        monthly_invest=111000,  # 每月定期定額金額
        initial_shares=33,  # 已有張數
):
    # 計算月化報酬率
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    monthly_dividend_growth = (1 + dividend_growth) ** (1 / 12) - 1

    # 初始數據
    current_price = get_current_price()
    price = current_price
    shares = initial_shares * 1000  # 張數轉股數 (1張=1000股)
    total_dividend = 0
    results = []

    for m in range(1, months + 1):
        # 股價更新
        price *= (1 + monthly_return)

        # 當月股利
        dividend_per_share = price * dividend_yield / 12
        total_dividend += shares * dividend_per_share

        # 定期定額買入
        buy_shares = monthly_invest // price
        shares += buy_shares

        # 淨值
        net_value = shares * price + total_dividend

        now_ym = (datetime.now() + pd.DateOffset(months=m)).strftime("%Y-%m")
        results.append([now_ym,m, price, shares, total_dividend, net_value])

        # 股利殖利率成長
        dividend_yield *= (1 + monthly_dividend_growth)

    # 轉成 DataFrame
    df = pd.DataFrame(results, columns=["YM","Month", "Price", "Shares", "Cumulative_Dividend", "Net_Value"])

    # 繪圖
    plt.figure(figsize=(10, 6))
    plt.plot(df["Month"], df["Net_Value"], label="Net Value")
    plt.xlabel("Month")
    plt.ylabel("Net Value (NTD)")
    plt.title("0050 Long-term Investment Simulation")
    plt.legend()
    plt.grid(True)
    plt.show()

    return df


def simulate_0050_v2(
    months=120,
    annual_return=0.06,          # 年化報酬率
    dividend_yield=0.025,        # 股利殖利率
    dividend_growth=0.0,         # 股利成長率
    invest_schedule=[{1: 111000}], # 投入計畫 [{起始月: 每月投入金額}]
    initial_shares=33,           # 已有張數 (張)

):
    # 計算月化報酬率 & 股利成長率
    monthly_return = (1 + annual_return) ** (1/12) - 1
    monthly_dividend_growth = (1 + dividend_growth) ** (1/12) - 1

    # 初始數據
    current_price = get_current_price()
    price = current_price
    shares = initial_shares * 1000   # 張數轉股數
    total_dividend = 0
    monthly_invest = 0

    # 把分段投入 schedule 整理成 dict
    schedule_dict = {}
    for s in invest_schedule:
        schedule_dict.update(s)

    results = []

    for m in range(1, months + 1):
        # 如果 schedule 有新金額，更新 monthly_invest
        if m in schedule_dict:
            monthly_invest = schedule_dict[m]

        # 更新股價
        price *= (1 + monthly_return)

        # 當月股利（存起來，等年底一次投入）
        dividend_per_share = price * dividend_yield / 12
        total_dividend += shares * dividend_per_share

        # 定期定額買股
        buy_shares = monthly_invest // price
        shares += buy_shares

        # 如果遇到第1月(或每12個月)，將股利再投入
        if m % 12 == 1 and total_dividend > 0:
            reinvest_shares = total_dividend // price
            shares += reinvest_shares
            total_dividend -= reinvest_shares * price  # 剩下換不到整股的股利保留

        # 淨值
        net_value = shares * price + total_dividend

        # results.append([m, price, shares, total_dividend, net_value, monthly_invest])
        now_ym = (datetime.now() + pd.DateOffset(months=m)).strftime("%Y-%m")
        results.append([now_ym,m, price, shares, total_dividend, net_value, monthly_invest])

        # 股利殖利率成長
        dividend_yield *= (1 + monthly_dividend_growth)

    # 轉成 DataFrame
    df = pd.DataFrame(results, columns=["YM","Month", "Price", "Shares", "Cumulative_Dividend", "Net_Value", "Monthly_Invest"])

    # 繪圖
    plt.figure(figsize=(10, 6))
    plt.plot(df["Month"], df["Net_Value"], label="Net Value")
    plt.xlabel("Month")
    plt.ylabel("Net Value (NTD)")
    plt.title("0050 Long-term Investment Simulation (with Dividend Reinvestment)")
    plt.legend()
    plt.grid(True)
    plt.show()

    return df


# 範例執行
df = simulate_0050(
    months=120,
    annual_return=0.06,
    dividend_yield=0.025,
    dividend_growth=0.0,
    monthly_invest=111000,
    initial_shares=33,
)

pd.set_option("display.float_format", "{:,.2f}".format)
print(df.tail(12))  # 顯示前12個月

df2 = simulate_0050_v2(
    months=120,
    annual_return=0.06,
    dividend_yield=0.025,
    dividend_growth=0.0,
    invest_schedule=[{1: 111000}, {37: 60000}, {61: 10000}], #
    initial_shares=33,
)

pd.set_option("display.float_format", "{:,.2f}".format)
print(df2.tail(12))  # 顯示前12個月

df3 = simulate_0050_v2(
    months=120,
    annual_return=0.06,
    dividend_yield=0.025,
    dividend_growth=0.0,
    invest_schedule=[{1: 40000}, {37: 20000}, {61: 10000}], #
    initial_shares=150,
)
print(df3.tail(12))  # 顯示前12個月