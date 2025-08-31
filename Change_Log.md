### 2024/x/x:
* System:
* Frontend：
* Tasks：

### 待辦事項：
* [ ] 交易功能：連接交易所API進行自動下單，可以設定每次交易的數量(預設=2)、槓桿倍數(預設=3)。(目前沒有這個功能)
* [ ] 停損/停利功能：

### 2025/09/02:
* /trading_swing:用來進行波段交易用。
  * trading_swing.py:
    * 步驟：
      * 下載日K線資料。
      * 計算技術指標（EMA20, EMA60, EMA120）。
      * 回策
      * 計算績效
      * 繪圖
    * 有回策與實際交易的功能。
  * 待改善：
    * 買賣的決策邏輯需要再優化。
    * 停損停利的邏輯需要再優化。
    * 圖表改成用dash來呈現。


### 2025/08/26:
* /trading_turnover:
  * strategy:
    * 使用last_row跟previous_row來判斷短中長期k線的變化，來決定交易決策。
    * 重新將SIGNAL_LIST的結構改為字典，方便後續擴充。
* /price_utils:
  * coin_price_ws.py:
    * 增加斷線後重連的功能。


### 2025/02/06:
* logs:
  * project start


