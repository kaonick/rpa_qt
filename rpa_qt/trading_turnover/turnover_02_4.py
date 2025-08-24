import json
import threading
import pandas as pd
from datetime import datetime
from dash import Dash, dcc, html, Output, Input, State
import plotly.graph_objs as go
import websocket
import time  # For graceful shutdown (optional, but good for explicit closes)

# =======================
# 全域設定 - Global Configuration
# =======================
DEFAULT_SYMBOL = "SOLUSDT"
DEFAULT_INTERVAL = "1s"
INTERVAL_OPTIONS = ["1s", "5s", "15s", "30s", "1m", "5m", "15m", "30m", "1h", "4h", "1d"]

# 儲存不同時間間隔的 K 線資料 - Stores K-line data for different time intervals
dfs = {}
# 即時價格 - Latest real-time price
latest_price = None

# Threading locks for safe access to shared data
data_lock = threading.Lock()
# Stores active WebSocketApp instances and their threads, keyed by (symbol, interval) tuple
active_wss = {}


# =======================
# WebSocket 函式 - WebSocket Functions
# =======================
def run_ws(symbol, interval):
    """
    Creates a WebSocketApp instance for a given symbol and interval.
    The on_message, on_error, and on_close handlers are defined within.
    """
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"

    def on_message(ws, message):
        """
        Callback function executed when a new message is received from the WebSocket.
        Parses K-line data and updates the global `dfs` and `latest_price`.
        """
        nonlocal interval  # Access interval from the enclosing scope
        global latest_price

        data = json.loads(message)
        k = data["k"]
        ts = datetime.fromtimestamp(k["t"] / 1000.0)  # Convert timestamp to datetime object

        # Create a new DataFrame row for the incoming K-line data
        new_row = pd.DataFrame({
            "open": [float(k["o"])],
            "high": [float(k["h"])],
            "low": [float(k["l"])],
            "close": [float(k["c"])],
            "volume": [float(k["v"])],
        }, index=[ts])

        with data_lock:
            # Update the global latest_price. For simplicity, any WS can update it.
            # If a specific interval's price is desired, this logic would need refinement.
            latest_price = float(k["c"])

            # Ensure the DataFrame for the current interval exists
            if interval not in dfs:
                dfs[interval] = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

            # Efficiently update or append K-line data
            if ts in dfs[interval].index:
                # If the timestamp already exists (e.g., the last K-line is still forming), update it
                dfs[interval].loc[ts] = new_row.loc[ts]
            else:
                # If it's a new timestamp, append the new row and sort by index
                dfs[interval] = pd.concat([dfs[interval], new_row]).sort_index()
                # Optionally, limit the DataFrame size to manage memory for high-frequency data
                if len(dfs[interval]) > 1000:  # Keep only the last 1000 data points
                    dfs[interval] = dfs[interval].iloc[-1000:]

    def on_error(ws, error):
        """Callback function for WebSocket errors."""
        print(f"WebSocket {symbol} {interval} 錯誤 (Error):", error)

    def on_close(ws, close_status_code, close_msg):
        """Callback function when WebSocket connection is closed."""
        print(f"WebSocket {symbol} {interval} 關閉 (Closed)")
        # Clean up the active_wss dictionary when a WebSocket closes
        with data_lock:
            if (symbol, interval) in active_wss:
                del active_wss[(symbol, interval)]

    # Create and return the WebSocketApp instance
    ws_app = websocket.WebSocketApp(url, on_message=on_message, on_error=on_error, on_close=on_close)
    return ws_app


def start_ws_thread(symbol, interval):
    """
    Starts a new WebSocket connection in a separate daemon thread for a given symbol and interval.
    Stores the WebSocketApp instance and its thread in `active_wss`.
    """
    # Check if a WebSocket for this (symbol, interval) is already running
    with data_lock:
        if (symbol, interval) in active_wss:
            print(f"WebSocket for {symbol} {interval} is already running. Skipping start.")
            return

    ws_app = run_ws(symbol, interval)
    # Start the WebSocket in a daemon thread so it terminates when the main program exits
    thread = threading.Thread(target=ws_app.run_forever, daemon=True)
    with data_lock:
        active_wss[(symbol, interval)] = {"ws_app": ws_app, "thread": thread}
    thread.start()
    print(f"Started WebSocket for {symbol} {interval}")


