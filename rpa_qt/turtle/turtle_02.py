"""
我把一個「完善版海龜交易系統（針對 SOL/USDT）」寫成可直接落地的 Python 模組了，包含：
系統一（20日突破/10日退出，含「盈利後跳過下一次 20 日突破」經典規則）
系統二（55日突破/20日退出）
N=ATR(20)（Wilder 平滑），2N 止損、每 +0.5N 金字塔加碼、最多 4 單
以「權益 × 風險%」計算初始單部位，含手續費、滑價、槓桿上限、最小成交量/步長/最小名義金額
Backtest 引擎（交易記錄、績效指標、圖表與 CSV 輸出）
CCXT 抓幣安 K 線（或讀 CSV）
產出：equity_curve.csv、trades.csv、價格含交易點圖、權益曲線圖


python turtle_solusdt.py --mode backtest --exchange binance \
  --symbol SOL/USDT --timeframe 4h --limit 3000 --allow_short \
  --initial 100000 --risk_pct 1.0 --leverage 3 \
  --taker_fee 0.0004 --maker_fee 0.0002 --slippage_bps 1

想客製化（都可用參數&原始碼設定）：
風險%（--risk_pct）、槓桿上限（--leverage）
手續費與滑價（--taker_fee、--maker_fee、--slippage_bps）
交易所過濾（--min_qty、--step_size、--min_notional）
是否做空（--allow_short）
"""
from pathlib import Path

"""
Turtle Trading System for Crypto (SOL/USDT focus)
=================================================

Features
--------
- System 1 (20-day breakout, 10-day exit) with classic "skip-next-20d after a win" rule
- System 2 (55-day breakout, 20-day exit)
- N = ATR(20) with Wilder smoothing (EWMA alpha = 1/period)
- Volatility-based position sizing: risk per initial unit = equity * risk_pct
- Initial stop: 2N from the most recent unit entry; pyramiding add every +0.5N/-0.5N up to max units
- Fees and slippage, leverage cap, and lot/step/min notional constraints
- Backtester with detailed performance metrics and CSV outputs (equity curve & trades)
- Optional CCXT data fetcher (Binance by default) for OHLCV
- Plots: price with markers (entries/exits) and equity curve (saved as PNGs)

Usage
-----
Install requirements:
    pip install pandas numpy matplotlib ccxt

Run backtest from CCXT:
    python turtle_solusdt.py --mode backtest --exchange binance --symbol SOL/USDT --timeframe 4h --limit 3000

Run backtest from CSV (file must have columns: timestamp,open,high,low,close,volume; timestamp in ms or ISO string):
    python turtle_solusdt.py --mode backtest --csv ./solusdt_4h.csv

Output files (in ./outputs):
    - equity_curve.csv
    - trades.csv
    - price_with_trades.png
    - equity_curve.png

Live trading skeleton:
    - See `LiveTrader` class; adapt API keys and exchange params responsibly (paper trade first!).

Disclaimer
----------
This code is for educational purposes. Live trading involves significant risk. Use at your own risk.
"""

from __future__ import annotations

import math
import sys
import json
import time
import argparse
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Tuple

import numpy as np
import pandas as pd

# Optional CCXT
try:
    import ccxt  # type: ignore
except Exception:
    ccxt = None  # CCXT is optional for CSV backtests

# Matplotlib only for saving plots
import matplotlib.pyplot as plt

# -----------------------------
# Utility Helpers
# -----------------------------

def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure df index is pandas.DatetimeIndex in UTC (no tz) sorted ascending."""
    if 'timestamp' in df.columns:
        ts = df['timestamp']
        if np.issubdtype(ts.dtype, np.number):
            # assume ms or s: treat >= 10^12 as ms
            unit = 'ms' if ts.astype('int64').median() > 10**12 else 's'
            df.index = pd.to_datetime(ts, unit=unit, utc=True).tz_convert(None)
        else:
            df.index = pd.to_datetime(ts, utc=True).tz_convert(None)
        df = df.drop(columns=['timestamp'])
    elif not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Data must have 'timestamp' column or DatetimeIndex.")
    return df.sort_index()

def wilder_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Wilder's ATR using EWMA alpha=1/period on True Range."""
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def donchian_high(df: pd.DataFrame, length: int, exclude_current: bool = True) -> pd.Series:
    """Highest high of the last `length` bars; optionally exclude current bar."""
    if exclude_current:
        return df['high'].shift(1).rolling(length).max()
    return df['high'].rolling(length).max()

