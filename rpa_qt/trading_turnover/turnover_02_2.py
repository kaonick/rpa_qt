"""

"""
import json
import threading
import pandas as pd
from datetime import datetime

from dash import Dash, dcc, html, Output, Input
import plotly.graph_objs as go
import websocket

# === 全域 DataFrame 存放 K 線 ===
df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

# Binance WebSocket URL (SOL/USDT 1秒K線)
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/solusdt@kline_1s"

# === WebSocket 處理函式 ===
def on_message(ws, message):
    global df
    data = json.loads(message)
    k = data["k"]  # kline 資料
    ts = datetime.fromtimestamp(k["t"] / 1000.0)  # 開盤時間 (毫秒轉秒)

    new_row = pd.DataFrame({
        "open":   [float(k["o"])],
        "high":   [float(k["h"])],
        "low":    [float(k["l"])],
        "close":  [float(k["c"])],
        "volume": [float(k["v"])],
    }, index=[ts])

    # 更新 DataFrame（以時間戳為索引，避免重複）
    df = pd.concat([df[~df.index.isin(new_row.index)], new_row]).sort_index()

def on_error(ws, error):
    print("WebSocket 錯誤:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket 關閉")

def run_ws():
    ws = websocket.WebSocketApp(
        BINANCE_WS_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()

# 啟動 WebSocket 在背景 thread
t = threading.Thread(target=run_ws, daemon=True)
t.start()

# === Dash App ===
app = Dash(__name__, title="SOL/USDT 1秒 K 線")

app.layout = html.Div([
    html.H2("SOL/USDT 即時 K 線 (Binance 1秒)", style={"margin":"8px"}),
    dcc.Graph(id="k-chart", style={"height":"75vh"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0),  # 每秒更新
])

def compute_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    # EMA
    out["ema20"]  = out["close"].ewm(span=20,  adjust=False).mean()
    out["ema60"]  = out["close"].ewm(span=60,  adjust=False).mean()
    out["ema120"] = out["close"].ewm(span=120, adjust=False).mean()
    # SMA
    out["sma20"]  = out["close"].rolling(20,  min_periods=1).mean()
    out["sma60"]  = out["close"].rolling(60,  min_periods=1).mean()
    out["sma120"] = out["close"].rolling(120, min_periods=1).mean()
    return out

@app.callback(
    Output("k-chart", "figure"),
    Input("interval", "n_intervals"),
)
def update_chart(n):
    global df
    if df.empty:
        return go.Figure()

    # 只顯示最近 500 根，避免圖表太大
    display_df = df.iloc[-500:]
    ind = compute_indicators(display_df)

    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=ind.index, open=ind["open"], high=ind["high"],
        low=ind["low"], close=ind["close"],
        name="K 線"
    ))

    # EMA 線
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema20"],  mode="lines", name="EMA20"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema60"],  mode="lines", name="EMA60"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema120"], mode="lines", name="EMA120"))

    # SMA 線
    # fig.add_trace(go.Scatter(x=ind.index, y=ind["sma20"],  mode="lines", name="SMA20"))
    # fig.add_trace(go.Scatter(x=ind.index, y=ind["sma60"],  mode="lines", name="SMA60"))
    # fig.add_trace(go.Scatter(x=ind.index, y=ind["sma120"], mode="lines", name="SMA120"))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )

    return fig

if __name__ == "__main__":
    app.run(debug=False)

