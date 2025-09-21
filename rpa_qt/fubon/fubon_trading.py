"""
OrderResult內容：
[
  {
    ...
    buy_sell: Buy,     #買賣別 (BSAction)
    price: 66,         #原始委託價格 (float)
    quantity: 2000,    #原始委託數量 (int)
    after_price: 66.5, #有效委託價格 (float)
    after_qty: 1000,   #有效委託數量 (int)
    filled_qty: 1000,  #已成交數量 (int)
    filled_money: 66000, #成交價金 (int)
    symbol: "2881",    #股票代號 (string)
    order_no: "bA888", #委託書號 (string)
    last_time: "10:13:12.123", #最後異動時間 (string)
    ...
  }
]

"""

from fubon_neo.sdk import FubonSDK, Order
from fubon_neo.constant import TimeInForce, OrderType, PriceType, MarketType, BSAction



# https://www.fbs.com.tw/TradeAPI/docs/trading/guide/trade_example
def buy_stock(sdk,active_account,symbol, price, quantity):
    """
    買進股票
    """
    # 建立委託單內容
    order = Order(
        buy_sell=BSAction.Buy,
        symbol=symbol,
        price=price,
        quantity=quantity,
        market_type=MarketType.Common,
        price_type=PriceType.Limit,
        time_in_force=TimeInForce.ROD,
        order_type=OrderType.Stock,
        user_def="From_Py"  # optional field
    )

    sdk.stock.place_order(active_account, order)  # 下單委託

def sell_stock(sdk,active_account,symbol, price, quantity):
    """
    買進股票
    """
    # 建立委託單內容
    order = Order(
        buy_sell=BSAction.Sell,
        symbol=symbol,
        price=price,
        quantity=quantity,
        market_type=MarketType.Common,
        price_type=PriceType.Limit,
        time_in_force=TimeInForce.ROD,
        order_type=OrderType.Stock,
        user_def="From_Py"  # optional field
    )

    sdk.stock.place_order(active_account, order)  # 下單委託

# 修改價格範例
def modify_order_price(sdk,active_account,order_result, price):
    """
    修改委託單
    """
    modified_pirce = sdk.stock.make_modify_price_obj(order_result, "66.5")
    sdk.stock.modify_price(active_account, modified_pirce)

def delete_order(sdk,active_account,deleted_order):
    """
    刪除委託單
    """
    sdk.stock.cancel_order(active_account, deleted_order)

def get_order_result(sdk,active_account,order_no):
    """
    取得委託單結果
    """
    order_res = sdk.stock.order_result(active_account, order_no)
    order_result_list=[]
    if order_res.is_success:
        print("委託單結果抓取成功")
        order_data = order_res.data
        for ord in order_data:
            print(ord)  # OrderResult
            order_result_list.append(ord)
    else:
        print("委託單結果抓取失敗")

    return order_result_list
