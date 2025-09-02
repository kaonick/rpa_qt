### 2024/x/x:
* System:
* Frontend：
* Tasks：

### Roadmap:
* [x] 取得台股股票清單。
* [x] 取得個股歷史K線資料。
* [x] 交易方案：
  * [x] trading_rebound：反彈區間交易策略。
    * [x] 載入股票清單。load_universe()
    * [x] 下載歷史K線資料。try_download_symbol()
    * [x] scan_symbol()：掃描符合條件的股票。
      * [x] find_pivots()：尋找區域高低點。
      * [x] detect_abc()：偵測是否符合abc轉折。
    * [x] 將有符合的儲存結果至CSV檔案。rebound_candidates.csv
    * [ ] 待開發功能：
      * [ ] 畫圖功能：將符合條件的股票畫出K線圖，並標記A、B、C點。
      * [ ] 可以設定n的參數(預設=15%)。
      * [ ] 可以設定停損點(預設=B點)。
      * [ ] 回策功能：模擬歷史資料進行策略測試。
      * [ ] 交易功能：連接交易所API進行自動下單，可以設定每次交易的數量(預設=2)、槓桿倍數(預設=3)。(目前沒有這個功能)
      * [ ] 停損/停利功能：
  * [x] trading_turnover：均量突破交易策略。


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


