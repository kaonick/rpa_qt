from typing import List

import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

from rpa_qt.db.df_utils import df_to_csv, csv_to_df


# get TW and TWO stock symbols from yfinance
def get_tw_tickers() -> List[str]:
    url = "https://raw.githubusercontent.com/datasets/taiwan-stock-list/master/data/tw_stock_list.csv"
    df = pd.read_csv(url)
    # 篩選上市（TSE）與上櫃（OTC）
    df = df[df['Exchange'].isin(['TSE', 'OTC'])]
    # 取得代碼並加上後綴
    df['Ticker'] = df['Code'].astype(str) + '.TW'
    return df['Ticker'].tolist()



def fetch_twse_tickers():
    df_columns=['symbol', 'name', 'ISIN_Code','ipo_date', 'market', 'industry', 'CFIC_Code', 'note']
    df= pd.DataFrame(columns=df_columns)
    # tickers = {}
    for mode, label in [(2, 'TWSE'), (4, 'TPEX')]:
        url = f"https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"
        res = requests.get(url)
        res.encoding = 'big5'
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', class_='h4')
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td') # 0.代號 簡稱,1.ISIN Code,2.上市日,3.市場別,4.產業別,5.CFIC Code,6.備註
            if len(cols) >= 6:
                code_name = cols[0].text.split('\u3000')
                if len(code_name) > 1:
                    symbol = code_name[0].strip()
                    if len(symbol) >4:
                        # 非股票代號，跳過
                        continue
                    name = code_name[1].strip()
                ISIN_Code = cols[1].text.strip()
                ipo_date = cols[2].text.strip()
                market = cols[3].text.strip()
                industry = cols[4].text.strip()
                CFIC_Code = cols[5].text.strip()
                note = cols[6].text.strip() if len(cols) > 6 else ''
                # Append a new row to the DataFrame
                # df.at[len(df)] = [symbol, name, ISIN_Code, ipo_date, market, industry, CFIC_Code, note]
                df.loc[len(df)] = [symbol, name, ISIN_Code, ipo_date, market, industry, CFIC_Code, note]
                # df = df.append({
                #     "symbol": symbol,
                #     "name": name,
                #     "ISIN_Code": ISIN_Code,
                #     "ipo_date": ipo_date,
                #     "market": market,
                #     "industry": industry,
                #     "CFIC_Code": CFIC_Code,
                #     "note": note
                # }, ignore_index=True)
    return df



# filter daily volume 必須大於 1000張以上
def filter_by_volume(df: pd.DataFrame, min_volume: int = 1000) -> pd.DataFrame:
    filtered_symbols = []
    for symbol in df['symbol']:
        ticker = symbol + ('.TW' if df[df['symbol'] == symbol]['market'].values[0] == '上市' else '.TWO')
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        if not hist.empty and hist['Volume'].mean() >= min_volume * 1000:  # 1000張 = 1000*1000股
            filtered_symbols.append(symbol)
    return df[df['symbol'].isin(filtered_symbols)]

def tmp_get_tw_tickers():
    tickers_df = fetch_twse_tickers()
    print(f"共取得 {len(tickers_df)} 檔台股代號")
    df_to_csv(tickers_df, "tw_tickers_detailed.csv")

def tmp_filter_by_volume():
    # load tw_tickers_detailed.csv
    df = csv_to_df(file_path="tw_tickers_detailed.csv")
    print(f"原始資料共 {len(df)} 檔股票")
    filtered_df = filter_by_volume(df, min_volume=1000)
    print(f"篩選後共 {len(filtered_df)} 檔股票")
    # save to tw_tickers_big_volume.csv
    df_to_csv(filtered_df, "tw_tickers_big_volume.csv")

    df=csv_to_df(file_path="tw_tickers_detailed.csv")
    print(df.head())


# def get_tw_tickers_yf() -> pd.DataFrame:
#     symbols = [code + ('.TW' if exch == 'TWSE' else '.TWO') for code, exch in tickers.items()]
#     # 範例取得 10 檔股票的收盤價
#     df = yf.download(" ".join(symbols[:10]), period="1mo")
#     print(df)
#     return df

if __name__ == '__main__':
    # tmp_get_tw_tickers()
    tmp_filter_by_volume()

