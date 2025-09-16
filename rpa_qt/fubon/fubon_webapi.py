
# 建立行情查詢 WebAPI 連線 Object Instance
from fubon_neo.sdk import FubonSDK, Order

from rpa_qt.fubon.fubon_auth import fubon_login

sdk=fubon_login()

sdk.init_realtime()  # 建立行情連線
reststock = sdk.marketdata.rest_client.stock # 建立行情查詢 WebAPI 連線 Object Instance


result=reststock.intraday.tickers(type='EQUITY', exchange="TWSE", isNormal=True) # 股票或指數列表（依條件查詢）

stock_list = ["8467", "9103", "2330"]  # 抽樣查詢之股票 symbols

print(f"資料長度: {len(result['data'])}\n")

for ticker in result["data"]:
    if ticker["symbol"] in stock_list:
        print(ticker)

# 取得股票資訊 (依股票代碼查詢)
result = reststock.intraday.ticker(symbol='2330')
print(result)

# 股票即時報價（依代碼查詢）
result = reststock.intraday.quote(symbol="2330")
print(result)

# 股票價格Ｋ線（依代碼查詢）
result = reststock.intraday.candles(symbol='2330', timeframe=5)
print(result)

# 股票成交明細（依代碼查詢）
result = reststock.intraday.trades(symbol='2330')
print(result)

# 股票分價量表（依代碼查詢）
result = reststock.intraday.volumes(symbol='2330')
print(result)

#
#
# if __name__ == '__main__':
#     get_tiker_list()