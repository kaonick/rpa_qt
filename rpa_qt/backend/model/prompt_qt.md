
# prompt_qt.md

## 生成models

請幫我生成一個包含以下欄位的SQLAlchemy模型：
檔名與欄位，請用適當的英文命名，間隔以「_」區隔。請在模型的檔名與每個欄位的最後附上中文說明。
檔案名稱：交易記錄檔
欄位包括：
* id：主鍵，自動增量
* 單號：預設get_now_code()函數
* symbol：股票代號，不可空白。
* name：股票名稱，不可空白。
* 交易日期：yyyymmdd，不可空白。
* 異動原因：買進、賣出、股利、配股、庫存、轉讓、其他，不可空白。
* 張數：float,不可空白。
* 交易方式：限價、市價，不可空白。
* 狀態：委託成功、交易成功、刪除、成交、未成交，不可空白。
* 成交價格：float,不可空白。
* 金額：float,不可空白。
* 手續費：float,不可空白。
* 淨額：float,不可空白。
* 說明：string(200),可空白。
* 異動時間：預設get_now_code()函數，不可空白。

請幫我生成一個包含以下欄位的SQLAlchemy模型：
檔名與欄位，請用適當的英文命名，間隔以「_」區隔。請在模型的檔名與每個欄位的最後附上中文說明。
檔案名稱：現股記錄檔
欄位包括：
* id：主鍵，自動增量
* 單號：預設get_now_day()函數，yyyymmdd，不可空白。
* symbol：股票代號，不可空白。
* name：股票名稱，不可空白。
* 初始買進日：yyyymmdd，不可空白。
* 張數：float,不可空白。
* 成本均價：float,不可空白。
* 現價：float,不可空白。
* 買進後最高價：float,不可空白。
* 損益率：float,不可空白。
* 停損標準：float,不可空白。
* 停利標準：float,不可空白。
* 停損價格：float,不可空白。
* 停利價格：float,不可空白。
* 回跌率：float,不可空白。
* 目前狀態：停損階段或停利階段，,不可空白。
* 交易記錄：(用來看有經過那幾次有完成的交易記錄)，string(500),可空白。
* 應採策略：觀望、停利、停損、第一次加碼、第二次加碼、逾時賣出，可空白。
* 結算日期：yyyymmdd,可空白。
* 成本總額：float,不可空白。
* 損益金額：float,可空白。
* 損益率：float,可空白。
* 結算檢討：string(500),可空白。
* 異動時間：預設get_now_code()函數，不可空白。

## 生成交易系統

請幫我生成一個包含以下功能的Python交易系統：
1. 每日收盤後，自動從Fubon API中讀取以下資料：
   * 即時庫存資料，以及即時庫存中的每一支股票的當日K線資料(包含開盤價、最高價、最低價、收盤價、成交量)
   * 未實現損益資料。
   * 當日的委託且成交資料。
2. 再從資料庫中讀取現股記錄檔，並與API讀取的資料進行比對。(取即時庫存的股票代號，與當日成交的股票代號之聯集)
   * 若現股記錄檔中沒有該股票代號，則新增一筆現股記錄檔。
3. 然後針對每一筆現股記錄檔，先進行資料更新：
   * 來源為「即時庫存資料」：股票代號。
   * 來源為「未實現損益資料」：更新張數、初始買進日(第一次買進的日期)、成本均價、成本總額。
   * 來源為「當日K線資料」：更新現價=收盤價。
   * 來源為「當日成交資料」：更新買進或賣出手續費。
5. 進行以下計算：
   * 計算買進後最高價=現價與買進後最高價的最大值。
   * 計算損益率=(現價-成本均價)/成本均價*100%。
   * 計算停損價格=成本均價*(1-停損標準%)。
   * 計算停利起算價格=成本均價*(1+2*停損標準%)。
   * 計算停利價格=買進後最高價*(1-停利標準%)。
   * 計算回跌率=(買進後最高價-現價)/買進後最高價*100%。
6. 判斷目前所在的階段：
    * 若現價<=停利起算價格，則目前狀態為停損階段。
    * 若現價>=停利起算價格，則目前狀態為停利階段。
7. 依據以下條件，決定應採策略：
   * 若現價<=停損價格，策略為停損。
   * 若現價>=停利起算價格，且現價小時停利價格，策略為停利。
   * 若現價>=停利起算價格，且損益率大於10%，策略為第一次加碼。
   * 若現價>=停利起算價格，且損益率大於20%，策略為第二次加碼。
   * 若持有天數>=60天，策略為逾時賣出。
   * 否則策略為觀望。
8. 依第7點的策略：
   * 若是停損、停利、逾時賣出，則新增一筆賣單，並寫入交易記錄檔。
   * 若是加碼，則新增一筆買單，並寫入交易記錄檔。
