from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import TradeRecord, get_now_day
from rpa_qt.backend.config import adbPool


async def get_tradeRecord(db: AsyncSession, tradeRecord_id: int):
    result = await db.execute(select(TradeRecord).where(TradeRecord.id == tradeRecord_id))
    return result.scalar_one_or_none()

async def get_tradeRecords(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(TradeRecord).offset(skip).limit(limit))
    return result.scalars().all()

async def create_tradeRecord(db: AsyncSession, tradeRecord: TradeRecord):
    db_tradeRecord = tradeRecord
    db.add(db_tradeRecord)
    await db.commit()
    await db.refresh(db_tradeRecord)
    return db_tradeRecord

async def update_tradeRecord(db: AsyncSession, db_tradeRecord: TradeRecord, updates: TradeRecord):
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_tradeRecord, key, value)
    await db.commit()
    await db.refresh(db_tradeRecord)
    return db_tradeRecord

async def delete_tradeRecord(db: AsyncSession, db_tradeRecord: TradeRecord):
    await db.delete(db_tradeRecord)
    await db.commit()

async def tmp_test_curd():

    async with adbPool.get_async_db_with() as session:
        aTradeRecord=TradeRecord()
        aTradeRecord.symbol="0050.TW"
        aTradeRecord.name="元大台灣50"
        aTradeRecord.trade_date=get_now_day()
        aTradeRecord.change_reason="buy"
        aTradeRecord.trade_type="market"
        aTradeRecord.status="order_success"
        aTradeRecord.price=60.5
        aTradeRecord.quantity=10
        aTradeRecord.amount=6050
        aTradeRecord.fee=15
        aTradeRecord.net_amount=6065
        aTradeRecord.description="this is a test record"
        new_tradeRecord=await create_tradeRecord(session,aTradeRecord)
        print(new_tradeRecord)

if __name__ == '__main__':
    import asyncio
    asyncio.run(tmp_test_curd())