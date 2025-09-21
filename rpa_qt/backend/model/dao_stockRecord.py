from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import StockRecord


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

