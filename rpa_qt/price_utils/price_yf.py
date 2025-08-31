import pandas as pd
import yfinance as yf


# ---------- 工具函數 ----------
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
    df = yf.download(ticker, start=start, end=end, progress=False) # 預設會加入tiker，例如：Open/2330.TW
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    if header_lower_case:
        df.columns = ['open', 'high', 'low', 'close', 'volume']
    else:
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df

if __name__ == '__main__':
    df = fetch_ohlcv('2330.TW', '2023-01-01', '2024-01-01', header_lower_case=True)
    print(df.head())