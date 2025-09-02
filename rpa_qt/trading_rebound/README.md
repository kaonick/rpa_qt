# Title: 區間反轉交易策略說明

## 簡介

## 規則

* 尋找 A(局部高) → B(局部低) 跌幅 ≥ n(15%)。
* B 之後反彈到 C，漲幅 ≥ 0.5n。
* 確認 C 後轉跌（下一個 pivot 為低點或最新價 < C）。
* 當前收盤價落在買進區間 [(B+C)/2, C] 就列入清單，停損設 B。

## prompt

```text
請幫我寫一個反彈區間操作法，規則如下： 
當從高點A，下跌超過n%，到底部B點，然後反彈0.5n%到C點開始又再下跌，
此時從C點往下到2分之1的B點到C點之間就是要買進的區間，
只要價位在此區間，就可以買入，然後設定停損點是B點 
請用幫我用python寫出一個可以篩選台股中符合此區間的股票，列入可買進股票代號、可買進的高點、可買進的低點、n(下跌百分比)。 
請取得台股近3個月的日K進行過濾與篩選。 
n%設定的篩選條件是15%。
```

## 使用方法

1. 安裝套件（Python 3.9+）
```
pip install -U pandas numpy yfinance requests
```

2. 準備股票清單（可選）
在腳本同層建立 `tw_tickers.txt`，每行輸入一個台股數字代碼，例如：
```
2330
2317
2454
```
若沒有此檔，腳本會用內建的一小份常見台股清單示範。

3. 執行
```
python tw_rebound_scanner.py
```
產生 `rebound_candidates.csv`，欄位：
- symbol（Yahoo 代碼，例如 2330.TW / 6182.TWO）
- exchange（TWSE/TPEX）
- buy_high（可買區間上緣 = C）
- buy_low（可買區間下緣 = (B+C)/2）
- drop_pct（A→B 跌幅%）
- stop_loss（B）
- A_date/B_date/C_date 與 A/B/C 價位
- last_close（最近收盤）

4. 策略與偵測細節
- 以鄰近比較找 pivot（區域高低點），再篩 A(高)→B(低)→C(高) 符合規則者。
- 驗證 C 後有轉跌（下一個 pivot 是低點或最新價 < C）。
- 僅列出「目前價格落在可買區間 [ (B+C)/2 , C ] 內」者。

5. 客製化
- 修改檔頭參數：
  - `N_PCT = 0.15`  # 下跌百分比 n
  - `MIN_REBOUND = 0.5 * N_PCT`  # 反彈 0.5n
  - `LOOKBACK_MONTHS = 3`  # 近幾個月
  - `PIVOT_NEIGHBOR = 1`   # pivot 靈敏度，數字越大越平滑（但越晚偵測）
