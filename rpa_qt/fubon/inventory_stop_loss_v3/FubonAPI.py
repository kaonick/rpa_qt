from typing import List, Dict

from rpa_qt.fubon.fubon_auth import fubon_login
from rpa_qt.fubon.fubon_webapi import sdk_init, get_reststock, get_inventory, get_unrealized_gains_and_loses, \
    get_filled_orders, get_last_day_candle


# 假設這是Fubon API的mockup
class FubonAPI:
    def __init__(self):
        self.sdk, self.active_account = fubon_login()
        if not self.active_account:
            raise "No active account. Please log in."

        sdk_init(self.sdk)
        self.reststock = get_reststock(self.sdk)

    def get_inventory(self) -> List[Dict]:
        """從Fubon API獲取即時庫存資料。"""
        # 這裡需要實作實際的API呼叫
        # 範例資料結構
        # return [
        #     {"symbol": "2330", "name": "台積電", "quantity": 1000},
        #     {"symbol": "2454", "name": "聯發科", "quantity": 500}
        # ]
        return get_inventory(self.sdk, self.active_account)

    def get_daily_kline(self, symbols: List[str]) -> Dict[str, Dict]:
        """從Fubon API獲取當日K線資料。"""
        # 這裡需要實作實際的API呼叫
        # 範例資料結構
        # return {
        #     "2330": {"open": 600, "high": 610, "low": 595, "close": 605, "volume": 10000},
        #     "2454": {"open": 950, "high": 965, "low": 945, "close": 960, "volume": 5000}
        # }
        result={}
        for i, inv in enumerate(self.get_inventory()):
            symbol = inv.stock_no
            closing_info = get_last_day_candle(self.reststock, symbol)  # Example for a specific stock
            print(closing_info)
            result[symbol]=closing_info

        return result

    def get_unrealized_profit(self) -> List[Dict]:
        """從Fubon API獲取未實現損益資料。"""
        # 這裡需要實作實際的API呼叫
        # 範例資料結構
        # return [
        #     {"symbol": "2330", "avg_cost": 590, "init_buy_date": "20231025", "total_cost": 590000},
        #     {"symbol": "2454", "avg_cost": 940, "init_buy_date": "20231020", "total_cost": 470000}
        # ]
        return get_unrealized_gains_and_loses(self.sdk, self.active_account)

    def get_daily_trades(self) -> List[Dict]:
        """從Fubon API獲取當日委託且成交資料。"""
        # 這裡需要實作實際的API呼叫
        # 範例資料結構
        # return [
        #     {"symbol": "2330", "buy_fee": 100, "sell_fee": 0},
        #     {"symbol": "2454", "buy_fee": 50, "sell_fee": 0}
        # ]
        return  get_filled_orders(self.sdk, self.active_account)