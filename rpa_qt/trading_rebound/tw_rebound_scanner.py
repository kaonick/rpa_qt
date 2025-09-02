# -*- coding: utf-8 -*-
"""
台股「反彈區間操作法」篩選器（n=15% 預設，可自行調整）
規則：
1) 從高點A下跌超過 n% 到低點B
2) 自B反彈至少 0.5n% 到C，且C之後出現轉跌跡象（例如下一個pivot是低點或最近價格已低於C）
3) 可買區間：從C往下到 (B與C的中點) 之間 [ (B+C)/2 , C ]
4) 停損：B
此腳本：抓「近3個月」日K，找出目前「價格落在可買區間內」的股票，輸出清單。

依賴：pandas, numpy, yfinance, requests（可選）
- 在本機執行：
    pip install -U pandas numpy yfinance requests
- 你可在腳本同層放 'tw_tickers.txt'（每行一個數字代碼，例如 2330 或 6182）；若沒有，會用內建小清單示範。
- 輸出：rebound_candidates.csv
"""
import os
import io
import math
import datetime as dt
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd
import yfinance as yf


# ------ 參數區 ------
N_PCT = 0.15  # n（下跌百分比）= 15%
MIN_REBOUND = 0.5 * N_PCT  # 反彈至少 0.5n
LOOKBACK_MONTHS = 3        # 抓近3個月日K
EXTRA_BUFFER_DAYS = 20     # 多抓幾天，避免不完整窗口
PIVOT_NEIGHBOR = 1         # 判定區域極值時的鄰近比較天數（1=嚴格相鄰）


def load_universe() -> List[str]:
    """
    優先嘗試讀取 tw_tickers.txt（每行一個數字代碼，例如 2330）
    若無，使用預設小清單（示範用）。
    回傳純數字代碼列表（不含 .TW / .TWO 後綴）
    """
    default_list = [
        "2330",  # 台積電
        "2317",  # 鴻海
        "2454",  # 聯發科
        "2303",  # 聯電
        "2881",  # 富邦金
        "2882",  # 國泰金
        "2603",  # 長榮
        "2615",  # 萬海
        "1301",  # 台塑
        "1303",  # 南亞
        "6505",  # 台塑化
        "2412",  # 中華電
        "3481",  # 群創
    ]
    path = "tw_tickers.txt"
    if os.path.exists(path):
        with io.open(path, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f if line.strip()]
        # 僅保留數字
        items = [s for s in items if s.isdigit()]
        if items:
            return items
    return default_list


def try_download_symbol(numeric_code: str) -> Tuple[str, Optional[pd.DataFrame], Optional[str]]:
    """
    給純數字代碼，如 '2330'。
    依序嘗試 '2330.TW'（上市）、'2330.TWO'（上櫃）。
    成功時回傳 (yahoo_symbol, df, exchange)
    若都失敗，回傳 (original, None, None)
    """
    for suffix, exch in [(".TW", "TWSE"), (".TWO", "TPEX")]:
        symbol = numeric_code + suffix
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=False)
            if df is not None and len(df) > 0:
                df = df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna()
                return symbol, df, exch
        except Exception:
            pass
    return numeric_code, None, None


def slice_last_n_months(df: pd.DataFrame, months: int = 3, extra_days: int = 20) -> pd.DataFrame:
    end_date = df.index.max()
    start_date = end_date - pd.DateOffset(months=months) - pd.Timedelta(days=extra_days)
    return df[df.index >= start_date]


def find_pivots(close: pd.Series, neighbor: int = 1) -> List[Tuple[int, float, str]]:
    """
    以簡單相鄰比較找區域極值（pivot），回傳 list of (index_pos, price, kind)
    kind: 'H'（高點）或 'L'（低點）
    """
    pivots = []
    for i in range(neighbor, len(close) - neighbor):
        window = close.iloc[i - neighbor:i + neighbor + 1]
        center = close.iloc[i].item()  # 單一值 -> float
        wmax = window.max().item()     # 區域最大值
        wmin = window.min().item()     # 區域最小值
        left = window.iloc[0].item()
        right = window.iloc[-1].item()

        # 區域高點
        if center == wmax and (center > left or center > right):
            pivots.append((i, center, 'H'))
        # 區域低點
        elif center == wmin and (center < left or center < right):
            pivots.append((i, center, 'L'))
    return pivots




