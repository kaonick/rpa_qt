"""
請幫我找近三個月日K的最後三個峰值跟低值
三個月日 K 線的最後三個高點 (peak) 與低點 (trough)，可以使用 pandas + scipy.signal.find_peaks 來實作。

"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import datetime
import mplfinance as mpf
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# === 參數設定 ===
ticker = "2330.TW"   # 台積電
today = datetime.date.today()
start_date = today - datetime.timedelta(days=90)  # 近三個月

# === 抓資料 ===
df = yf.download(ticker, start=start_date, end=today, interval="1d")
df = df[['Open','High','Low','Close','Volume']].dropna()
df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# === 找局部峰值 ===
array_High = df['High'].values.flatten() #.to_numpy()
array_Low = df['Low'].values.flatten()# .to_numpy()
peaks, _ = find_peaks(array_High, distance=3)
troughs, _ = find_peaks(-array_Low, distance=3)

# 取最後三個高點 & 低點
last3_peaks = df.iloc[peaks].tail(3)
last3_troughs = df.iloc[troughs].tail(3)

print("📈 最近三個高點：")
print(last3_peaks[['High']])
print("\n📉 最近三個低點：")
print(last3_troughs[['Low']])

# === 畫K線圖 ===

# 取df最近45天
df = df.tail(45)

fig, ax = mpf.plot(
    df,
    type="candle",
    volume=True,
    style="yahoo",
    returnfig=True,
    figsize=(12,6)
)

# === 畫高低點 ===

x_points = [df.index.get_loc(i) for i in last3_peaks.index]  # 取得日期索引位置
ax[0].plot(x_points, last3_peaks['High'], 'ro')

x_points = [df.index.get_loc(i) for i in last3_troughs.index]  # 取得日期索引位置
ax[0].plot(x_points, last3_troughs['Low'], 'go')

# # === 定義函式：畫延伸趨勢線 ===
def draw_trendline(ax, points, color, label):
    # x 轉為數字 (日期索引 -> 0,1,2,...)
    x = np.arange(len(df))
    x_points = [df.index.get_loc(i) for i in points.index]  # 取得日期索引位置
    y_points = points.values
    ax.plot(x_points, y_points, color=color, linestyle="--", label=label)
    # 線性回歸
    # model = LinearRegression()
    # model.fit(np.array(x_points).reshape(-1,1), y_points)
    #
    # # 預測全範圍 (延伸到最後一天)
    # y_pred = model.predict(x.reshape(-1,1))
    #
    # ax.plot(df.index, y_pred, color=color, linestyle="--", label=label)

# # === 畫高點趨勢線 ===
draw_trendline(ax[0], last3_peaks['High'], 'red', "Peaks Trendline")
#
# # === 畫低點趨勢線 ===
draw_trendline(ax[0], last3_troughs['Low'], 'green', "Troughs Trendline")

ax[0].legend()
plt.show()
plt.savefig(f"trend.png")
plt.close()
