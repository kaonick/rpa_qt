import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

plt.style.use('seaborn-v0_8')  # you can change later

# ---------- 基本參數（可調） ----------
ENTRY_BREAKOUT = 20        # 海龜原始常用 20 日突破進場
EXIT_BREAKOUT  = 10        # 退出條件：10 日低點
ATR_PERIOD     = 20        # 計算 ATR 的週期
RISK_PER_TRADE = 0.01      # 每筆交易風險佔資本比 (1% => 0.01)
MAX_UNITS      = 4         # 最多金字塔倉位單位
Pyramid_ADD    = 0.5       # 加倉間隔 (以 N 為單位) - 每加一單要再上漲多少 (常見 0.5*N)
START_CAPITAL  = 100000    # 初始資本
SLIPPAGE       = 0.0       # 假設滑價
COMMISSION     = 0.0       # 假設手續費（每筆交易固定或可改成比例）


# ---------- 工具函數 ----------
def fetch_ohlcv(ticker: str, start: str, end: str) -> pd.DataFrame:
    """使用 yfinance 取得資料，回傳 OHLCV（index 為日期）"""
    df = yf.download(ticker, start=start, end=end, progress=False)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    return df

def atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """計算 ATR（True Range 的移動平均）"""
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Wilder's ATR (EMA-like with alpha = 1/period) is common for Turtle;  we use rolling mean for simplicity
    return tr.rolling(window=period, min_periods=1).mean()

