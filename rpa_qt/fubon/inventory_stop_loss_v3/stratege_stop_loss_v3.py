"""
參照PROMPT生成。
每日交易系統流程：
1. 每日收盤後，自動從Fubon API中讀取資料。
2. 讀取現股記錄檔並與API資料比對，若有新增股票則新增記錄。
3. 針對每一筆現股記錄進行資料更新和計算。
4. 判斷目前所在的階段（停損階段或停利階段）。
5. 依據條件決定應採策略（停損、停利、第一次加碼、第二次加碼、或觀望）。
6. 依據策略生成交易記錄。並從API自動下單。
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Union

from rpa_qt.backend.config import dbPool
from rpa_qt.backend.model.models import StockRecord, TradeRecord, get_now_code, get_now_day
from rpa_qt.fubon.inventory_stop_loss_v3.FubonAPI import FubonAPI


def fee_buy(amount: float) -> float:
    """計算買進手續費"""
    fee = max(20, amount * 0.001425)
    return fee

def fee_sell(amount: float) -> float:
    """計算賣出手續費"""
    fee = max(20, amount * 0.001425)
    tax_fee= amount * 0.003
    return fee+tax_fee


class DataProcessor:
    def __init__(self):
        self.api = FubonAPI()

    def fetch_data(self) -> Dict[str, Union[List, Dict]]:
        """
        1. 每日收盤後，自動從Fubon API中讀取資料。
        """
        print(f"1. 每日收盤後，自動從Fubon API中讀取資料...")
        inventory_data = self.api.get_inventory()
        symbols = [item.stock_no for item in inventory_data]
        kline_data = self.api.get_daily_kline(symbols)
        unrealized_data = self.api.get_unrealized_profit()
        trade_data = self.api.get_daily_trades()

        return {
            "inventory": inventory_data,
            "kline": kline_data,
            "unrealized": unrealized_data,
            "trades": trade_data
        }


class TradingSystem:
    def __init__(self):
        self.processor = DataProcessor()
        self.stop_loss_rate = 0.05  # 停損標準，5%
        self.take_profit_rate = 0.03  # 停利標準，3%

    def run_daily_process(self):
        """
        主要流程控制函式，依序執行所有步驟。
        """
        # 1. 讀取API資料
        api_data = self.processor.fetch_data()

        # 2. 讀取現股記錄檔並與API資料比對
        stock_records = self._get_stock_records()
        symbols_from_api = {item.stock_no for item in api_data['inventory']}
        symbols_from_db = {record.symbol for record in stock_records}

        all_symbols = symbols_from_api.union(symbols_from_db)

        # 創建或更新現股記錄檔
        self._update_or_create_records(stock_records, all_symbols, api_data)

        # 3. 處理並更新每一筆記錄
        self._process_all_records()

        # 4. 判斷並執行策略
        new_trades = self._execute_strategies()

        # 5. 儲存更新後的記錄和交易記錄
        self._save_updates(new_trades)

        print("每日交易系統流程執行完畢。")

    def _get_stock_records(self) -> List[StockRecord]:
        """從資料庫讀取所有現股記錄檔。"""
        with dbPool.get_db_with() as session:
            return session.query(StockRecord).all()

    def _update_or_create_records(self, stock_records: List[StockRecord], all_symbols: set, api_data: Dict):
        """
        根據API資料更新或新增現股記錄。
        """
        with dbPool.get_db_with() as session:
            db_symbols = {rec.symbol for rec in stock_records}

            # 新增不存在於資料庫的記錄
            new_symbols = all_symbols - db_symbols
            for symbol in new_symbols:
                # 假設這裡需要從API獲取更詳細的初始資料
                # 這裡僅為範例，實際需要更多邏輯來獲取股票名稱等
                unrealized = next((d for d in api_data['unrealized'] if d.stock_no == symbol), None)
                if not unrealized:
                    continue  # 忽略沒有未實現損益資料的股票

                inv = next((d for d in api_data['inventory'] if d.stock_no == symbol), None)
                if not inv:
                    continue  # 忽略沒有

                new_record = StockRecord(
                    order_code=get_now_code(),
                    symbol=symbol,
                    name=symbol, #    api_data['inventory'][0]['name'],  # 假設這裡能找到名稱
                    init_buy_date=unrealized.date,
                    quantity=unrealized.today_qty,
                    avg_cost_price=unrealized.cost_price,
                    current_price=0,
                    highest_price=0,
                    buy_fee=0,
                    sell_fee=0,
                    profit_rate=0,
                    stop_loss_rate=self.stop_loss_rate,
                    take_profit_rate=self.take_profit_rate,
                    stop_loss_price=0,
                    take_profit_begin_price=0,
                    take_profit_price=0,
                    fallback_rate=0,
                    current_status="stop_loss_stage",
                    total_cost=0,
                    trade_history=f"{get_now_day()}: 初始買進 {unrealized.today_qty/1000} 張",
                    data_time=get_now_code()
                )
                session.add(new_record)

            session.commit()

    def _process_all_records(self) -> List[StockRecord]:
        """
        3. 針對每一筆現股記錄進行資料更新和計算。
        """
        with dbPool.get_db_with() as session:
            records = session.query(StockRecord).all()
            api_data = self.processor.fetch_data()

            for record in records:
                # 更新資料
                inventory = next((d for d in api_data['inventory'] if d.stock_no == record.symbol), None)
                unrealized = next((d for d in api_data['unrealized'] if d.stock_no == record.symbol), None)
                kline = api_data['kline'].get(record.symbol)
                trades = next((d for d in api_data['trades'] if d.stock_no == record.symbol), None)

                # if inventory:
                #     # record.symbol = inventory['symbol']
                #     # record.name = inventory['name']  # 假設API提供名稱

                if unrealized:
                    record.quantity = unrealized.today_qty # 假設API提供數量
                    record.avg_cost_price = unrealized.cost_price

                if kline:
                    record.current_price = kline['close']
                    # record.current_volume = kline['volume']

                if trades:
                    #　？？？？
                    record.buy_fee = record.buy_fee+trades.get('buy_fee', record.buy_fee)
                    record.sell_fee = record.sell_fee+trades.get('sell_fee', record.sell_fee)

                # 4. 進行計算
                record.highest_price = max(record.highest_price, record.current_price)
                record.profit_rate = ((record.current_price - record.avg_cost_price) / record.avg_cost_price) * 100
                record.stop_loss_price = record.avg_cost_price * (1 - self.stop_loss_rate)
                record.take_profit_begin_price = record.avg_cost_price * (1 + 2 * self.stop_loss_rate)
                record.take_profit_price = record.highest_price * (1 - self.take_profit_rate)
                record.fallback_rate = ((record.highest_price - record.current_price) / record.highest_price) * 100

                # 5. 判斷目前所在的階段
                if record.current_price <= record.take_profit_begin_price:
                    record.current_status = "stop_loss_stage"
                elif record.current_price >= record.take_profit_begin_price:
                    record.current_status = "take_profit_stage"

            session.commit()
            session.close()
        # return records

    def _execute_strategies(self) -> List[TradeRecord]:
        """
        6. 依據條件決定應採策略。
        7. 依據策略生成交易記錄。
        """
        with dbPool.get_db_with() as session:
            records = session.query(StockRecord).all()

            new_trades = []
            for record in records:
                holding_days = (datetime.now() - datetime.strptime(record.init_buy_date, "%Y/%m/%d")).days

                # 決定策略
                if record.current_price <= record.stop_loss_price:
                    record.strategy = "stop_loss"
                elif record.current_price >= record.take_profit_begin_price and record.current_price <= record.take_profit_price:
                    record.strategy = "take_profit"
                elif record.current_price >= record.take_profit_begin_price and record.profit_rate > 10:
                    record.strategy = "first_add"
                elif record.current_price >= record.take_profit_begin_price and record.profit_rate > 20:
                    record.strategy = "second_add"
                elif holding_days >= 60:
                    record.strategy = "timeout_sell"
                else:
                    record.strategy = "observe"

                # 根據策略生成交易記錄
                if record.strategy in ["stop_loss", "take_profit", "timeout_sell"]:

                    quantity=record.quantity  # 假設賣出全部持股
                    amount = record.current_price * quantity
                    fee = fee_sell(amount)
                    net_amount=amount-fee

                    trade = TradeRecord(
                        order_code=get_now_code(),
                        symbol=record.symbol,
                        name=record.name,
                        trade_date=datetime.now().strftime("%Y%m%d"),
                        change_reason="sell",
                        quantity=quantity,
                        trade_type="market",  # 假設為市價單
                        status="order_success",  # 假設委託成功
                        price=record.current_price,
                        amount=amount,
                        fee=fee,
                        net_amount=net_amount,
                        description=f"執行{record.strategy}策略",
                        data_time=get_now_code()
                    )
                    new_trades.append(trade)

                elif record.strategy in ["first_add", "second_add"]:

                    quantity=record.quantity * 0.5  # 假設加碼半張
                    amount = record.current_price * quantity
                    fee = fee_buy(amount)
                    net_amount=amount+fee
                    trade = TradeRecord(
                        order_code=get_now_code(),
                        symbol=record.symbol,
                        name=record.name,
                        trade_date=datetime.now().strftime("%Y%m%d"),
                        change_reason="buy",
                        quantity=quantity,  # 假設加碼半張
                        trade_type="market",
                        status="order...yet",
                        price=record.current_price,
                        amount=amount,
                        fee=fee,
                        net_amount=net_amount,
                        description=f"執行{record.strategy}策略",
                        data_time=get_now_code()
                    )
                    new_trades.append(trade)

                record.trade_history = record.trade_history+"\n"+ f"{get_now_day()}: 執行 {record.strategy} 策略 {new_trades[-1].change_reason}:{new_trades[-1].quantity/1000} 張"

            session.commit()
            session.close()
        return new_trades

    def _save_updates(self,new_trades: List[TradeRecord]):
        """
        將更新後的現股記錄和新增的交易記錄存回資料庫。
        """
        with dbPool.get_db_with() as session:
            # # 更新現股記錄
            # for record in records:
            #     session.merge(record)

            # 新增交易記錄
            session.add_all(new_trades)
            session.commit()


# --- 運行範例 ---
if __name__ == '__main__':
    # 這裡需要修改為您的資料庫連線字串


    # 初始化並運行交易系統
    system = TradingSystem()
    system.run_daily_process()