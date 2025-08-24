import threading

import numpy as np
import pandas as pd

from rpa_qt.price_utils.coin_price_ws import KlineWebSocket


def analyze_trading_signal(current_price: float, ema20: float, ema60: float, ema120: float,
                            volume: bool, avg_volume: bool) -> tuple[str, str]:
    """

    """
    is_volume_high=False
    is_volume_low=False
    if avg_volume*1.2 < volume:
        is_volume_high = True

    if avg_volume*0.8 > volume:
        is_volume_low = True


    # 初始化預設值 (Initialize default values)
    signal_description = "無明確訊號" # No clear signal
    action_advice = "觀望" # Observe

    # 定義「靠近」均線的價格閾值 (Define price threshold for "near" EMA, e.g., within 1%)
    price_near_ema_threshold = 0.01

    # 定義均線「糾結」的閾值 (Define EMA "consolidation" threshold, e.g., EMAs within 0.5% of each other)
    ema_closeness_threshold = 0.005

    # --- 策略判斷 (Strategy Prioritization) ---
    # 按照策略的特異性/強度從高到低進行判斷，以避免重複或較弱的訊號覆蓋較強的訊號。
    # (Prioritize strategies from most specific/strongest to more general to prevent weaker signals from overriding stronger ones.)

    # 1. 強勢多頭排列 (Strong Bullish Alignment)
    # 條件: 價格高於所有EMA, 且 EMA20 > EMA60 > EMA120, 伴隨大量
    if current_price > ema20 and ema20 > ema60 and ema60 > ema120 and is_volume_high:
        signal_description = "市場處於強勁上升趨勢，短期、中期、長期均線皆呈多頭排列，並有大量能助推。"
        action_advice = "買入 (大倉位)"
        return action_advice, signal_description

    # 2. 強勢空頭排列 (Strong Bearish Alignment)
    # 條件: 價格低於所有EMA, 且 EMA20 < EMA60 < EMA120, 伴隨大量
    if current_price < ema20 and ema20 < ema60 and ema60 < ema120 and is_volume_high:
        signal_description = "市場處於強勁下跌趨勢，短期、中期、長期均線皆呈空頭排列，並有大量能加速下跌。"
        action_advice = "賣出 (大倉位)"
        return action_advice, signal_description

    # 3. 短線黃金交叉 (Short-term Golden Cross)
    # 條件: EMA20在EMA60上方，且現價在EMA60上方 (暗示多頭趨勢，並假設剛發生或已維持黃金交叉), 伴隨放量
    # Note: 判斷精確的「交叉」需要前一時間點數據，此處是判斷交叉後的「狀態」。
    # (Precise "cross" detection requires previous data. Here we detect the *state* after a cross.)
    if ema20 > ema60 and current_price > ema60 and is_volume_high:
        signal_description = "短期多頭動能增強，EMA20向上穿越EMA60（或已在上方），代表短期趨勢轉強。"
        action_advice = "買入 (中倉位)"
        return action_advice, signal_description

    # 4. 短線死亡交叉 (Short-term Death Cross)
    # 條件: EMA20在EMA60下方，且現價在EMA60下方 (暗示空頭趨勢), 伴隨放量
    if ema20 < ema60 and current_price < ema60 and is_volume_high:
        signal_description = "短期空頭動能增強，EMA20向下穿越EMA60（或已在下方），代表短期趨勢轉弱。"
        action_advice = "賣出 (中倉位)"
        return action_advice, signal_description

    # 5. 中長期黃金交叉 (Mid-to-Long-term Golden Cross)
    # 條件: EMA20在EMA120上方，且現價在EMA120上方, 伴隨放量
    if ema20 > ema120 and current_price > ema120 and is_volume_high:
        signal_description = "中長期趨勢轉強信號，EMA20向上穿越EMA120（或已在上方），可能預示著較大的上升空間。"
        action_advice = "買入 & 加碼"
        return action_advice, signal_description

    # 6. 中長期死亡交叉 (Mid-to-Long-term Death Cross)
    # 條件: EMA20在EMA120下方，且現價在EMA120下方, 伴隨放量
    if ema20 < ema120 and current_price < ema120 and is_volume_high:
        signal_description = "中長期趨勢轉弱信號，EMA20向下穿越EMA120（或已在下方），可能預示著較大的下跌空間。"
        action_advice = "賣出 & 減碼"
        return action_advice, signal_description

    # 7. 價格回踩EMA支撐 (Price Retracement to EMA Support)
    # 條件: 均線呈多頭排列, 價格在長期支撐上方, 且靠近短期或中期EMA, 伴隨縮量
    if (ema20 > ema60 and ema60 > ema120 and # 均線多頭排列，暗示上升趨勢 (Bullish EMA order implies uptrend)
        current_price > ema120 and # 價格在長期支撐上方 (Price above long-term support)
        (abs(current_price - ema20) / ema20 < price_near_ema_threshold or
         abs(current_price - ema60) / ema60 < price_near_ema_threshold) and # 價格靠近EMA20或EMA60 (Price near EMA20 or EMA60)
        is_volume_low): # 回踩時縮量 (Retracement with low volume)
        signal_description = "價格在上升趨勢中回落至均線附近，獲得支撐後反彈，縮量回踩表明拋壓減輕。"
        action_advice = "買入 (觀察反彈K線)"
        return action_advice, signal_description

    # 8. 價格觸及EMA壓力 (Price Touching EMA Resistance)
    # 條件: 均線呈空頭排列, 價格在長期壓力下方, 且靠近短期或中期EMA, 伴隨縮量
    if (ema20 < ema60 and ema60 < ema120 and # 均線空頭排列，暗示下降趨勢 (Bearish EMA order implies downtrend)
        current_price < ema120 and # 價格在長期壓力下方 (Price below long-term resistance)
        (abs(current_price - ema20) / ema20 < price_near_ema_threshold or
         abs(current_price - ema60) / ema60 < price_near_ema_threshold) and # 價格靠近EMA20或EMA60 (Price near EMA20 or EMA60)
        is_volume_low): # 觸及時縮量 (Touching resistance with low volume)
        signal_description = "價格在下降趨勢中反彈至均線附近，遭遇壓力後回落，縮量反彈表明買盤不足。"
        action_advice = "賣出 (觀察受阻K線)"
        return action_advice, signal_description

    # 9. 均線糾結盤整 (EMA Consolidation / Range-bound)
    # 條件: 短中長期EMA之間距離接近 (糾結), 且非高量
    is_consolidated = (abs(ema20 - ema60) / ema60 < ema_closeness_threshold and
                       abs(ema60 - ema120) / ema120 < ema_closeness_threshold)
    if is_consolidated and not is_volume_high: # 均線糾結且非高量 (EMAs tangled and not high volume)
        signal_description = "均線相互纏繞，市場趨勢不明顯，多空力量均衡，容易出現假突破。"
        action_advice = "觀望 / 區間操作"
        return action_advice, signal_description

    # 10. 盤整區間突破 (Breakout from Consolidation)
    # 條件: 不處於糾結狀態, 且伴隨大量 (暗示突破), 並形成明確的多空排列傾向
    if not is_consolidated and is_volume_high: # 不糾結且大量 (Not consolidating and high volume)
        if current_price > ema120 and ema20 > ema60: # 向上突破的偏向 (Upward breakout bias)
            signal_description = "價格突破長期整理區間，均線開始向上發散，並伴隨大量能確認方向。"
            action_advice = "買入 (向上突破)"
            return action_advice, signal_description
        elif current_price < ema120 and ema20 < ema60: # 向下突破的偏向 (Downward breakout bias)
            signal_description = "價格突破長期整理區間，均線開始向下發散，並伴隨大量能確認方向。"
            action_advice = "賣出 (向下突破)"
            return action_advice, signal_description

    return action_advice, signal_description



