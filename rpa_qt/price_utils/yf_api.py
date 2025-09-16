import pandas as pd
import yfinance as yf


# ---------- 工具函數 ----------
# 收盤價
def fetch_ohlcv(ticker: str, start: str, end: str,header_lower_case=False) -> pd.DataFrame:
    """
    使用 yfinance 取得資料，回傳 OHLCV（index 為日期）
    ticker: 股票代號，例如 '2330.TW'
    start: 起始日期，格式 'YYYY-MM-DD'
    end: 結束日期，格式 'YYYY-MM-DD'
    header_lower_case: 是否將欄位名稱轉為小寫，預設 False
    回傳 DataFrame，欄位為 ['Open', 'High', 'Low', 'Close', 'Volume'] 或小寫版本
    """


    """使用 yfinance 取得資料，回傳 OHLCV（index 為日期）"""
    # df = yf.download(ticker, start=start, end=end, progress=False) # 預設會加入tiker，例如：Open/2330.TW
    df = yf.download(ticker, start=start, end=end, auto_adjust=False) # 預設會加入tiker，例如：Open/2330.TW
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    if header_lower_case:
        df.columns = ['open', 'high', 'low', 'close', 'volume']
    else:
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df


def fetch_dividend(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    使用 yfinance 取得股息資料，回傳 DataFrame（index 為日期）
    ticker: 股票代號，例如 '2330.TW'
    start: 起始日期，格式 'YYYY-MM-DD'
    end: 結束日期，格式 'YYYY-MM-DD'
    回傳 DataFrame，欄位為 ['Dividend']
    """
    stock = yf.Ticker(ticker)
    dividends = stock.dividends

    # 將帶有時區的索引轉換為無時區
    # dividends.index = dividends.index.tz_localize(None) # 或者用下面的 astype
    dividends.index = dividends.index.tz_localize(None)

    dividends = dividends[(dividends.index >= pd.to_datetime(start)) & (dividends.index <= pd.to_datetime(end))]
    dividends = dividends.to_frame(name='Dividends')
    return dividends

def fetch_quarter_financials(ticker: str):
    """
    使用yf取得季度財報資料，
    內容包括：最近四季的「營收」、「營業利益」、「稅後淨利」、「每股盈餘」、
    去年同期的「營收」、「營業利益」、「稅後淨利」、「每股盈餘」，
    與上季比較的「營收成長率」、「營業利益成長率」、「稅後淨利成長率」、「每股盈餘成長率」
    與去年同期比較的「營收成長率」、「營業利益成長率」、「稅後淨利成長率」、「每股盈餘成長率」
    累計四季的「營收」、「營業利益」、「稅後淨利」、「每股盈餘」，
    去年同期累計的「營收」、「營業利益」、「稅後淨利」、「每股盈餘」，
    與去年同期累計比較的「營收成長率」、「營業利益成長率」、「稅後淨利成長率」、「每股盈餘成長率」
    """
    stock = yf.Ticker(ticker)

    # 抓季度財報
    fin = stock.quarterly_financials.T   # 損益表
    eps = stock.quarterly_earnings       # EPS 與 Revenue
    # 透過 .dividends 屬性取得股息資料
    dividends = stock.dividends

    # 取最近 8 季 (避免去年同期抓不到)
    fin = fin.head(8)
    eps = eps.head(8)

    # 對齊資料
    df = pd.DataFrame({
        "Revenue": eps["Revenue"],                                # 營收
        "Operating Income": fin["Operating Income"],              # 營業利益
        "Net Income": fin["Net Income"],                          # 稅後淨利
        "EPS": eps["Earnings"]                                    # 每股盈餘
    })

    # 最近四季
    recent = df.head(4)
    last_year = df.iloc[4:8].head(4)

    # 計算成長率
    def growth_rate(now, prev):
        if prev == 0 or pd.isna(prev):
            return None
        return (now - prev) / abs(prev) * 100

    # 與上季比較
    qoq = recent.iloc[0:2].apply(lambda row: None)  # placeholder
    qoq_growth = {}
    for col in ["Revenue", "Operating Income", "Net Income", "EPS"]:
        qoq_growth[col + " QoQ Growth"] = [
            growth_rate(recent[col].iloc[i], recent[col].iloc[i+1])
            for i in range(3)
        ]
    qoq_growth = pd.DataFrame(qoq_growth)

    # 與去年同期比較
    yoy_growth = {}
    for col in ["Revenue", "Operating Income", "Net Income", "EPS"]:
        yoy_growth[col + " YoY Growth"] = [
            growth_rate(recent[col].iloc[i], last_year[col].iloc[i])
            for i in range(4)
        ]
    yoy_growth = pd.DataFrame(yoy_growth)

    # 累計
    recent_sum = recent.sum()
    last_year_sum = last_year.sum()

    cumulative_growth = {}
    for col in ["Revenue", "Operating Income", "Net Income", "EPS"]:
        cumulative_growth[col + " YoY Growth"] = growth_rate(
            recent_sum[col], last_year_sum[col]
        )
    cumulative_growth = pd.Series(cumulative_growth)

    return {
        "Recent 4 Quarters": recent,
        "Last Year Same Quarters": last_year,
        "QoQ Growth": qoq_growth,
        "YoY Growth": yoy_growth,
        "Recent Sum (TTM)": recent_sum,
        "Last Year Sum (TTM)": last_year_sum,
        "Cumulative Growth": cumulative_growth
    }

def tmp_quarter_financials(ticker: str):
    """
    取得季度財報資料
    ticker: 股票代號，例如 '2330.TW'
    回傳 DataFrame，欄位為 ['Revenue', 'Operating Income', 'Net Income', 'EPS']
    """
    stock = yf.Ticker(ticker)
    df = stock.quarterly_financials.T
    df = df[['Total Revenue', 'Operating Income', 'Net Income', 'Basic EPS']]
    df.columns = ['Revenue', 'Operating Income', 'Net Income', 'EPS']
    return df



if __name__ == '__main__':
    # df = fetch_ohlcv('2330.TW', '2023-01-01', '2024-01-01', header_lower_case=True)
    # print(df.head())

    tiker="2330.TW"

    tiker="1734.TW" # 杏輝
    # df = tmp_quarter_financials(tiker)
    # print(f"{tiker} 財報資料：")
    # print(df.head())

    fetch_quarter_financials(tiker)