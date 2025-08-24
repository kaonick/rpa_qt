"""
ChatGPT生成：


以下的程式碼是用python Dash框架動態顯示Binance交易所的SOL/USDT 1秒K線圖。
請進行改進，完成以下功能：
1. 幣種改為可設定的參數，預設為SOL/USDT。(未達成)
2. 畫面上方顯示目前的幣種名稱。
3. 畫面上方顯示目前的即時價格。
4. 可選擇k線的時間間隔，預設為1秒，選項有1秒、5秒、15秒、30秒、1分鐘、5分鐘、15分鐘、30分鐘、1小時、4小時、1天。
5. 畫面上方顯示目前的時間間隔。
6. 畫面上方顯示目前的時間。
7. 除了K線圖與SMA、EMA指標外，還要顯示成交量的柱狀圖。
8. 可以同時顯示兩種時間間隔的K線圖，例如1秒與5秒，或1分鐘與5分鐘。(分成兩個圖表顯示，上下排列)

--目前的程式碼如下所示--

# 待辦事項：
1. [x] 可以預設往前抓取一些歷史K線資料，避免一開始畫面空白。
2. 因為可以設定兩個K線時間間隔，應該要有兩個WebSocket連線，分別抓取不同時間間隔的K線資料。(目前是只抓取一個時間間隔)
3. 幣種應該要改成可以選擇不同幣種，而不是寫死在程式碼中。(目前是寫死在程式碼中)
4. 自動計算交易訊號，並在圖上標記買賣點。(目前沒有這個功能)
5. 可以有回測功能，模擬歷史資料進行策略測試。(目前沒有這個功能)
6. 可以有交易功能，連接交易所API進行自動下單，可以設定每次交易的數量(預設=2)、槓桿倍數(預設=3)。(目前沒有這個功能)
7. 可以記錄每一筆交易記錄，並計算績效，以表格記錄，並以圖表顯示績效。(目前沒有這個功能)
8. 可以設定投入資金(預設=300USDT)。(目前沒有這個功能)

"""

import json
import threading
import pandas as pd
from datetime import datetime

from ccxt.static_dependencies.ethereum.utils.humanize import DISPLAY_HASH_CHARS
from dash import Dash, dcc, html, Output, Input, State
import plotly.graph_objs as go
import websocket

from rpa_qt.price_utils.coin_price_ws import KlineWebSocket

# =======================
# 全域設定
# =======================
DEFAULT_SYMBOL = "SOLUSDT"
DEFAULT_INTERVAL = "1s"
DEFAULT_INTERVAL_2 = "5m"


# INTERVAL_OPTIONS = ["1s","5s","15s","30s","1m","5m","15m","30m","1h","4h","1d"]
INTERVAL_OPTIONS = ["1s","1m","5m","15m","30m","1h","4h","1d"]
# 儲存不同時間間隔的 K 線資料
dfs = {}

# 即時價格
latest_price = None

# =======================
# WebSocket 函式
# =======================
# def create_ws(symbol, interval):
#     url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
#
#     def on_message(ws, message):
#         global dfs, latest_price
#         data = json.loads(message)
#         k = data["k"]
#         ts = datetime.fromtimestamp(k["t"] / 1000.0)
#         new_row = pd.DataFrame({
#             "open": [float(k["o"])],
#             "high": [float(k["h"])],
#             "low": [float(k["l"])],
#             "close": [float(k["c"])],
#             "volume": [float(k["v"])],
#         }, index=[ts])
#         latest_price = float(k["c"])
#
#         if interval not in dfs:
#             dfs[interval] = pd.DataFrame(columns=["open","high","low","close","volume"])
#             dfs["5m"] = pd.DataFrame(columns=["open","high","low","close","volume"])
#         dfs[interval] = pd.concat([dfs[interval][~dfs[interval].index.isin(new_row.index)], new_row]).sort_index()
#         dfs["5m"] = pd.concat([dfs["5m"][~dfs["5m"].index.isin(new_row.index)], new_row]).sort_index()
#
#     def on_error(ws, error):
#         print(f"WebSocket {symbol} {interval} 錯誤:", error)
#
#     def on_close(ws, close_status_code, close_msg):
#         print(f"WebSocket {symbol} {interval} 關閉")
#
#     ws = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
#     ws.run_forever()
#
# # =======================
# # 啟動 WebSocket 執行緒
# # =======================
# ws_thread = threading.Thread(target=create_ws, args=(DEFAULT_SYMBOL, DEFAULT_INTERVAL), daemon=True)
# ws_thread.start()

kws = KlineWebSocket(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL,dfs=dfs)
kws.start()

kws2 = KlineWebSocket(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL_2,dfs=dfs)
kws2.start()


# =======================
# 計算指標
# =======================
def compute_indicators(df):
    df = df.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema60"] = df["close"].ewm(span=60, adjust=False).mean()
    df["ema120"] = df["close"].ewm(span=120, adjust=False).mean()
    df["sma20"] = df["close"].rolling(20, min_periods=1).mean()
    df["sma60"] = df["close"].rolling(60, min_periods=1).mean()
    df["sma120"] = df["close"].rolling(120, min_periods=1).mean()
    return df

# =======================
# Dash App
# =======================
app = Dash(__name__, title="即時 K 線圖")

