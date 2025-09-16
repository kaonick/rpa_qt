import os

import fubon_neo
from dotenv import load_dotenv
# 匯入 SDK Library
from fubon_neo.sdk import FubonSDK, Order
from fubon_neo.constant import TimeInForce, OrderType, PriceType, MarketType, BSAction


def fubon_login():
    print(fubon_neo.__version__)
    load_dotenv()

    fubon_stock_account=os.getenv("FUBON_STOCK_ACCOUNT")
    fubon_stock_password=os.getenv("FUBON_STOCK_PASSWORD")
    fubon_stock_cert_path=os.getenv("FUBON_STOCK_CERT_PATH")
    fubon_stock_cert_password=os.getenv("FUBON_STOCK_CERT_PASSWORD")

    # 連結 API Server
    sdk = FubonSDK()

    accounts = sdk.login(fubon_stock_account, fubon_stock_password,fubon_stock_cert_path, fubon_stock_cert_password)   # 登入帳號 輸入:帳號、密碼、憑證路徑、憑證密碼
    print(accounts)
    return sdk