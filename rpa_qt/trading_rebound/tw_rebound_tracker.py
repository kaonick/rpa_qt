"""
針對rebound_candidates.csv的股票，追蹤其後續表現
假設條件：
    於last_date當天隔天開盤買入，依停損5%，並且移動停利(高點回落3%賣出)
    於一個月後計算報酬率。

"""

# 載入rebound_candidates.csv to df
import pandas as pd
import os
from rpa_qt.db.df_utils import csv_to_df
from rpa_qt.root import ROOT_DIR
file_path = os.path.join(ROOT_DIR, 'trading_rebound', 'rebound_candidates.csv')
df = csv_to_df(file_path)
print(df.head())


# get symbol's chinese name
symbol_path = ROOT_DIR+"/price_utils/tw_tickers_detailed.csv"
symbols_df=csv_to_df(symbol_path)
# get 'symbol' column as list
if 'symbol' in symbols_df.columns:
    symbol_name_dict = pd.Series(symbols_df.name.values,index=symbols_df.symbol).to_dict()
    # bu df's 'symbol' need to skip '.TW' or '.TWO'
    df['symbol_skip'] = df['symbol'].str.replace('.TW', '').str.replace('O', '')
    df['symbol_skip'] = df['symbol_skip'].astype(int)
    # map to symbol_name_dict's name
    df['name'] = df['symbol_skip'].map(symbol_name_dict)
    df.drop(columns=['symbol_skip'], inplace=True)

print(df.head())


#