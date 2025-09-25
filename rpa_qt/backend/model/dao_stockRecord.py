from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import StockRecord, get_now_code


async def get_stockRecord(db: AsyncSession, stockRecord_id: int):
    result = await db.execute(select(StockRecord).where(StockRecord.id == stockRecord_id))
    return result.scalar_one_or_none()

async def get_stockRecords(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(StockRecord).offset(skip).limit(limit))
    return result.scalars().all()

async def create_stockRecord(db: AsyncSession, stockRecord: StockRecord):
    db_stockRecord = StockRecord(**stockRecord.dict())
    db.add(db_stockRecord)
    await db.commit()
    await db.refresh(db_stockRecord)
    return db_stockRecord

async def update_stockRecord(db: AsyncSession, db_stockRecord: StockRecord, updates: StockRecord):
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_stockRecord, key, value)
    await db.commit()
    await db.refresh(db_stockRecord)
    return db_stockRecord

async def delete_stockRecord(db: AsyncSession, db_stockRecord: StockRecord):
    await db.delete(db_stockRecord)
    await db.commit()


async def init_stockRecords(unrealized):
    vo = StockRecord()

    vo.order_code=get_now_code()
    vo.symbol=unrealized.stock_no
    vo.name=
    vo.quantity=unrealized.today_qty
    vo.init_buy_date=unrealized.date
    vo.avg_cost_price=unrealized.cost_price
    vo.current_price=
    vo.highest_price=
    vo.profit_rate=
    vo.stop_loss_rate=0.05  # 停損標準，float，不可空白
    vo.take_profit_rate=0.03  # 停利標準，float，不可空白
    vo.stop_loss_price=  # 停損價格，float，不可空白
    vo.take_profit_begin_price =  # 停利起算價格，float，不可空白
    vo.take_profit_price=  # 停利價格，float，不可空白
    vo.fallback_rate=  # 回跌率，float，不可空白

    # if current_price is higher than take_profit_begin_price, then set current_status="take_profit_stage" otherwise "stop_loss_stage"
    vo.current_status=("take_profit_stage" if vo.current_price > vo.take_profit_begin_price else "stop_loss_stage") # 目前狀態：停損階段或停利階段，不可空白
    vo.trade_history="" # 交易記錄，可空白

    # if current_price is lower than stop_loss_price then set strategy="stop_loss"
    # if current_price is higher than take_profit_begin_price and lower than  take_profit_price then set strategy="take_profit"
    # if profit_rate is higher than 10% then set strategy="first_add"
    # if profit_rate is higher than 20% then set strategy="second_add"
    # if holding days is more than 60 days(from init_buy_date till now) and current_price lower than take_profit_begin_price then set strategy="timeout_sell"
    # otherwise "observe"
    vo.strategy = (
        "stop_loss" if vo.current_price < vo.stop_loss_price else
        "take_profit" if vo.current_price > vo.take_profit_begin_price and vo.current_price < vo.take_profit_price else
        "second_add" if vo.profit_rate > 0.2 else
        "first_add" if vo.profit_rate > 0.1 else
        "timeout_sell" if (int(get_now_day()) - int(vo.init_buy_date)) > 60 and vo.current_price < vo.take_profit_begin_price else
        "observe"
    )
    # 應採策略：觀望、停利、停損、第一次加碼、第二次加碼、逾時賣出，可空白

    vo.settlement_date=  # 結算日期，yyyymmdd，可空白
    vo.total_cost=  # 成本總額，float，不可空白
    vo.profit_amount=  # 損益金額，float，可空白
    vo.final_profit_rate=  # 損益率，float，可空白
    vo.review= # 結算檢討，string(500)，可空白

    vo.data_time=get_now_code()  # 異動時間，預設 get_now_code()，不可空白
    await db.commit()