def detect_abc(close: pd.Series, n_pct: float, min_rebound: float, neighbor: int = 1) -> Optional[Dict]:
    """
    從 pivot 序列中找出符合規則的 (A 高點, B 低點, C 高點)。
    條件：
    - (A->B) 跌幅 >= n_pct
    - (B->C) 漲幅 >= min_rebound
    - C 之後有轉跌跡象（下一個pivot是低點，或最新收盤 < C)
    若找到，回傳 dict，否則 None。
    若有多組，回傳離現在最近的一組。
    """
    pivots = find_pivots(close, neighbor=neighbor)
    if len(pivots) < 3:
        return None

    candidates = []
    for i in range(len(pivots) - 2):
        (ia, pa, ka) = pivots[i]
        (ib, pb, kb) = pivots[i + 1]
        (ic, pc, kc) = pivots[i + 2]
        if ka == 'H' and kb == 'L' and kc == 'H' and ia < ib < ic:
            drop = (pa - pb) / pa
            rebound = (pc - pb) / pb
            if drop >= n_pct and rebound >= min_rebound:
                # 檢查C後是否轉跌
                turned_down = False
                if i + 3 < len(pivots):
                    next_kind = pivots[i + 3][2]
                    if next_kind == 'L':
                        turned_down = True
                else:
                    # 沒有下一個pivot，用「最近價格 < C」當作轉跌跡象
                    if float(close.iloc[-1]) < pc:
                        turned_down = True

                if turned_down:
                    candidates.append({
                        "ia": ia, "pa": pa,
                        "ib": ib, "pb": pb,
                        "ic": ic, "pc": pc,
                        "drop": drop, "rebound": rebound
                    })

    if not candidates:
        return None

    # 取離現在最近的C
    best = max(candidates, key=lambda d: d["ic"])
    return best


def scan_symbol(numeric_code: str, n_pct: float = N_PCT, min_rebound: float = MIN_REBOUND,
                neighbor: int = PIVOT_NEIGHBOR) -> Optional[Dict]:
    """
    回傳一筆命中的資訊（或 None）：
    {
      'symbol': '2330.TW', 'exchange': 'TWSE',
      'A_date': ..., 'B_date': ..., 'C_date': ...,
      'A': float, 'B': float, 'C': float,
      'drop_pct': float,
      'buy_high': float, 'buy_low': float,
      'stop_loss': float,
      'last_close': float, 'in_zone': bool
    }
    僅當 in_zone = True（目前價在可買區間）時，才列入輸出清單。
    """
    ysym, df, exch = try_download_symbol(numeric_code)
    if df is None:
        return None

    df = slice_last_n_months(df, months=LOOKBACK_MONTHS, extra_days=EXTRA_BUFFER_DAYS)
    if len(df) < 30:  # 資料太少
        return None

    close = df["Close"].astype(float).copy()
    abc = detect_abc(close, n_pct=n_pct, min_rebound=min_rebound, neighbor=neighbor)
    if not abc:
        print(f"{numeric_code}: 無符合 ABC 組合")
        return None

    ia, ib, ic = abc["ia"], abc["ib"], abc["ic"]
    pa, pb, pc = abc["pa"], abc["pb"], abc["pc"]
    drop = abc["drop"]

    # 可買區間：[(B+C)/2, C]
    buy_low = (pb + pc) / 2.0
    buy_high = pc

    last_close = float(close.iloc[-1])
    in_zone = (buy_low <= last_close <= buy_high)

    if not in_zone:
        print(f"{numeric_code}: 價格不在可買區間 ({buy_low:.2f} ~ {buy_high:.2f})，目前 {last_close:.2f}")
        return None

    print(f"{numeric_code}: 命中！價格在可買區間 ({buy_low:.2f} ~ {buy_high:.2f})，目前 {last_close:.2f}")

    dates = df.index
    return {
        "symbol": ysym,
        "exchange": exch,
        "A_date": dates[ia].date(),
        "B_date": dates[ib].date(),
        "C_date": dates[ic].date(),
        "A": round(pa, 2),
        "B": round(pb, 2),
        "C": round(pc, 2),
        "drop_pct": round(drop * 100, 2),
        "buy_high": round(buy_high, 2),
        "buy_low": round(buy_low, 2),
        "stop_loss": round(pb, 2),
        "last_close": round(last_close, 2),
    }


def run_scan():
    universe = load_universe()
    results = []
    for code in universe:
        try:
            row = scan_symbol(code, n_pct=N_PCT, min_rebound=MIN_REBOUND, neighbor=PIVOT_NEIGHBOR)
            if row:
                results.append(row)
        except Exception as e:
            # 不中斷，繼續掃描其他股票
            print(f"掃描 {code} 時發生錯誤：{e}")
            pass

    if results:
        out_df = pd.DataFrame(results)[
            ["symbol", "exchange", "buy_high", "buy_low", "drop_pct", "stop_loss",
             "A_date", "B_date", "C_date", "A", "B", "C", "last_close"]
        ].sort_values(["exchange", "symbol"]).reset_index(drop=True)
    else:
        out_df = pd.DataFrame(columns=[
            "symbol", "exchange", "buy_high", "buy_low", "drop_pct", "stop_loss",
            "A_date", "B_date", "C_date", "A", "B", "C", "last_close"
        ])

    save_path = "rebound_candidates.csv"
    out_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"完成。結果已儲存：{save_path}")
    if results:
        print(out_df.to_string(index=False))
    else:
        print("目前沒有股票在可買區間。")

if __name__ == "__main__":
    run_scan()