def stop_ws_thread(symbol, interval):
    """
    Stops an active WebSocket connection for a given symbol and interval.
    Closes the WebSocketApp and removes its data from `dfs`.
    """
    if (symbol, interval) in active_wss:
        ws_info = active_wss[(symbol, interval)]
        ws_info["ws_app"].close()  # Gracefully close the WebSocket connection
        print(f"Stopped WebSocket for {symbol} {interval}")
        # Remove data associated with the stopped interval to free up memory
        with data_lock:
            if interval in dfs:
                del dfs[interval]
    else:
        print(f"WebSocket for {symbol} {interval} was not found or already stopped.")


# =======================
# 計算指標 - Indicator Calculation
# =======================
def compute_indicators(df):
    """
    Computes various technical indicators (EMA, SMA) for the given DataFrame.
    Returns the DataFrame with new indicator columns.
    Handles cases where there might not be enough data for calculation.
    """
    if df.empty:
        return df

    df_copy = df.copy()  # Operate on a copy to avoid SettingWithCopyWarning

    # Define common functions for cleaner code
    def safe_ewm(data, span):
        return data.ewm(span=span, adjust=False).mean() if len(data) >= span else pd.NA

    def safe_rolling(data, window):
        return data.rolling(window=window, min_periods=1).mean() if len(data) >= window else pd.NA

    # EMA calculations
    df_copy["ema20"] = safe_ewm(df_copy["close"], 20)
    df_copy["ema60"] = safe_ewm(df_copy["close"], 60)
    df_copy["ema120"] = safe_ewm(df_copy["close"], 120)

    # SMA calculations
    df_copy["sma20"] = safe_rolling(df_copy["close"], 20)
    df_copy["sma60"] = safe_rolling(df_copy["close"], 60)
    df_copy["sma120"] = safe_rolling(df_copy["close"], 120)

    return df_copy


# =======================
# Dash App - Dash Application Setup
# =======================
app = Dash(__name__, title="即時 K 線圖")

app.layout = html.Div([
    html.Div([
        html.H2(id="symbol-title", style={"margin": "5px"}),  # Display the symbol title
        html.Div([
            html.Span("即時價格 (Real-time Price): ", style={"margin-right": "5px"}),
            html.Span(id="price-display")  # Display the latest price
        ], style={"margin": "5px"}),
        html.Div([
            html.Span("目前時間 (Current Time): ", style={"margin-right": "5px"}),
            html.Span(id="time-display")  # Display the current time
        ], style={"margin": "5px"}),
        html.Div([
            html.Label("選擇時間間隔1 (Select Interval 1):"),
            dcc.Dropdown(
                id="interval1-dropdown",
                options=[{"label": x, "value": x} for x in INTERVAL_OPTIONS],
                value=DEFAULT_INTERVAL,  # Default selected interval
                clearable=False  # Cannot clear this dropdown
            ),
            html.Label("選擇時間間隔2 (Select Interval 2 - Optional):"),
            dcc.Dropdown(
                id="interval2-dropdown",
                options=[{"label": x, "value": x} for x in INTERVAL_OPTIONS],
                value=None,  # No default for the second interval
                clearable=True  # Can clear this dropdown
            ),
        ], style={"width": "400px", "margin": "5px"})
    ]),
    # 上下兩個圖表 - Two charts, one above the other
    dcc.Graph(id="k-chart1", style={"height": "45vh"}),
    dcc.Graph(id="k-chart2", style={"height": "45vh"}),
    # Interval component to trigger graph updates every 1000ms (1 second)
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])


