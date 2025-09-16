"""
幫我用python yf-finance寫一個台股0050的回測程式，功能如下：
1. 可以設定初始張數。
2. 可以設定每月定期定額金額。
3. 可以設定近期高點回檔多少%時，停損賣出。然後將賣出後的金額放在一個變數中，分成10等份，若繼續下跌，則每下跌3%再買入1等份，直到買完為止。若反彈至賣出價格，則停止買入，就將剩下的金額全部買入。
4. 每年的股利在年底時再投入買股。


"""

import yfinance as yf
import pandas as pd

from datetime import datetime


import matplotlib.pyplot as plt

from rpa_qt.price_utils.yf_api import fetch_ohlcv, fetch_dividend


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





def backtest_0050(
        start_date: str,
        end_date: str,
        initial_shares: int,
        monthly_investment: int,
        stop_loss_percentage: float,
        reinvest_dividend: bool = True
):
    """
    回測台股0050的定期定額投資策略，並加入高點回檔分批買入的停損機制。

    參數：
    - start_date (str): 回測開始日期，格式 'YYYY-MM-DD'
    - end_date (str): 回測結束日期，格式 'YYYY-MM-DD'
    - initial_shares (int): 初始投入的張數
    - monthly_investment (int): 每月定期定額投入的金額
    - stop_loss_percentage (float): 高點回檔停損賣出的百分比 (e.g., 0.20 代表 20%)
    - reinvest_dividend (bool): 是否將股利再投入，預設為 True
    """
    # 獲取 0050 的歷史股價及股利資料
    ticker = "0050.TW"
    try:
        # data = yf.download(ticker, start=start_date, end=end_date)
        data=fetch_ohlcv(ticker, start_date, end_date)
        dividends=fetch_dividend(ticker,start_date,end_date)

        # data add dividends
        data = data.join(dividends, how='left')

        # if 'Dividends' is NaN, fill with 0
        data['Dividends'] = data['Dividends'].fillna(0)


        if data.empty:
            print("無法下載 0050.TW 的歷史資料，請檢查日期範圍或網路連線。")
            return
    except Exception as e:
        print(f"下載資料時發生錯誤：{e}")
        return

    # 初始化變數
    cash = 0
    shares = initial_shares * 1000  # 一張等於 1000 股
    total_investment = initial_shares * data['Close'].iloc[0] * 1000

    # 紀錄高點和賣出價格
    peak_price = 0
    sell_out_price = 0
    sold_cash_for_reinvest = 0
    reinvest_tranches = 0 # 分批買回的等份金額
    reinvest_times = 0 # 已經買回的等份數

    # 處理第一筆初始買入的成本
    last_investment_date = data.index[0]
    monthly_invest_date = pd.to_datetime(last_investment_date).day

    # 回測主迴圈
    for date, row in data.iterrows():
        current_price = row['Close']
        month_changed = (date.month != last_investment_date.month)

        # year_changed = (date.year != last_investment_date.year)

        # 1. 紀錄最高價
        if current_price > peak_price:
            peak_price = current_price

        # 2. 定期定額買入
        if month_changed and date.day == monthly_invest_date:
            buy_shares = monthly_investment // current_price
            shares += buy_shares
            cash -= buy_shares * current_price
            total_investment += monthly_investment
            last_investment_date = date

        # 3. 股利再投入
        if reinvest_dividend and row['Dividends'] > 0:
            dividend_cash = shares * row['Dividends']
            buy_shares = dividend_cash // current_price
            shares += buy_shares
            total_investment -= dividend_cash  # 為了正確計算投入成本，先減去股利
            print(f"在 {date.date()} 收到股利並再投資，股利總額: ${dividend_cash:,.2f}，買入 {buy_shares:,.0f} 股。")

        # 4. 停損賣出並分批買回
        if sold_cash_for_reinvest == 0 and current_price <= peak_price * (1 - stop_loss_percentage):
            # 觸發停損條件，全部賣出
            sell_out_price = current_price
            sold_cash_for_reinvest = shares * current_price
            cash += sold_cash_for_reinvest
            shares = 0
            reinvest_tranches = sold_cash_for_reinvest / 10
            print(
                f"在 {date.date()} 觸發停損賣出，價格 ${current_price:,.2f}，賣出總金額 ${sold_cash_for_reinvest:,.2f}。")

        # 停損賣出後，分批買回邏輯
        elif sold_cash_for_reinvest > 0:
            # 賣出後，若價格繼續下跌，則每下跌 3% 買回 1 等份
            if (sell_out_price - current_price) / sell_out_price >= 0.03 * (
                    10 - reinvest_times) and cash >= reinvest_tranches:
                buy_shares = reinvest_tranches // current_price
                shares += buy_shares
                cash -= buy_shares * current_price
                reinvest_tranches.append(reinvest_tranches)
                reinvest_times += 1
                print(f"在 {date.date()} 繼續下跌，價格 ${current_price:,.2f}，買回第 {len(reinvest_tranches)} 等份。")

            # 若反彈至賣出價格，則將剩餘金額全部買入
            elif current_price >= sell_out_price and cash > 0:
                buy_shares = cash // current_price
                shares += buy_shares
                cash = 0
                sold_cash_for_reinvest = 0
                reinvest_tranches = 0
                reinvest_times = 0
                print(f"在 {date.date()} 價格反彈至賣出價，將剩餘資金全部買入。")

        last_investment_date = date

    # 5. 計算最終結果
    end_date = data.index[-1]
    final_value = shares * data['Close'].iloc[-1] + cash
    total_profit = final_value - total_investment
    profit_percentage = (total_profit / total_investment) * 100 if total_investment > 0 else 0

    print("\n--- 回測結果 ---")
    print(f"回測區間：{start_date} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"初始投入成本：${initial_shares * data['Close'].iloc[0] * 1000:,.2f}")
    print(f"總投入成本 (含定期定額)：${total_investment:,.2f}")
    print(f"最終資產總值：${final_value:,.2f}")
    print(f"總損益：${total_profit:,.2f}")
    print(f"總報酬率：{profit_percentage:,.2f}%")


# 執行回測
backtest_0050(
    start_date="2004-01-01",
    end_date="2024-09-01",
    initial_shares=1,  # 初始投入 1 張
    monthly_investment=10000,  # 每月定期定額 10,000 元
    stop_loss_percentage=0.20  # 高點回檔 20% 停損
)










