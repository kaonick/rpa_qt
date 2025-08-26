import pandas as pd
import yfinance as yf


# ---------- 工具函數 ----------
def fetch_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    """使用 yfinance 取得資料，回傳 OHLCV（index 為日期）"""
    df = yf.download(ticker, start=start, end=end, progress=False)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    return df