import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI,Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# middlewares
from backend.middleware.exception_handler import add_global_exception_handler
from backend.middleware.logging import LoggingMiddleware
from backend.middleware.auth import AuthMiddleware

from backend.model import models
# from evoucher.config import engine
from backend.routers import user, auth, secure_router, product_router

from backend.config import settings, adbPool
from pathlib import Path
from api_analytics.fastapi import Analytics
# models.Base.metadata.create_all(bind=engine)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # create DB tables if not exist (for demo). In prod use migrations (alembic).
#     async with engine.begin() as conn:
#         await conn.run_sync(models.Base.metadata.create_all)


app = FastAPI()
key="c91d6234-6927-4035-a25b-066a6965e7f0" #https://www.apianalytics.dev/generate
app.add_middleware(Analytics, api_key=key)

# 請求日誌
app.add_middleware(LoggingMiddleware)

# 驗證 token
# app.add_middleware(AuthMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret"), algorithms=["HS256"])


origins = ["*"] # 部署時請改為你的前端網址
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ---------- Lifespan: create tables on startup (for demo) ----------
# @app.on_event("startup")
# async def on_startup():
#     # create DB tables if not exist (for demo). In prod use migrations (alembic).
#     async with adbPool.get_engine().begin() as conn:
#         await conn.run_sync(models.Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB tables if not exist (for demo). In prod use migrations (alembic).
    async with adbPool.get_engine().begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


# 全域例外處理
add_global_exception_handler(app)

@app.get("/client-info")
async def get_client_info(request: Request):
    client_host = request.client.host
    client_port = request.client.port
    user_agent = request.headers.get("User-Agent")
    # You can access other headers similarly, e.g., request.headers.get("Accept-Language")

    return {
        "client_host": client_host,
        "client_port": client_port,
        "user_agent": user_agent,
        # Add more client info as needed
    }


app.include_router(user.router)
app.include_router(auth.router)
app.include_router(secure_router.router)
app.include_router(product_router.router)
# app.include_router(card.router)
# app.include_router(transaction.router)
# app.include_router(endporint_api.router)
# app.include_router(monitor.router)

# statci files
main_path = Path(__file__).parent  # main.py所在目錄
static_files_dir = main_path / "backend/frontend"
app.mount(
    "/",
    StaticFiles(directory=static_files_dir, html=True),
    name="static",
)

# @app.get("/client-info")
# async def get_client_info(request: Request):
#     client_host = request.client.host
#     client_port = request.client.port
#     user_agent = request.headers.get("User-Agent")
#     # You can access other headers similarly, e.g., request.headers.get("Accept-Language")
#
#     return {
#         "client_host": client_host,
#         "client_port": client_port,
#         "user_agent": user_agent,
#         # Add more client info as needed
#     }

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000) # for debug