class Strategy:
    def __init__(self, capital=100000, leverage=3, unit=100):
        self.capital = capital              # 總資金
        self.leverage = leverage            # 槓桿倍數 (n倍)
        self.unit = unit                    # 分成100等份 = N
        self.position = 0                   # 目前持倉數量 (N)
        self.entry_price = None             # 當前均價
        self.highest_price = None           # 買進後最高價 (移動停損用)
        self.lowest_price = None            # 空單最低價 (移動停損用)
        self.history = []                   # 紀錄操作

    def decide(self, row, avg_vol):
        ema20, ema60, ema120, vol, close = row.ema20, row.ema60, row.ema120, row.volume, row.close
        signal = "HOLD"
        size = 0   # 預計操作倉位

        # 判斷成交量狀態
        if vol > 1.5 * avg_vol:
            vol_state = "High"
        elif vol < 0.8 * avg_vol:
            vol_state = "Low"
        else:
            vol_state = "Normal"

        # ----------- 多空決策表 -----------
        if ema20 > ema60 > ema120:
            if vol_state == "High":
                signal, size = "BUY", 5
            elif vol_state == "Normal":
                signal, size = "BUY", 1
        elif ema20 < ema60 < ema120:
            if vol_state == "High":
                signal, size = "SELL", 5
            elif vol_state == "Normal":
                signal, size = "SELL", 1
        elif ema20 > ema60 and row.ema20.shift(1) <= row.ema60.shift(1):  # 黃金交叉
            if vol_state in ["High", "Normal"]:
                signal, size = "BUY", 1
        elif ema20 < ema60 and row.ema20.shift(1) >= row.ema60.shift(1):  # 死亡交叉
            if vol_state in ["High", "Normal"]:
                signal, size = "SELL", 1

        # ----------- 資金控管 -----------
        if signal in ["BUY", "SELL"]:
            # 新倉 or 加碼 (最多 30N)
            if abs(self.position) + size <= 30:
                if self.position == 0:  # 開倉
                    self.entry_price = close
                    self.highest_price = close
                    self.lowest_price = close
                    self.position = size if signal == "BUY" else -size
                else:  # 加碼
                    # 更新均價
                    self.entry_price = (self.entry_price * abs(self.position) + close * size) / (abs(self.position) + size)
                    self.position += size if signal == "BUY" else -size
            else:
                signal = "HOLD"

        # ----------- 移動停損 -----------
        exit_flag = False
        if self.position > 0:  # 多單
            self.highest_price = max(self.highest_price, close)
            stop_loss = self.entry_price * 0.95
            trail_stop = self.highest_price * 0.97
            if close <= stop_loss or close <= trail_stop:
                exit_flag = True
        elif self.position < 0:  # 空單
            self.lowest_price = min(self.lowest_price, close)
            stop_loss = self.entry_price * 1.05
            trail_stop = self.lowest_price * 1.03
            if close >= stop_loss or close >= trail_stop:
                exit_flag = True

        if exit_flag:
            signal = "EXIT"
            self.position = 0
            self.entry_price = None
            self.highest_price = None
            self.lowest_price = None

        # ----------- 紀錄 -----------
        self.history.append({
            "close": close,
            "signal": signal,
            "pos": self.position,
            "entry": self.entry_price,
            "vol": vol_state
        })
        return signal, self.position, self.entry_price