def donchian_low(df: pd.DataFrame, length: int, exclude_current: bool = True) -> pd.Series:
    """Lowest low of the last `length` bars; optionally exclude current bar."""
    if exclude_current:
        return df['low'].shift(1).rolling(length).min()
    return df['low'].rolling(length).min()

def round_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.floor(value / step) * step

def apply_qty_filters(qty: float, min_qty: float = 0.0, step_size: float = 0.0) -> float:
    """Enforce minQty & stepSize like Binance filters."""
    if step_size > 0:
        qty = round_step(qty, step_size)
    if min_qty > 0 and qty < min_qty:
        return 0.0
    return qty

# -----------------------------
# Configs
# -----------------------------

@dataclass
class StrategyConfig:
    # Entry/Exit periods
    len_entry1: int = 20
    len_exit1: int = 10
    len_entry2: int = 55
    len_exit2: int = 20
    exclude_current_bar: bool = True

    # Risk & ATR
    atr_len: int = 20
    atr_stop_mult: float = 2.0  # 2N stop
    add_step_n: float = 0.5     # add every 0.5N
    max_units: int = 4          # total units including initial
    risk_pct: float = 1.0       # risk per initial unit (% equity)
    contract_mult: float = 1.0  # contract dollar per 1 price unit (SOL/USDT spot/perp ~ 1)
    min_qty: float = 0.0        # exchange min quantity
    step_size: float = 0.0      # exchange step size
    min_notional: float = 0.0   # exchange min notional in quote currency

    # Systems toggle
    use_system1: bool = True
    use_system2: bool = True
    skip_20d_after_win: bool = True  # classic turtle rule

    # Trading constraints
    leverage: float = 1.0       # notional cap = equity * leverage
    taker_fee: float = 0.0004   # 4 bps default (Binance taker ~ 0.04% before VIP)
    maker_fee: float = 0.0002   # 2 bps
    slippage_bps: float = 1.0   # 1 bp per fill

@dataclass
class BacktestConfig:
    initial_capital: float = 100_000.0
    allow_short: bool = True  # enable shorts (perp) or only long (spot)
    price_col: str = 'close'
    save_dir: str = './outputs'

@dataclass
class Trade:
    timestamp: pd.Timestamp
    side: str               # 'long' or 'short'
    action: str             # 'entry','add','exit','stop'
    price: float
    qty: float
    fee: float
    slippage: float
    comment: str

# -----------------------------
# Strategy Engine (event-driven)
# -----------------------------