def n_unit(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """海龜裡的 N（波動性單位）通常使用 ATR 的值"""
    return atr(df, period)

# ---------- 回測主體 ----------
def turtle_backtest(df: pd.DataFrame,
                    entry_breakout: int = ENTRY_BREAKOUT,
                    exit_breakout: int = EXIT_BREAKOUT,
                    atr_period: int = ATR_PERIOD,
                    risk_per_trade: float = RISK_PER_TRADE,
                    max_units: int = MAX_UNITS,
                    pyramid_add: float = Pyramid_ADD,
                    start_capital: float = START_CAPITAL,
                    slippage: float = SLIPPAGE,
                    commission: float = COMMISSION) -> Dict:
    """
    回傳 dict 包含：trade log, equity series, performance summary
    假設每次以「N」計算每單位的頭寸大小：
        position_size = floor( (risk_per_trade * equity) / (N * dollar_risk_per_share) )
    這裡我們把 dollar_risk_per_share = N（ATR），也就是把每股風險當成 N 美元（近似）。
    """
    df = df.copy().assign(date=df.index)
    df['N'] = n_unit(df, period=atr_period)
    df['highest_entry'] = df['high'].rolling(window=entry_breakout, min_periods=1).max().shift(1)  # 防止 look-ahead
    df['lowest_exit']  = df['low'].rolling(window=exit_breakout, min_periods=1).min().shift(1)

    equity = start_capital
    cash = start_capital
    position = 0            # 持股張數（股數）
    entry_price = 0.0
    unit_size_shares = 0
    trades = []
    equity_curve = []

    last_pyramid_price = None
    units_added = 0

    for i in range(len(df)):
        row = df.iloc[i]
        date = row['date']
        close = row['close']
        high = row['high']
        low = row['low']
        N = row['N']
        entry_trigger = row['highest_entry']
        exit_trigger = row['lowest_exit']

        # record equity (market-to-market)
        mkt_val = position * close
        equity = cash + mkt_val
        equity_curve.append({'date': date, 'equity': equity, 'cash': cash, 'position': position, 'price': close})

        # --- Exit check (10-day low) ---
        if position > 0:
            # 若當日低於 exit_trigger，則以 exit_trigger 賣出 (或以當日 low 賣出以保守)
            if low <= exit_trigger:
                sell_price = min(exit_trigger, close)  # 以 exit_trigger 為主，簡化假設
                proceeds = position * sell_price - commission
                cash += proceeds
                trades.append({
                    'date': date, 'type': 'EXIT', 'price': sell_price, 'shares': position, 'equity_after': cash
                })
                position = 0
                entry_price = 0.0
                units_added = 0
                last_pyramid_price = None
                # continue to next day after exit
                continue

        # --- Entry check (20-day high breakout) ---
        if position == 0:
            # 當日若高於 entry_trigger，進場一個 unit（基於 N 計算股數）
            if not np.isnan(entry_trigger) and high >= entry_trigger:
                # 計算每 unit 的股數：以風險資金與N計算
                dollar_risk = risk_per_trade * equity    # 每筆單位風險金額
                if N <= 0 or np.isnan(N):
                    continue
                shares_per_unit = int((dollar_risk / N))  # 簡化：每單位承擔 N 美元風險 -> 股數 = dollar_risk / N
                if shares_per_unit <= 0:
                    continue
                # 進場買一 unit（以 entry_trigger 或 close 決價）
                buy_price = max(entry_trigger, close) + slippage
                cost = shares_per_unit * buy_price + commission
                if cash >= cost:
                    cash -= cost
                    position += shares_per_unit
                    entry_price = buy_price
                    last_pyramid_price = buy_price
                    units_added = 1
                    trades.append({
                        'date': date, 'type': 'ENTRY', 'price': buy_price, 'shares': shares_per_unit, 'units': units_added, 'equity_after': cash + position*close
                    })
        else:
            # 若已有頭寸，檢查 pyramid 加倉條件：價格上漲到 last_pyramid_price + pyramid_add * N 且未超過 max_units
            if units_added < max_units and (not np.isnan(N)) and high >= (last_pyramid_price + pyramid_add * N):
                shares_per_unit = int((risk_per_trade * equity) / N)
                if shares_per_unit > 0:
                    buy_price = last_pyramid_price + pyramid_add * N + slippage
                    cost = shares_per_unit * buy_price + commission
                    if cash >= cost:
                        cash -= cost
                        position += shares_per_unit
                        units_added += 1
                        last_pyramid_price = buy_price
                        trades.append({
                            'date': date, 'type': 'PYRAMID', 'price': buy_price, 'shares': shares_per_unit, 'units': units_added, 'equity_after': cash + position*close
                        })

        # --- 強制止損 (若當日低到 entry_price - 2*N 等) ---
        # Turtle 常用止損：每單位的初始止損為 entry_price - 2*N
        # 這段做一個簡化檢查：若 low <= any unit stop, 出場全部
        if position > 0:
            # 計算目前最緊的止損（以最早進場的止損為代表）：entry_price - 2*N
            stop_price = entry_price - 2 * N if entry_price and (not np.isnan(N)) else None
            if stop_price and low <= stop_price:
                sell_price = max(stop_price, close)
                proceeds = position * sell_price - commission
                cash += proceeds
                trades.append({
                    'date': date, 'type': 'STOP_LOSS', 'price': sell_price, 'shares': position, 'equity_after': cash
                })
                position = 0
                units_added = 0
                last_pyramid_price = None

    equity_df = pd.DataFrame(equity_curve).set_index('date')
    trades_df = pd.DataFrame(trades)
    # 簡單績效
    if len(equity_df) > 0:
        returns = equity_df['equity'].pct_change().fillna(0)
        total_return = (equity_df['equity'].iloc[-1] / start_capital) - 1
        annual_return = (1 + total_return) ** (252 / len(equity_df)) - 1 if len(equity_df) > 0 else 0
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else np.nan
    else:
        total_return = annual_return = sharpe = np.nan

    perf = {
        'start_capital': start_capital,
        'end_capital': equity_df['equity'].iloc[-1] if len(equity_df) > 0 else start_capital,
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe': sharpe,
        'trades': trades_df,
        'equity_curve': equity_df
    }
    return perf


# ---------- 繪圖工具 ----------
def plot_equity(equity_df: pd.DataFrame, ticker: str):
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(equity_df.index, equity_df['equity'], label='Equity')
    ax.set_title(f'Equity Curve - {ticker}')
    ax.set_ylabel('Equity ($)')
    ax.legend()
    plt.tight_layout()
    fname = f'equity_{ticker}.png'
    plt.savefig(fname)
    print(f'[Saved] {fname}')
    plt.close()


# ---------- 範例使用 ----------
if __name__ == '__main__':
    # 修改下面 ticker, start, end 做回測
    ticker = 'TSLA' #'SPY'            # 或 'AAPL', 'TSLA' 等
    start = '2015-01-01'
    end   = '2024-12-31'
    print('Fetching data...')
    df = fetch_ohlcv(ticker, start, end)
    print('Running backtest...')
    perf = turtle_backtest(df,
                           entry_breakout=20,
                           exit_breakout=10,
                           atr_period=20,
                           risk_per_trade=0.01,
                           max_units=4,
                           pyramid_add=0.5,
                           start_capital=100000)
    print('Done. Summary:')
    print(f"Start capital: {perf['start_capital']}")
    print(f"End capital:   {perf['end_capital']:.2f}")
    print(f"Total return:  {perf['total_return']*100:.2f}%")
    print(f"Annual est.:   {perf['annual_return']*100:.2f}%")
    print(f"Sharpe est.:   {perf['sharpe']:.2f}")

    # 交易明細前幾筆
    trades_df = perf['trades']
    if not trades_df.empty:
        print('\nTrades (first 10):')
        print(trades_df.head(10).to_string(index=False))
    # 存圖
    plot_equity(perf['equity_curve'], ticker)
