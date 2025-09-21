"""
/intraday/tickers - 股票或指數列表（依條件查詢）
/intraday/ticker/{symbol} - 股票基本資料（依代碼查詢）
/intraday/quote/{symbol} - 股票即時報價（依代碼查詢）
/intraday/candles/{symbol} - 股票價格Ｋ線（依代碼查詢）
/intraday/trades/{symbol} - 股票成交明細（依代碼查詢）
/intraday/volumes/{symbol} - 股票分價量表（依代碼查詢）
/snapshot/quotes/{market} - 股票行情快照（依市場別）
/snapshot/movers/{market} - 股票漲跌幅排行（依市場別）
/snapshot/actives/{market} - 股票成交量值排行（依市場別）
/historical/candles/{symbol} - 取得 1 年內歷史股價（依代碼查詢）
/historical/stats/{symbol} - 取得近 52 週股價數據（依代碼查詢）

"""



from fubon_neo.fugle_marketdata import Mode
# 建立行情查詢 WebAPI 連線 Object Instance
from fubon_neo.sdk import FubonSDK, Order

from rpa_qt.fubon.fubon_auth import fubon_login

sdk,active_account=fubon_login()



def sdk_init(sdk,mode=Mode.Normal):
    sdk.init_realtime(mode)  # 建立行情連線
    print("行情連線建立OK")
    return sdk

def get_reststock(sdk):
    reststock = sdk.marketdata.rest_client.stock # 建立行情查詢 WebAPI 連線 Object Instance
    return reststock

def get_wsstock(sdk):
    wsstock = sdk.marketdata.websocket_client.stock
    return wsstock


def get_inventory(sdk, active_account):
    inv_res = sdk.accounting.inventories(active_account)
    inv_list=[]
    if inv_res.is_success:
        print("庫存抓取成功")
        inv_data = inv_res.data
        for inv in inv_data:
            print(inv) # InventoryData
            inv_list.append(inv)
    else:
        print("庫存抓取失敗")

    return inv_list

def get_unrealized_gains_and_loses(sdk, active_account):
    res = sdk.accounting.unrealized_gains_and_loses(active_account)
    upnl_list=[]
    if res.is_success:
        print("未實現損益抓取成功")
        upnl_data = res.data
        for upnl in upnl_data:
            print(upnl)  # UnrealizedData
            upnl_list.append(upnl)
    else:
        print("未實現損益抓取失敗")

    return upnl_list






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