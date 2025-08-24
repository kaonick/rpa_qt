import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from dash import Dash, dcc, html, Output, Input
import plotly.graph_objs as go

# === 模擬即時資料 ===
# 這裡用隨機漫步模擬逐筆成交；實務上可替換成交易所 WebSocket (如 Binance) 的最新成交價
class MockTicker:
    def __init__(self, start=30000.0, vol=0.3):
        self.price = float(start)
        self.vol = float(vol)

    def tick(self):
        # 隨機漫步產生下一筆成交價
        self.price *= float(np.exp(np.random.normal(0, self.vol/1000.0)))
        return float(self.price)

def resample_ticks_to_ohlc(tick_prices, window_seconds=1):
    """
    將一段期間的逐筆成交價聚合成一根 K 棒 (OHLC)
    若該秒只有一筆，就 O=H=L=C；沒有則回 None。
    """
    if len(tick_prices) == 0:
        return None
    o = tick_prices[0]
    h = max(tick_prices)
    l = min(tick_prices)
    c = tick_prices[-1]
    v = len(tick_prices)  # 用筆數當作成交量示意
    return o, h, l, c, v

# === 初始化資料（先放幾根 K 棒） ===
CANDLE_SECONDS = 1          # 每根 K 棒的時間（秒）
MAX_CANDLES    = 500        # 畫面最多顯示多少根
ticker         = MockTicker(start=30000, vol=0.6)

now = datetime.utcnow()
index = pd.date_range(now - timedelta(seconds=200*CANDLE_SECONDS),
                      now, freq=f'{CANDLE_SECONDS}S')
prices = [ticker.tick() for _ in range(len(index))]
df = pd.DataFrame({
    'open':  prices,
    'high':  prices,
    'low':   prices,
    'close': prices,
    'volume': np.ones(len(index))
}, index=index)

# === Dash App ===
app = Dash(__name__, title="Real-time Candlestick")

app.layout = html.Div([
    html.Div([
        html.H1("Python 動態即時 K 線圖", style={"margin": "8px 0"}),
        html.Div("資料源：模擬逐筆。改接交易所 WebSocket 即可上線。",
                 style={"color": "#555", "marginBottom": "8px"}),
        html.Div([
            html.Label("顯示根數："),
            dcc.Slider(id="max-candles",
                       min=100, max=1500, step=50, value=MAX_CANDLES,
                       tooltip={"placement":"bottom", "always_visible":True}),
        ], style={"margin":"8px 0"}),
    ]),
    dcc.Graph(id="k-chart", style={"height":"75vh"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0),  # 每秒更新
])

# 用來累積當前秒內的 ticks
_current_second_bucket = []
_last_candle_second    = df.index[-1]

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
    Output("max-candles", "value"),
    Input("interval", "n_intervals"),
    Input("max-candles", "value"),
)
def update_chart(n, max_candles_ui):
    global df, _current_second_bucket, _last_candle_second

    # 1) 產生這一秒內的多筆 tick（模擬）
    #    實務改成：把 WebSocket 來的 tick append 進 _current_second_bucket
    for _ in range(np.random.randint(1, 6)):  # 這秒的 tick 筆數 (1~5 筆)
        _current_second_bucket.append(ticker.tick())

    now_utc = datetime.utcnow()
    this_sec = now_utc.replace(microsecond=0)

    # 2) 若跨秒了，聚合成一根新 K 棒
    if this_sec > _last_candle_second:
        ohlcv = resample_ticks_to_ohlc(_current_second_bucket, CANDLE_SECONDS)
        _current_second_bucket = []
        _last_candle_second = this_sec

        if ohlcv is not None:
            o, h, l, c, v = ohlcv
            new_row = pd.DataFrame(
                {"open":[o], "high":[h], "low":[l], "close":[c], "volume":[v]},
                index=[this_sec]
            )
            df = pd.concat([df, new_row])

            # 控制顯示長度與資料長度
            if len(df) > 5000:
                df = df.iloc[-5000:]

    # 3) 指標計算（只對要顯示的尾段計算即可）
    display_df = df.iloc[-int(max_candles_ui):]
    ind = compute_indicators(display_df)

    # 4) 畫圖
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=ind.index, open=ind["open"], high=ind["high"],
        low=ind["low"], close=ind["close"],
        name="K"
    ))

    # EMA 線
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema20"],  mode="lines", name="EMA20"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema60"],  mode="lines", name="EMA60"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["ema120"], mode="lines", name="EMA120"))

    # SMA 線
    fig.add_trace(go.Scatter(x=ind.index, y=ind["sma20"],  mode="lines", name="SMA20"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["sma60"],  mode="lines", name="SMA60"))
    fig.add_trace(go.Scatter(x=ind.index, y=ind["sma120"], mode="lines", name="SMA120"))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )

    return fig, max_candles_ui

if __name__ == "__main__":
    # http://127.0.0.1:8050  打開瀏覽器即可看到即時 K 線
    # app.run_server(debug=False)
    app.run(debug=False)