# =======================
# Dash App Layout
# =======================
app.layout = html.Div([
    html.Div([

        html.Div([
            html.Span("即時價格: ", style={"margin-right":"5px"}),
            html.Span(id="price-display")
        ], style={"margin":"5px"}),
        # html.H2(id="symbol-title", style={"margin": "5px"}),
        # html.Div([
        #     html.Span("目前時間: ", style={"margin-right":"5px"}),
        #     html.Span(id="time-display")
        # ], style={"margin":"5px"}),
        html.Div([
            html.Label("選擇時間間隔1:"),
            dcc.Dropdown(
                id="interval1-dropdown",
                options=[{"label": x, "value": x} for x in INTERVAL_OPTIONS],
                value=DEFAULT_INTERVAL,
                clearable=False
            ),
            html.Label("選擇時間間隔2 (可選):"),
            dcc.Dropdown(
                id="interval2-dropdown",
                options=[{"label": x, "value": x} for x in INTERVAL_OPTIONS],
                value=DEFAULT_INTERVAL_2,
                clearable=True
            ),
        ], style={"width":"400px", "margin":"5px"})
    ]),
    html.Div([
        html.Label("k1顯示根數:"),
        dcc.Slider(
            id="k1-limit-slider",
            min=25,
            max=500,
            step=None,  # 限制只能選 marks
            value=100,  # 初始值
            marks={
                25: "25",
                50: "50",
                75: "75",
                100: "100",
                200: "200",
                300: "300",
                400: "400",
                500: "500"
            }
        )
    ], style={"margin": "20px"}),
    html.Div([
        html.Label("k2顯示根數:"),
        dcc.Slider(
            id="k2-limit-slider",
            min=25,
            max=500,
            step=None,  # 限制只能選 marks
            value=100,  # 初始值
            marks={
                25: "25",
                50: "50",
                75: "75",
                100: "100",
                200: "200",
                300: "300",
                400: "400",
                500: "500"
            }
        )
    ], style={"margin": "20px"}),

    html.Div([
        html.H2(id="symbol-title", style={"margin": "5px"}),

        html.Div([
            html.Span("目前時間: ", style={"margin-right":"5px"}),
            html.Span(id="time-display")
        ], style={"margin":"5px"})
    ], style={"display": "flex", "alignItems": "center"}),

    # 上下兩個圖表
    dcc.Graph(id="k-chart1", style={"height":"45vh"}),
    dcc.Graph(id="k-chart2", style={"height":"45vh"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])


# =======================
# 更新圖表 Callback
# =======================
@app.callback(
    Output("k-chart1", "figure"),
    Output("k-chart2", "figure"),
    Output("symbol-title", "children"),
    Output("price-display", "children"),
    Output("time-display", "children"),
    Input("interval1-dropdown", "value"),
    Input("interval2-dropdown", "value"),
    Input("interval", "n_intervals"),  # 用來觸發資料更新用，所以要用input
    Input("k1-limit-slider", "value"),
    Input("k2-limit-slider", "value"),
    State("interval1-dropdown", "value"),
    State("interval2-dropdown", "value")
)
def update_charts(interval1_now, interval2_now,n,k1_limit_slider,k2_limit_slider, interval1, interval2):
    print("更新圖表...", interval1_now, interval2_now)
    def make_fig(set_interval, limit:int=50):
        fig = go.Figure()
        if set_interval and set_interval in dfs and not dfs[set_interval].empty:
            df_disp = dfs[set_interval].iloc[-limit:]
            ind = compute_indicators(df_disp)
            fig.add_trace(go.Candlestick(
                x=ind.index, open=ind["open"], high=ind["high"],
                low=ind["low"], close=ind["close"],
                name=f"K線 {set_interval}"
            ))
            fig.add_trace(go.Scatter(x=ind.index, y=ind["ema20"], mode="lines", name=f"EMA20 {set_interval}"))
            fig.add_trace(go.Scatter(x=ind.index, y=ind["ema60"], mode="lines", name=f"EMA60 {set_interval}"))
            fig.add_trace(go.Scatter(x=ind.index, y=ind["ema120"], mode="lines", name=f"EMA120 {set_interval}"))
            fig.add_trace(go.Bar(x=ind.index, y=ind["volume"], name=f"成交量 {set_interval}", yaxis="y2", opacity=0.3))

            # ====== 顯示最後收盤價 ======
            last_close = ind["close"].iloc[-1]
            last_time = ind.index[-1]

            # 在收盤價位置加點
            fig.add_trace(go.Scatter(
                x=[last_time], y=[last_close],
                mode="markers+text",
                marker=dict(color="blue", size=10, symbol="arrow-bar-left"),
                text=[f" {last_close:.2f}"],  # 在點旁邊顯示價格
                textposition="middle right",
                name="最新收盤價"
            ))

            # 可選：加一條水平線 (表示收盤價水平位置)
            # fig.add_hline(
            #     y=last_close,
            #     line=dict(color="red", dash="dot"),
            #     annotation_text=f"收盤價 {last_close:.2f}",
            #     annotation_position="top right"
            # )

            fig.update_layout(
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified",
                yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Volume")
            )
        return fig

    fig1 = make_fig(interval1, limit=k1_limit_slider)
    fig2 = make_fig(interval2, limit=k2_limit_slider) if interval2 else go.Figure()

    symbol_title = DEFAULT_SYMBOL
    price_display = latest_price if latest_price else "N/A"
    time_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return fig1, fig2, symbol_title, price_display, time_display

if __name__ == "__main__":
    app.run(debug=False)
