import logging
import cx_Oracle
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from contextlib import contextmanager, asynccontextmanager

from .config import settings


connector = settings.database_connector #"mysql+mysqlconnector"
SYNC_DATABASE_URL = f"{connector}://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
aconnector = settings.database_aconnector #"mysql+aiomysql"
ASYNC_DATABASE_URL = (
    f"{aconnector}://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
)


# create a DbPool Class that for client to get_conn for session
"""
oracle目前無支援非同步io。
"""
class DataPool:
    def __init__(self):

        self.db_url = SYNC_DATABASE_URL
        try:
            if self.db_url.startswith('oracle'):
                lib_dir = r"D:/dev_env/instantclient_21_13"
                try:
                    cx_Oracle.init_oracle_client(lib_dir=lib_dir)
                except Exception as err:
                    print("Error connecting: cx_Oracle.init_oracle_client()")
                    print(err);
                    # sys.exit(1);

            self.engine = create_engine(self.db_url,
                                        pool_pre_ping=True)  # 自動在每次借出連線前執行 SELECT 1，確保連線有效

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        except Exception as e:
            logging.error(f"create_engine error: {e}")
            raise e

    def get_engine(self):
        return self.engine



    # for fastapi depend用：一般使用時，要用for db in get_db():才行(不建議)
    def get_depend_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # 一般用(with)
    @contextmanager
    def get_db_with(self):
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    # 一般用(非with)
    def get_db(self):
        db = self.SessionLocal()
        return db





class AsyncDataPool:
    def __init__(self):
        self.db_url = ASYNC_DATABASE_URL
        try:
            if self.db_url.startswith('oracle'):
                lib_dir = r"D:/dev_env/instantclient_21_13"
                try:
                    cx_Oracle.init_oracle_client(lib_dir=lib_dir)
                except Exception as err:
                    print("Error connecting: cx_Oracle.init_oracle_client()")
                    print(err);
                    # sys.exit(1);

            # ---------- Engine & Pool tuning ----------
            # 池參數（視需求調整）
            # pool_size：常駐連線數（對高併發建議值視 MySQL 與 app 併發而定）
            # max_overflow：允許超出 pool_size 的暫時連線數
            # pool_recycle：秒數；避免 MySQL 連線被 server 關閉
            self.engine = create_async_engine(
                ASYNC_DATABASE_URL,
                echo=False,
                pool_size=30,  # 調整成你需要的常駐連線數
                max_overflow=100,  # 允許短暫 burst
                pool_timeout=30,
                pool_recycle=1800,  # 30 分鐘
                future=True,
            )

            # Async sessionmaker
            self.AsyncSessionLocal = sessionmaker(bind=self.engine,
                                             class_=AsyncSession,
                                             expire_on_commit=False,
                                             )


        except Exception as e:
            logging.error(f"create_engine error: {e}")
            raise e

    def get_engine(self):
        return self.engine

    # for fastapi depend用：一般使用時，要用async for db in get_async_db():才行(不建議)
    async def get_depend_async_db(self):
        async with self.AsyncSessionLocal() as session:
            yield session

    # 一般用(with，不用close)
    @asynccontextmanager
    async def get_async_db_with(self):
        async with self.AsyncSessionLocal() as session:
            yield session

    # 一般用(非with，需要自已close)
    async def get_async_db(self):
        async with self.AsyncSessionLocal() as session:
            return session


# Base = declarative_base()

dbPool = DataPool()
adbPool = AsyncDataPool()

async def tmp_async_db():
    try:
        # depend用
        async for db in adbPool.get_depend_async_db():
            await db.execute(text("SELECT 1 FROM dual"))

        # 一般用(注意這種要自已關閉才行)
        db=await adbPool.get_async_db()
        await db.execute(text("SELECT 1 FROM dual"))
        await db.close()

        # with用
        async with adbPool.get_async_db_with() as session:
            await session.execute(text("SELECT 1 FROM dual"))  # 簡單的查詢來檢查連線
        print("Database Check Pass...")
    except Exception as e:
        print("\n⚠️ Database Check ERROR...")
        print(f"e={e}")
    finally:
        pass

def tmp_db():
    try:
        # depend用
        for db in dbPool.get_depend_db():
            db.execute(text("SELECT 1 FROM dual"))

        # 一般用(注意這種要自已關閉才行)
        db=dbPool.get_db()
        db.execute(text("SELECT 1 FROM dual"))
        db.close()

        # with用
        with dbPool.get_db_with() as session:
            session.execute(text("SELECT 1 FROM dual"))  # 簡單的查詢來檢查連線
        print("Database Check Pass...")
    except Exception as e:
        print("\n⚠️ Database Check ERROR...")
        print(f"e={e}")
    finally:
        pass