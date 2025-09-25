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
from calendar import Day

from fubon_neo.fugle_marketdata import Mode
# 建立行情查詢 WebAPI 連線 Object Instance
from fubon_neo.sdk import FubonSDK, Order

from rpa_qt.fubon.fubon_auth import fubon_login

# sdk,active_account=fubon_login()



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
            # if inv.odd is not None:
                # inv.lastday_qty=inv.lastday_qty+inv.odd.lastday_qty # 無法回寫。not writable attribute
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


def get_last_day_candle(reststock,symbol):
    """
    取得股票前一日收盤資訊
    """
    result = reststock.historical.candles(symbol=symbol, timeframe="D", count=1)
    # print(result)
    if result['data']:
        # data內含6天的日K線
        last_day_candle=result['data'][0] # 取最後一天的K線
        print(symbol,last_day_candle)
        return last_day_candle
    else:
        return None


def get_filled_orders(sdk,active_account):
    """
    取得成交回報
    """
    res = sdk.stock.filled_history(active_account)
    filled_order_list=[]
    if res.is_success:
        print("成交回報抓取成功")
        filled_data = res.data
        for filled in filled_data:
            print(filled)  # FilledOrder
            filled_order_list.append(filled)
    else:
        print("成交回報抓取失敗")

    return filled_order_list

if __name__ == '__main__':
    sdk,active_account=fubon_login()
    if not active_account:
        raise "No active account. Please log in."

    sdk_init(sdk)
    reststock=get_reststock(sdk)
    inv_list=get_inventory(sdk,active_account)
    unrealized_list=get_unrealized_gains_and_loses(sdk,active_account)
    list_filled_orders=get_filled_orders(sdk,active_account)

    for i,inv in enumerate(inv_list):
        symbol=inv.stock_no
        closing_info = get_last_day_candle(reststock, symbol)  # Example for a specific stock
        print(closing_info)

