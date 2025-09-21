from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user: User):
    db_user = User(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, db_user: User, updates: User):
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, db_user: User):
    await db.delete(db_user)
    await db.commit()