8. 最後將更新後的現股記錄檔存回資料庫。

--- 以下是「現股記錄檔StockRecord」的類別定義：---
```python
class StockRecord(Base):
    __tablename__ = "stock_records"  # 現股記錄檔

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動增量

    order_code: Mapped[str] = mapped_column(String(8), nullable=False, default=get_now_day)  # 單號，預設 get_now_day()，yyyymmdd，不可空白

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)  # 股票代號，不可空白
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 股票名稱，不可空白

    init_buy_date: Mapped[str] = mapped_column(String(8), nullable=False)  # 初始買進日，yyyymmdd，不可空白
    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # 張數，float，不可空白
    avg_cost_price: Mapped[float] = mapped_column(Float, nullable=False)  # 成本均價，float，不可空白
    current_price: Mapped[float] = mapped_column(Float, nullable=False)  # 現價，float，不可空白
    highest_price: Mapped[float] = mapped_column(Float, nullable=False)  # 買進後最高價，float，不可空白
    
    buy_fee: Mapped[float] = mapped_column(Float, nullable=False)  # 買進手續費，float，不可空白
    sell_fee: Mapped[float] = mapped_column(Float, nullable=False)  # 賣出手續費，float，不可空白
    
    profit_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 損益率，float，不可空白
    stop_loss_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 停損標準，float，不可空白
    take_profit_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 停利標準，float，不可空白
    stop_loss_price: Mapped[float] = mapped_column(Float, nullable=False)  # 停損價格，float，不可空白
    take_profit_begin_price : Mapped[float] = mapped_column(Float, nullable=False)  # 停利起算價格，float，不可空白
    take_profit_price: Mapped[float] = mapped_column(Float, nullable=False)  # 停利價格，float，不可空白
    fallback_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 回跌率，float，不可空白

    current_status: Mapped[str] = mapped_column(
        Enum("stop_loss_stage", "take_profit_stage", name="status_enum"),
        nullable=False
    )  # 目前狀態：停損階段或停利階段，不可空白

    trade_history: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 交易記錄，可空白

    strategy: Mapped[str | None] = mapped_column(
        Enum("observe", "take_profit", "stop_loss", "first_add", "second_add", "timeout_sell", name="strategy_enum"),
        nullable=True
    )  # 應採策略：觀望、停利、停損、第一次加碼、第二次加碼、逾時賣出，可空白

    settlement_date: Mapped[str | None] = mapped_column(String(8), nullable=True)  # 結算日期，yyyymmdd，可空白
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)  # 成本總額，float，不可空白
    profit_amount: Mapped[float | None] = mapped_column(Float, nullable=True)  # 損益金額，float，可空白
    final_profit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 損益率，float，可空白
    review: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 結算檢討，string(500)，可空白

    data_time: Mapped[str] = mapped_column(String(20), nullable=False, default=get_now_code)  # 異動時間，預設 get_now_code()，不可空白
```
--- 以下是「交易記錄檔TradeRecord」的類別定義：---
```python
class TradeRecord(Base):
    __tablename__ = "trade_records"  # 交易記錄檔

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動增量

    order_code: Mapped[str] = mapped_column(String(20), nullable=False, default=get_now_code)  # 單號，預設 get_now_code()

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)  # 股票代號，不可空白
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 股票名稱，不可空白

    trade_date: Mapped[str] = mapped_column(String(8), nullable=False)  # 交易日期，yyyymmdd，不可空白

    change_reason: Mapped[str] = mapped_column(
        Enum("buy", "sell", "dividend", "allocation", "inventory", "transfer", "other", name="reason_enum"),
        nullable=False
    )  # 異動原因：買進、賣出、股利、配股、庫存、轉讓、其他

    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # 張數，float，不可空白

    trade_type: Mapped[str] = mapped_column(
        Enum("limit", "market", name="trade_type_enum"),
        nullable=False
    )  # 交易方式：限價、市價

    status: Mapped[str] = mapped_column(
        Enum("order_success", "trade_success", "deleted", "filled", "unfilled", name="status_enum"),
        nullable=True
    )  # 狀態：委託成功、交易成功、刪除、成交、未成交

    price: Mapped[float] = mapped_column(Float, nullable=False)  # 成交價格，float，不可空白
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 金額，float，不可空白
    fee: Mapped[float] = mapped_column(Float, nullable=False)  # 手續費，float，不可空白
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)  # 淨額，float，不可空白

    description: Mapped[str | None] = mapped_column(String(200), nullable=True)  # 說明，可空白

    data_time: Mapped[str] = mapped_column(String(20), nullable=False, default=get_now_code)  # 異動時間，預設 get_now_code()
```