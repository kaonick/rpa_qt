"""
這是一個針對現有庫存進行「停損、停利、或是第一次加碼、第二次加碼」的策略程式。
步驟說明:
1. 建立連線
2. 取得庫存
3. 取得未實現損益
4. 讀取當日收盤資訊。
5. 從資料庫，讀取StockRecords資料，然後依庫存、未實現損益、當日收盤資訊，計算各項數據。
6. 依計算結果，制定策略：停損或停利、或加碼...。
7. 發出隔日交易指令。

"""

import threading
import time
import logging
from datetime import datetime, timedelta

from sqlalchemy import text

from rpa_qt.backend.config import dbPool
from rpa_qt.backend.model.models import StockRecord
from rpa_qt.fubon.fubon_auth import fubon_login
from rpa_qt.fubon.fubon_webapi import get_inventory, get_unrealized_gains_and_loses, sdk_init, get_reststock, \
    get_last_day_candle
from rpa_qt.fubon.inventory_stop_loss_v2.auto_map import auto_map


class StrategyStopLoss:
    def __init__(self, sdk, db_manager, logger=None):
        self.sdk = sdk
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.thread = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            self.logger.info("StrategyStopLoss started.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            self.logger.info("StrategyStopLoss stopped.")

    def run(self):
        while self.is_running:
            try:
                self.execute_strategy()
            except Exception as e:
                self.logger.error(f"Error executing strategy: {e}")
            time.sleep(60)  # Run every minute

def execute_strategy():
    # Step 1: Establish connection
    sdk,active_account=fubon_login()
    if not active_account:
        raise "No active account. Please log in."

    # Step 2: Get inventory
    inv_list = get_inventory(sdk, active_account)

    # Step 3: Get unrealized profit/loss
    unrealized_list = get_unrealized_gains_and_loses(sdk, active_account)

    # Step 4: Get daily closing information
    sdk_init(sdk)
    reststock=get_reststock(sdk)

    for i,inv in enumerate(inv_list):
        print(inv)  # InventoryData

        print(unrealized_list[i])  # UnrealizedData
        unrealized=unrealized_list[i]

        symbol=inv.stock_no
        closing_info = get_last_day_candle(reststock, symbol)  # Example for a specific stock

        # Step 5: Read StockRecords from database and calculate metrics
        with dbPool.get_db_with() as session:
            # fetch StockRecords
            stock_record=session.execute(text("SELECT * FROM stock_records where symbol=:symbol"),{"symbol":symbol}).first()
            print(stock_record)
            if stock_record is None:
                stock_record=auto_map(target_obj=StockRecord(), obj1=inv,obj2=unrealized)
                print(stock_record)


if __name__ == '__main__':
    execute_strategy()