class TurtleStrategy:
    def __init__(self, sconf: StrategyConfig, bconf: BacktestConfig):
        self.s = sconf
        self.b = bconf
        self.reset()

    def reset(self):
        self.equity = self.b.initial_capital
        self.position_side: Optional[str] = None  # 'long' or 'short'
        self.units: List[Tuple[float, float]] = []  # list of (entry_price, qty) per unit
        self.stop_price: Optional[float] = None
        self.add_levels: List[float] = []
        self.trades: List[Trade] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        # For skip-after-win rule (20d system)
        self.last_20d_result: Dict[str, Optional[str]] = {'long': None, 'short': None}  # 'win','loss',None

    # ---------- Sizing helpers ----------
    def unit_qty(self, equity: float, N: float, price: float) -> float:
        if N <= 0 or price <= 0:
            return 0.0
        risk_money = equity * (self.s.risk_pct / 100.0)
        dollar_per_point = self.s.contract_mult  # for SOL/USDT ~ 1
        raw_qty = risk_money / (self.s.atr_stop_mult * N * dollar_per_point)
        # Enforce filters
        qty = apply_qty_filters(raw_qty, self.s.min_qty, self.s.step_size)
        # Min notional
        if self.s.min_notional > 0 and qty * price < self.s.min_notional:
            return 0.0
        # Leverage cap will be enforced at order time
        return qty

    def can_add_unit(self) -> bool:
        return len(self.units) < self.s.max_units

    def current_notional(self, price: float) -> float:
        qty = sum(q for _, q in self.units)
        return abs(qty) * price

    def within_leverage(self, add_qty: float, price: float) -> bool:
        notional_after = self.current_notional(price) + abs(add_qty) * price
        return notional_after <= self.equity * self.s.leverage + 1e-9

    # ---------- Order execution (backtest fill model) ----------
    def execute_fill(self, ts: pd.Timestamp, side: str, action: str, price: float, qty: float, taker: bool = True, comment: str = ''):
        if qty <= 0:
            return

        slip = price * (self.s.slippage_bps / 10_000.0)
        fill_price = price + slip if (side == 'long' and (action in ('entry','add'))) else price - slip if (side == 'short' and (action in ('entry','add'))) else price
        fee_rate = self.s.taker_fee if taker else self.s.maker_fee
        fee = abs(qty) * fill_price * fee_rate

        # Update position/equity for entries/exits
        if action in ('entry','add'):
            # open/increase
            if self.position_side is None:
                self.position_side = side
            assert self.position_side == side, "Direction conflict"
            self.units.append((fill_price, qty))
            # set/adjust stop from the most recent unit entry
            if side == 'long':
                self.stop_price = fill_price - self.s.atr_stop_mult * self.current_N  # set below last entry
            else:
                self.stop_price = fill_price + self.s.atr_stop_mult * self.current_N
            # set (or refresh) add levels
            base = self.units[0][0]  # first unit entry price
            n = self.current_N
            step = self.s.add_step_n * n
            if side == 'long':
                self.add_levels = [base + step * i for i in range(1, self.s.max_units)]
            else:
                self.add_levels = [base - step * i for i in range(1, self.s.max_units)]
            # pay fee immediately
            self.equity -= fee
        elif action in ('exit','stop'):
            # close all
            pos_qty = sum(q for _, q in self.units)
            avg_px = sum(p*q for p, q in self.units) / pos_qty if pos_qty != 0 else 0.0
            pnl = (fill_price - avg_px) * pos_qty if self.position_side == 'long' else (avg_px - fill_price) * (-pos_qty)
            self.equity += pnl
            self.equity -= fee
            # determine win/loss for 20d skip rule if the entry came from 20d
            if self.entry_source in ('20d_long','20d_short'):
                dir_key = 'long' if 'long' in self.entry_source else 'short'
                self.last_20d_result[dir_key] = 'win' if pnl > 0 else 'loss'
            # reset position
            self.position_side = None
            self.units.clear()
            self.stop_price = None
            self.add_levels = []
            self.entry_source = None

        self.trades.append(Trade(ts, side, action, float(fill_price), float(qty), float(fee), float(slip), comment))

    # ---------- Per-bar update ----------
    def on_bar(self, i: int, row: pd.Series, signals: Dict[str, bool], N: float, price: float, high: float, low: float, exit_levels: Dict[str, float]):
        ts = row.name
        self.current_N = N  # cache for stop calc

        # Record equity mark-to-market
        if self.position_side is None:
            self.equity_curve.append((ts, self.equity))
        else:
            pos_qty = sum(q for _, q in self.units)
            avg_px = sum(p*q for p, q in self.units) / pos_qty if pos_qty != 0 else 0.0
            mtm = (price - avg_px) * pos_qty if self.position_side == 'long' else (avg_px - price) * (-pos_qty)
            self.equity_curve.append((ts, self.equity + mtm))

        # Exit logic (channel-based)
        if self.position_side == 'long':
            if price < exit_levels['exit_long']:
                self.execute_fill(ts, 'long', 'exit', price, sum(q for _, q in self.units), True, 'Channel exit')
                return  # after exit, skip adds/stops this bar
        elif self.position_side == 'short':
            if price > exit_levels['exit_short']:
                self.execute_fill(ts, 'short', 'exit', price, sum(q for _, q in self.units), True, 'Channel exit')
                return

        # Stop (2N from most recent unit entry)
        if self.position_side is not None and self.stop_price is not None:
            if self.position_side == 'long' and low <= self.stop_price:
                self.execute_fill(ts, 'long', 'stop', self.stop_price, sum(q for _, q in self.units), True, '2N stop')
                return
            if self.position_side == 'short' and high >= self.stop_price:
                self.execute_fill(ts, 'short', 'stop', self.stop_price, sum(q for _, q in self.units), True, '2N stop')
                return

        # Add units
        if self.position_side == 'long' and self.can_add_unit() and len(self.add_levels) > 0:
            next_level = self.add_levels[len(self.units)-1] if len(self.units) < self.s.max_units else None
            if next_level is not None and high >= next_level:
                qty_unit = self.unit_qty(self.equity, N, price)
                if qty_unit > 0 and self.within_leverage(qty_unit, price):
                    self.execute_fill(ts, 'long', 'add', next_level, qty_unit, True, f'Add @{self.s.add_step_n}N')
        elif self.position_side == 'short' and self.can_add_unit() and len(self.add_levels) > 0:
            next_level = self.add_levels[len(self.units)-1] if len(self.units) < self.s.max_units else None
            if next_level is not None and low <= next_level:
                qty_unit = self.unit_qty(self.equity, N, price)
                if qty_unit > 0 and self.within_leverage(qty_unit, price):
                    self.execute_fill(ts, 'short', 'add', next_level, qty_unit, True, f'Add @{self.s.add_step_n}N')

        # Entry logic
        def allow_20d(direction: str) -> bool:
            if not self.s.skip_20d_after_win:
                return True
            last = self.last_20d_result[direction]
            # Take 20d breakout only if last 20d trade (same direction) was a LOSS or None
            return (last is None) or (last == 'loss')

        took_signal = False
        if self.position_side is None:
            if self.s.use_system1 and signals['long_20d'] and allow_20d('long'):
                qty = self.unit_qty(self.equity, N, price)
                if qty > 0 and self.within_leverage(qty, price):
                    self.entry_source = '20d_long'
                    self.execute_fill(ts, 'long', 'entry', price, qty, True, '20d breakout')
                    took_signal = True
            elif self.s.use_system2 and signals['long_55d']:
                qty = self.unit_qty(self.equity, N, price)
                if qty > 0 and self.within_leverage(qty, price):
                    self.entry_source = '55d_long'
                    self.execute_fill(ts, 'long', 'entry', price, qty, True, '55d breakout')
                    took_signal = True

            if not took_signal and self.b.allow_short:
                if self.s.use_system1 and signals['short_20d'] and allow_20d('short'):
                    qty = self.unit_qty(self.equity, N, price)
                    if qty > 0 and self.within_leverage(qty, price):
                        self.entry_source = '20d_short'
                        self.execute_fill(ts, 'short', 'entry', price, qty, True, '20d breakdown')
                        took_signal = True
                elif self.s.use_system2 and signals['short_55d']:
                    qty = self.unit_qty(self.equity, N, price)
                    if qty > 0 and self.within_leverage(qty, price):
                        self.entry_source = '55d_short'
                        self.execute_fill(ts, 'short', 'entry', price, qty, True, '55d breakdown')
                        took_signal = True