class TradingStrategy:
    def __init__(self, capital=100000, leverage=3):
        self.capital = capital
        self.N = capital / 100       # 一份倉位大小
        self.max_position = 30 * self.N
        self.position = 0            # 當前持倉
        self.avg_price = 0           # 持倉均價
        self.entry_price = None      # 進場價 (記錄當次開倉的現價)
        self.leverage = leverage
        self.stop_loss = None
        self.highest = None
        self.lowest = None

    # 判斷多空信號，與決定買賣倉位大小
    def check_signal(self, close, ema20, ema60, ema120, volume, avg_volume):
        """ 根據EMA排列 + 現價 + 量能，產生交易信號 """
        print("判斷多空信號，與決定買賣倉位大小")
        signal = None
        pos_size = 0

        # ====== 多頭趨勢 ======
        if ema20 > ema60 > ema120 and close > ema20:
            if volume > avg_volume * 1.2:  # 放量上漲
                signal = "Buy"
                pos_size = 5 * self.N  # 大倉位
            else:
                signal = "Buy small"
                pos_size = 1 * self.N  # 小倉位

        # ====== 空頭趨勢 ======
        elif ema20 < ema60 < ema120 and close < ema20:
            if volume > avg_volume * 1.2:  # 放量下跌
                signal = "Sell"
                pos_size = 5 * self.N
            else:
                signal = "Sell small"
                pos_size = 1 * self.N

        # ====== 現價與 EMA20 偏離過大，減少倉位 ======
        if signal:
            deviation = abs(close - ema20) / ema20
            if deviation > 0.05:  # 偏離超過5%
                pos_size = max(1 * self.N, pos_size // 2)
                print(f"⚠️ 現價 {close:.2f} 與 EMA20 {ema20:.2f} 偏離 {deviation * 100:.2f}%，縮小倉位")

        # ====== 可選：現價與 entry_price 偏離過大，也可忽略信號 ======
        if self.entry_price:
            entry_dev = abs(close - self.entry_price) / self.entry_price
            if entry_dev > 0.05:
                pos_size = max(1 * self.N, pos_size // 2)
                print(f"⚠️ 現價 {close:.2f} 與 entry_price {self.entry_price:.2f} 偏離 {entry_dev * 100:.2f}%，縮小倉位")

        return signal, pos_size

    def update_position(self, close, signal, pos_size):
        """ 根據交易信號，更新倉位與停損點 """
        print("更新倉位與停損點")

        if signal in ["Buy", "Buy small"]:
            add_size = min(pos_size, self.max_position - self.position)
            if add_size > 0:
                # 計算新的均價
                self.avg_price = (self.avg_price * self.position + close * add_size) / (self.position + add_size)
                self.position += add_size
                self.entry_price = close
                self.stop_loss = self.avg_price * 0.95
                self.highest = close
                print(f"✅ 買進 {add_size:.2f}，現價 {close:.2f}，均價 {self.avg_price:.2f}，停損 {self.stop_loss:.2f}")

        elif signal in ["Sell", "Sell small"]:
            reduce_size = min(pos_size, self.position)
            if reduce_size > 0:
                self.position -= reduce_size
                print(f"🔻 賣出 {reduce_size:.2f}，現價 {close:.2f}，剩餘倉位 {self.position:.2f}")

    def check_stop_loss(self, close):
        """ 停損與移動停損判斷 """
        print("停損與移動停損判斷")

        if self.position > 0:
            # 更新最高價
            self.highest = max(self.highest, close)

            # 初始停損 (均價 -5%)
            if close <= self.stop_loss:
                print(f"⛔ 觸發初始停損 {close:.2f}，全部平倉")
                self.position = 0
                self.entry_price = None

            # 移動停損 (回調超過3%)
            elif close <= self.highest * 0.97:
                print(f"⚠️ 觸發移動停損 {close:.2f}，全部平倉")
                self.position = 0
                self.entry_price = None


class StrategyThread:
    def __init__(self, interval="1s",dfs:{}={}):
        self.dfs = dfs  # 儲存不同 interval 的 K 線資料
        self.strategy = TradingStrategy(capital=500, leverage=3)
        self.interval = interval
        self.last_signal = ""


    def _run(self):

        while True:
            if self.interval in self.dfs and not self.dfs[self.interval].empty:
                df = self.dfs[self.interval]
                df = df.sort_index()
                df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
                df["ema60"] = df["close"].ewm(span=60, adjust=False).mean()
                df["ema120"] = df["close"].ewm(span=120, adjust=False).mean()
                df["avg_vol"] = df["volume"].rolling(20, min_periods=1).mean()

                latest_row = df.iloc[-1]

                action_advice, signal_description=analyze_trading_signal(current_price=latest_row.close,
                                       ema20=latest_row.ema20,
                                       ema60=latest_row.ema60,
                                       ema120=latest_row.ema120,
                                       volume=latest_row.volume,
                                       avg_volume=latest_row.avg_vol
                                       )
                if self.last_signal==f"{action_advice};{signal_description}":
                    continue
                else:
                    self.last_signal=f"{action_advice};{signal_description}"
                    print(f"{latest_row.name} price:{latest_row.close} action_advice: {action_advice}, signal_description: {signal_description}")


                # signal, pos_size = self.strategy.check_signal(
                #     close=latest_row.close,
                #     ema20=latest_row.ema20,
                #     ema60=latest_row.ema60,
                #     ema120=latest_row.ema120,
                #     volume=latest_row.volume,
                #     avg_volume=latest_row.avg_vol
                # )
                #
                # if signal:
                #     self.strategy.update_position(latest_row.close, signal, pos_size)
                #
                # self.strategy.check_stop_loss(latest_row.close)

            # 每秒檢查一次
            threading.Event().wait(1)


    def start(self):
        """啟動所有 interval 的 WebSocket"""
        t = threading.Thread(target=self._run, daemon=True)
        t.start()




def tmp_run_strategy():
    DEFAULT_SYMBOL = "SOLUSDT"
    DEFAULT_INTERVAL_2 = "5m"

    dfs = {}
    kws2 = KlineWebSocket(symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL_2, dfs=dfs)
    kws2.start()

    sth = StrategyThread(interval=DEFAULT_INTERVAL_2, dfs=dfs)
    sth.start()

    # 很重要：加了while，thread才會一直跑！
    import time
    while True:
        time.sleep(0.7)  # 等 10 秒接收資料


if __name__ == '__main__':
    tmp_run_strategy()

