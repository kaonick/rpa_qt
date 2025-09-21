import asyncio

from rpa_qt.backend.config import adbPool
from rpa_qt.backend.model import models


async def init_db():
    # 這個函數用來初始化資料庫，建立所有定義的表格
    async with adbPool.get_engine().begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

if __name__ == '__main__':
    asyncio.run(init_db())