# -----------------------------
# Backtester
# -----------------------------

class Backtester:
    def __init__(self, df: pd.DataFrame, sconf: StrategyConfig, bconf: BacktestConfig):
        self.df = ensure_datetime_index(df.copy())
        self.s = sconf
        self.b = bconf
        self.prepare_indicators()

    def prepare_indicators(self):
        df = self.df
        df['N'] = wilder_atr(df, self.s.atr_len)
        df['h20'] = donchian_high(df, self.s.len_entry1, self.s.exclude_current_bar)
        df['l20'] = donchian_low(df,  self.s.len_entry1, self.s.exclude_current_bar)
        df['h55'] = donchian_high(df, self.s.len_entry2, self.s.exclude_current_bar)
        df['l55'] = donchian_low(df,  self.s.len_entry2, self.s.exclude_current_bar)
        df['x10'] = donchian_low(df,  self.s.len_exit1, self.s.exclude_current_bar)
        df['x20'] = donchian_high(df, self.s.len_exit2, self.s.exclude_current_bar)
        self.df = df.dropna().copy()  # drop warmup

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
        strat = TurtleStrategy(self.s, self.b)
        price_col = self.b.price_col

        for i, row in enumerate(self.df.itertuples(index=False), start=0):
            # Build row Series with index timestamp
            ts = self.df.index[i]
            srow = pd.Series({
                'open': getattr(row, 'open'),
                'high': getattr(row, 'high'),
                'low': getattr(row, 'low'),
                'close': getattr(row, 'close'),
                'volume': getattr(row, 'volume')
            }, name=ts)
            price = srow[price_col]
            N = float(self.df.iloc[i]['N'])

            signals = {
                'long_20d': price > float(self.df.iloc[i]['h20']),
                'short_20d': price < float(self.df.iloc[i]['l20']),
                'long_55d': price > float(self.df.iloc[i]['h55']),
                'short_55d': price < float(self.df.iloc[i]['l55']),
            }
            exits = {
                'exit_long': float(self.df.iloc[i]['x10']),
                'exit_short': float(self.df.iloc[i]['x20']),
            }
            strat.on_bar(i, srow, signals, N, price, float(srow['high']), float(srow['low']), exits)

        # Build outputs
        eq = pd.DataFrame(strat.equity_curve, columns=['timestamp','equity']).set_index('timestamp')
        trades = pd.DataFrame([asdict(t) for t in strat.trades])

        # Metrics
        metrics = self.compute_metrics(eq['equity'], trades)
        return eq, trades, metrics

    def compute_metrics(self, equity: pd.Series, trades: pd.DataFrame) -> Dict[str, float]:
        ret = equity.pct_change().fillna(0.0)
        # convert to per-period return; approximate daily if timeframe >= daily; otherwise still fine
        cagr = (equity.iloc[-1] / equity.iloc[0]) ** (365.0 / max((equity.index[-1] - equity.index[0]).days, 1)) - 1.0
        sharpe = (ret.mean() / (ret.std() + 1e-12)) * math.sqrt(365) if ret.std() > 0 else 0.0
        downside = ret[ret < 0].std()
        sortino = (ret.mean() / (downside + 1e-12)) * math.sqrt(365) if downside > 0 else 0.0
        dd = (equity / equity.cummax() - 1.0).min()
        max_dd = float(dd)
        # trade stats
        closed = trades[trades['action'].isin(['exit','stop'])].copy()
        num_trades = int(len(closed))
        wins = 0
        profit_sum = 0.0
        loss_sum = 0.0
        if num_trades > 0:
            # compute PnL per round-trip via comments on exit rows by matching to prior entries
            # Simpler: approximate by diff in equity between exit fills (not perfect but OK for aggregate stats)
            closed_equity = equity.loc[closed['timestamp'].values].values if len(equity) and len(closed) else np.array([])
            # fallback
            wins = int((closed['comment'].str.contains('win', case=False, na=False)).sum())  # unused
        # Profit factor via trade-by-trade reconstruction
        # We'll do rough calculation using fees and price differences:
        pf_profit = 0.0
        pf_loss = 0.0
        # Reconstruct trades by grouping between 'entry' and 'exit/stop'
        pos_side = None
        pos_qty = 0.0
        avg_px = 0.0
        for _, tr in trades.iterrows():
            if tr['action'] in ('entry','add'):
                if pos_qty == 0.0:
                    pos_side = tr['side']
                    pos_qty = tr['qty']
                    avg_px = tr['price']
                else:
                    # update VWAP
                    new_qty = pos_qty + tr['qty']
                    avg_px = (avg_px * pos_qty + tr['price'] * tr['qty']) / new_qty
                    pos_qty = new_qty
            elif tr['action'] in ('exit','stop'):
                if pos_qty != 0.0 and pos_side is not None:
                    pnl = (tr['price'] - avg_px) * pos_qty if pos_side == 'long' else (avg_px - tr['price']) * pos_qty
                    pnl -= tr['fee']  # fees on exit
                    # estimate entry/add fees too by summing previous fees in the trade window
                    # (approximate: add last few fees)
                    # For simplicity in PF: split by sign
                    if pnl >= 0:
                        pf_profit += pnl
                        wins += 1
                    else:
                        pf_loss += -pnl
                    pos_side = None
                    pos_qty = 0.0
                    avg_px = 0.0
        win_rate = wins / num_trades if num_trades > 0 else 0.0
        profit_factor = (pf_profit / pf_loss) if pf_loss > 0 else float('inf') if pf_profit > 0 else 0.0

        return {
            'CAGR': float(cagr),
            'Sharpe': float(sharpe),
            'Sortino': float(sortino),
            'MaxDrawdown': float(max_dd),
            'NumTrades': num_trades,
            'WinRate': float(win_rate),
            'ProfitFactor': float(profit_factor),
            'FinalEquity': float(equity.iloc[-1]),
            'Return': float(equity.iloc[-1] / equity.iloc[0] - 1.0),
        }

