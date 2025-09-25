import asyncio
from datetime import datetime

from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, UniqueConstraint

from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP, Boolean, Text, DateTime, Float, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Base = declarative_base()


# trade_records.py  # 交易記錄檔







# 單號與異動時間產生函數
def get_now_code() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f%z")

def get_now_day() -> str:
    return datetime.now().strftime("%Y%m%d")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    date_created = Column(TIMESTAMP(timezone=True),
                          nullable=False, server_default=text('now()'))
    date_modified = Column(TIMESTAMP(timezone=True), nullable=False,
                           server_default=text('now()'), onupdate=text('now()'))

    acquisition_channel = Column(String(100), nullable=True, default="SYSTEM") # 客戶來源管道 GOOGLE, FACEBOOK, APPLE,etc.
    verified = Column(Boolean,nullable=False,default=False)# email驗證完成=True, 未驗證=False
    verification_code = Column(String(10), nullable=True) # 雙因子驗證：驗證碼

    name = Column(String(100), nullable=True)
    avatar = Column(String(100), nullable=True)
    biography = Column(String(200), nullable=True)
    position = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    status = Column(String(15), nullable=True, default="ACTIVE") # NULL, ACTIVE, PASSIVE

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


class StockRecord(Base):
    __tablename__ = "stock_records"  # 現股記錄檔

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # 主鍵，自動增量

    order_code: Mapped[str] = mapped_column(String(20), nullable=False, default=get_now_day)  # 單號，預設 get_now_day()，yyyymmdd，不可空白

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)  # 股票代號，不可空白
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # 股票名稱，不可空白

    init_buy_date: Mapped[str] = mapped_column(String(20), nullable=False)  # 初始買進日，yyyymmdd，不可空白
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

    settlement_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 結算日期，yyyymmdd，可空白
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)  # 成本總額，float，不可空白
    profit_amount: Mapped[float | None] = mapped_column(Float, nullable=True)  # 損益金額，float，可空白
    final_profit_rate: Mapped[float | None] = mapped_column(Float, nullable=True)  # 損益率，float，可空白
    review: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 結算檢討，string(500)，可空白

    data_time: Mapped[str] = mapped_column(String(20), nullable=False, default=get_now_code)  # 異動時間，預設 get_now_code()，不可空白



