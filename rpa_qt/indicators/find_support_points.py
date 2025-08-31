"""
用來找近期 n 根 K 線的支撐點，條件結合以下三個判斷：
成交量增加（確認買盤）
靠近均線（例如 EMA20）
接近費波水準（Fibonacci 回調 0.382~0.618）
程式會返回符合條件的支撐點列表。

"""

import pandas as pd
import numpy as np

# 假設 df 有 'open','high','low','close','volume'
# df.index 為日期，倒序排列最近在最後

def find_support_points(df, n=20, ema_period=20, fib_levels=[0.382, 0.5, 0.618]):
    """
    找近期支撐點
    df: OHLCV DataFrame
    n: 取最近 n 根 K 線
    ema_period: 均線週期
    fib_levels: 費波水準比例
    """
    df_recent = df[-n:].copy()

    # 1️⃣ 計算均線
    df_recent['EMA'] = df_recent['close'].ewm(span=ema_period, adjust=False).mean()

    # 2️⃣ 計算近期高低做費波水準
    high = df_recent['high'].max()
    low = df_recent['low'].min()
    fib_supports = [high - (high-low)*level for level in fib_levels]

    # 3️⃣ 找局部低點
    df_recent['prev_low'] = df_recent['low'].shift(1)
    df_recent['next_low'] = df_recent['low'].shift(-1)
    df_recent['local_low'] = (df_recent['low'] < df_recent['prev_low']) & (df_recent['low'] < df_recent['next_low'])

    # 4️⃣ 成交量判斷 (比前一根增加)
    df_recent['vol_up'] = df_recent['volume'] > df_recent['volume'].shift(1)

    # 5️⃣ 均線靠近判斷 (低於均線 + 誤差範圍)
    tol = 0.01  # 1% 誤差範圍
    df_recent['near_ema'] = abs(df_recent['low'] - df_recent['EMA'])/df_recent['EMA'] <= tol

    # 6️⃣ 費波水準靠近判斷
    tol_fib = 0.01  # 1% 誤差
    df_recent['near_fib'] = df_recent['low'].apply(lambda x: any(abs(x - f)/f <= tol_fib for f in fib_supports))

    # 7️⃣ 全部條件同時滿足
    df_recent['support'] = df_recent['local_low'] & df_recent['vol_up'] & df_recent['near_ema'] & df_recent['near_fib']

    # 取出支撐點
    support_points = df_recent[df_recent['support']]

    return support_points[['low','EMA','volume']]

# -----------------------------
# 使用範例
# df = pd.read_csv('your_ohlcv.csv', parse_dates=['date'], index_col='date')
# support_points = find_support_points(df, n=50)
# print(support_points)
