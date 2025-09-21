# 停用，改用db_pool
# from contextlib import contextmanager, asynccontextmanager
#
# from sqlalchemy import create_engine, text
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from .config import settings
#
# connector = settings.database_connector #"mysql+mysqlconnector"
# SYNC_DATABASE_URL = f"{connector}://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
# aconnector = settings.database_aconnector #"mysql+aiomysql"
# ASYNC_DATABASE_URL = (
#     f"{aconnector}://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"
# )
#
# run_async_db:bool=True
# run_db:bool=True
# if run_async_db:
#     # ---------- Engine & Pool tuning ----------
#     # 池參數（視需求調整）
#     # pool_size：常駐連線數（對高併發建議值視 MySQL 與 app 併發而定）
#     # max_overflow：允許超出 pool_size 的暫時連線數
#     # pool_recycle：秒數；避免 MySQL 連線被 server 關閉
#     engine = create_async_engine(
#         ASYNC_DATABASE_URL,
#         echo=False,
#         pool_size=30,  # 調整成你需要的常駐連線數
#         max_overflow=100,  # 允許短暫 burst
#         pool_timeout=30,
#         pool_recycle=1800,  # 30 分鐘
#         future=True,
#     )
#
#     # Async sessionmaker
#     AsyncSessionLocal = sessionmaker(bind=engine,
#                                      class_=AsyncSession,
#                                      expire_on_commit=False,
#                                      )
# if run_db:
#     engine = create_engine(SYNC_DATABASE_URL)
#     SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#
#
#
#
# Base = declarative_base()
#
# # for fastapi depend用：一般使用時，要用for db in get_db():才行(不建議)
# def get_depend_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
# # 一般用
# def get_db():
#     db = SessionLocal()
#     return db
#
# # with用
# @contextmanager
# def get_db_with():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
# # for fastapi depend用：一般使用時，要用async for db in get_async_db():才行(不建議)
# async def get_depend_async_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         yield session
#
# # 一般用
# async def get_async_db():
#     async with AsyncSessionLocal() as session:
#         return session
#
# @asynccontextmanager
# async def get_async_db_with():
#     async with AsyncSessionLocal() as session:
#         yield session
#
# async def tmp_async_db():
#     try:
#         # depend用
#         async for db in get_depend_async_db():
#             await db.execute(text("SELECT 1 FROM dual"))
#
#         # 一般用(注意這種要自已關閉才行)
#         db=await get_async_db()
#         await db.execute(text("SELECT 1 FROM dual"))
#         await db.close()
#
#         # with用
#         async with get_async_db_with() as session:
#             await session.execute(text("SELECT 1 FROM dual"))  # 簡單的查詢來檢查連線
#         print("Database Check Pass...")
#     except Exception as e:
#         print("\n⚠️ Database Check ERROR...")
#         print(f"e={e}")
#     finally:
#         pass
#
# def tmp_db():
#     try:
#         # depend用
#         for db in get_depend_db():
#             db.execute(text("SELECT 1 FROM dual"))
#
#         # 一般用(注意這種要自已關閉才行)
#         db=get_db()
#         db.execute(text("SELECT 1 FROM dual"))
#         db.close()
#
#         # with用
#         with get_db_with() as session:
#             session.execute(text("SELECT 1 FROM dual"))  # 簡單的查詢來檢查連線
#         print("Database Check Pass...")
#     except Exception as e:
#         print("\n⚠️ Database Check ERROR...")
#         print(f"e={e}")
#     finally:
#         pass