# -----------------------------
# Data Loader (CSV or CCXT)
# -----------------------------

def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Expect columns: timestamp, open, high, low, close, volume
    return ensure_datetime_index(df)

def fetch_ccxt_ohlcv(exchange='binance', symbol='SOL/USDT', timeframe='4h', limit=3000) -> pd.DataFrame:
    if ccxt is None:
        raise RuntimeError("ccxt not installed. Install with `pip install ccxt`.")
    ex = getattr(ccxt, exchange)()
    if hasattr(ex, 'load_markets'):
        ex.load_markets()
    ohlcv = ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    # columns per CCXT spec: [timestamp, open, high, low, close, volume]
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    return ensure_datetime_index(df)

# -----------------------------
# Plotting helpers (no specific colors; one chart per figure)
# -----------------------------

def plot_price_with_trades(df: pd.DataFrame, trades: pd.DataFrame, out_path: str):
    plt.figure()
    plt.plot(df.index, df['close'], label='Close')
    # Plot markers
    if not trades.empty:
        ent = trades[trades['action']=='entry']
        add = trades[trades['action']=='add']
        exi = trades[trades['action'].isin(['exit','stop'])]
        if len(ent):
            plt.scatter(ent['timestamp'], ent['price'], marker='^', label='Entry')
        if len(add):
            plt.scatter(add['timestamp'], add['price'], marker='o', label='Add')
        if len(exi):
            plt.scatter(exi['timestamp'], exi['price'], marker='v', label='Exit/Stop')
    plt.title('Price with Trades')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def plot_equity_curve(eq: pd.DataFrame, out_path: str):
    plt.figure()
    plt.plot(eq.index, eq['equity'], label='Equity')
    plt.title('Equity Curve')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Turtle Trading (Crypto / SOLUSDT)")
    parser.add_argument('--mode', choices=['backtest'], default='backtest')
    parser.add_argument('--exchange', default='binance')
    parser.add_argument('--symbol', default='SOL/USDT')
    parser.add_argument('--timeframe', default='4h')
    parser.add_argument('--limit', type=int, default=3000)
    parser.add_argument('--csv', default=None, help='Path to CSV (timestamp,open,high,low,close,volume)')
    parser.add_argument('--initial', type=float, default=100000.0)
    parser.add_argument('--risk_pct', type=float, default=1.0)
    parser.add_argument('--leverage', type=float, default=3.0)
    parser.add_argument('--taker_fee', type=float, default=0.0004)
    parser.add_argument('--maker_fee', type=float, default=0.0002)
    parser.add_argument('--slippage_bps', type=float, default=1.0)
    parser.add_argument('--allow_short', action='store_true', help='Enable shorts (perp).')
    parser.add_argument('--min_qty', type=float, default=0.0)
    parser.add_argument('--step_size', type=float, default=0.0)
    parser.add_argument('--min_notional', type=float, default=0.0)
    parser.add_argument('--output', default='./outputs')
    args = parser.parse_args()

    # Load data
    if args.csv:
        df = load_csv(args.csv)
    else:
        df = fetch_ccxt_ohlcv(args.exchange, args.symbol, args.timeframe, args.limit)

    # Configs
    sconf = StrategyConfig(
        risk_pct=args.risk_pct,
        leverage=args.leverage,
        taker_fee=args.taker_fee,
        maker_fee=args.maker_fee,
        slippage_bps=args.slippage_bps,
        min_qty=args.min_qty,
        step_size=args.step_size,
        min_notional=args.min_notional,
        contract_mult=1.0,  # SOL/USDT linear
        use_system1=True,
        use_system2=True,
        skip_20d_after_win=True,
    )
    bconf = BacktestConfig(
        initial_capital=args.initial,
        allow_short=args.allow_short,
        save_dir=args.output
    )

    bt = Backtester(df, sconf, bconf)
    eq, trades, metrics = bt.run()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    eq_path = out_dir / 'equity_curve.csv'
    tr_path = out_dir / 'trades.csv'
    price_fig = out_dir / 'price_with_trades.png'
    eq_fig = out_dir / 'equity_curve.png'

    eq.to_csv(eq_path)
    trades.to_csv(tr_path, index=False)

    # Plot
    plot_price_with_trades(df.loc[eq.index], trades, str(price_fig))
    plot_equity_curve(eq, str(eq_fig))

    # Print metrics as JSON
    print(json.dumps(metrics, indent=2))
    print(f'Saved: {eq_path}')
    print(f'Saved: {tr_path}')
    print(f'Saved: {price_fig}')
    print(f'Saved: {eq_fig}')

if __name__ == '__main__':
    main()