# =======================
# 更新圖表和 WebSocket Callback - Update Charts and WebSocket Callback
# =======================
@app.callback(
    Output("k-chart1", "figure"),
    Output("k-chart2", "figure"),
    Output("symbol-title", "children"),
    Output("price-display", "children"),
    Output("time-display", "children"),
    Input("interval", "n_intervals"),  # Trigger on interval tick
    Input("interval1-dropdown", "value"),  # Trigger on interval1 change
    Input("interval2-dropdown", "value"),  # Trigger on interval2 change
    State("interval1-dropdown", "value"),  # Get previous value of interval1 for comparison
    State("interval2-dropdown", "value")  # Get previous value of interval2 for comparison
)
def update_charts(n, current_interval1, current_interval2, prev_interval1, prev_interval2):
    """
    Callback function to update the K-line charts, symbol title, price display,
    and current time. It also manages WebSocket connections based on dropdown selections.
    """
    global latest_price

    # --- WebSocket Connection Management ---
    # Check if interval1 has changed and manage its WebSocket connection
    if current_interval1 != prev_interval1:
        if prev_interval1:
            stop_ws_thread(DEFAULT_SYMBOL, prev_interval1)
        if current_interval1:
            start_ws_thread(DEFAULT_SYMBOL, current_interval1)

    # Check if interval2 has changed and manage its WebSocket connection
    if current_interval2 != prev_interval2:
        if prev_interval2:
            stop_ws_thread(DEFAULT_SYMBOL, prev_interval2)
        if current_interval2:  # Only start if a new interval2 is selected (not None)
            start_ws_thread(DEFAULT_SYMBOL, current_interval2)

    # Initial start for default intervals if they haven't been started yet (e.g., first app load)
    # This ensures that on the very first load, the default intervals are connected.
    with data_lock:  # Protect access to active_wss
        if current_interval1 and (DEFAULT_SYMBOL, current_interval1) not in active_wss:
            start_ws_thread(DEFAULT_SYMBOL, current_interval1)
        if current_interval2 and (DEFAULT_SYMBOL, current_interval2) not in active_wss:
            start_ws_thread(DEFAULT_SYMBOL, current_interval2)

    # --- Figure Generation Function ---
    def make_fig(interval_to_plot):
        """Helper function to create a Plotly figure for a given interval."""
        fig = go.Figure()
        with data_lock:  # Acquire lock to read from dfs
            # Check if the interval is valid and data exists
            if interval_to_plot and interval_to_plot in dfs and not dfs[interval_to_plot].empty:
                # Get the latest 500 data points for display
                df_disp = dfs[interval_to_plot].iloc[-500:].copy()  # Operate on a copy for safety
                ind = compute_indicators(df_disp)  # Compute indicators

                # Add Candlestick trace
                fig.add_trace(go.Candlestick(
                    x=ind.index, open=ind["open"], high=ind["high"],
                    low=ind["low"], close=ind["close"],
                    name=f"K線 {interval_to_plot}"
                ))

                # Add EMA traces if available
                if "ema20" in ind.columns and ind["ema20"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["ema20"], mode="lines", name=f"EMA20 {interval_to_plot}"))
                if "ema60" in ind.columns and ind["ema60"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["ema60"], mode="lines", name=f"EMA60 {interval_to_plot}"))
                if "ema120" in ind.columns and ind["ema120"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["ema120"], mode="lines", name=f"EMA120 {interval_to_plot}"))

                # Add SMA traces if available
                if "sma20" in ind.columns and ind["sma20"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["sma20"], mode="lines", name=f"SMA20 {interval_to_plot}",
                                   line=dict(dash="dot")))
                if "sma60" in ind.columns and ind["sma60"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["sma60"], mode="lines", name=f"SMA60 {interval_to_plot}",
                                   line=dict(dash="dot")))
                if "sma120" in ind.columns and ind["sma120"].notna().any():
                    fig.add_trace(
                        go.Scatter(x=ind.index, y=ind["sma120"], mode="lines", name=f"SMA120 {interval_to_plot}",
                                   line=dict(dash="dot")))

                # Add Volume trace (on a secondary y-axis)
                fig.add_trace(
                    go.Bar(x=ind.index, y=ind["volume"], name=f"成交量 {interval_to_plot}", yaxis="y2", opacity=0.3))

                # Update layout for better presentation
                fig.update_layout(
                    xaxis_rangeslider_visible=False,  # Hide the range slider at the bottom
                    margin=dict(l=20, r=20, t=20, b=20),  # Adjust margins
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),  # Position legend
                    hovermode="x unified",  # Unified hover for better data inspection
                    yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Volume"),
                    # Secondary y-axis for volume
                    uirevision=interval_to_plot  # Key for Plotly to remember zoom/pan state per interval
                )
        return fig

    # Generate figures for both charts
    fig1 = make_fig(current_interval1)
    fig2 = make_fig(
        current_interval2) if current_interval2 else go.Figure()  # Create an empty figure if interval2 is not selected

    # Update display elements
    symbol_title = DEFAULT_SYMBOL
    with data_lock:  # Acquire lock to read latest_price
        price_display = f"{latest_price:.2f}" if latest_price is not None else "N/A"
    time_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return fig1, fig2, symbol_title, price_display, time_display


# =======================
# Main execution block
# =======================
if __name__ == "__main__":
    # Start the WebSocket connection for the default interval when the app initializes
    start_ws_thread(DEFAULT_SYMBOL, DEFAULT_INTERVAL)
    # Run the Dash server in debug mode (set to False for production)
    # app.run_server(debug=True)

    app.run(debug=False)
