# 富邦api申請

## 簽署
* 富邦e點通APP：從手機中簽署API使用同意書，簽署完後，應該是隔天才能使用API。
  * 富邦e點通APP→帳務查詢→線上簽署→2.應用程式介面(API)服務申請書暨聲明書。(線上簽署，簽署之後，會顯示「已申請待測試」)
* 富邦online APP
  * 透過富邦online APP簽署「條件單同意書」。
  * https://www.fbs.com.tw/TradeAPI/docs/smart-condition/prepare

## 驗證
* 下載憑證：
  * https://www.fbs.com.tw/Certificate/Management
  * 或是使用C:\CAFubon\TCEM.exe管理憑證
    * 使用證券帳號、密碼登入。
    * 下載憑證，憑證也要設置憑證密碼。
    * 下載位置：C:\CAFubon\{帳號}\{帳號}.pfx
* 驗證：採以下方法驗證：
以下連線測試方法請擇一進行，24:00前申請並完成測試，隔日即可使用。
方法一 : 路徑C\:Fubon e01\API3執行「InstallFubonE01API2」，並開啟「API_DLL」進行連線測試
方法二 : 使用XQ全球交易贏家帳號登入XQ，上方選單列選擇交易、帳號設定，並以富邦證券帳號登入
方法三 : 以新一代API登入，下載SDK後，撰寫程式碼(python/C#...等) 執行登入
第一次登入會顯示【帳號無使用權限】，即代表API連線測試成功。


## sdk安裝與使用
* 主要網址：
  * https://www.fbs.com.tw/TradeAPI/
  * 下載SDK
  * 安裝whl檔案
    * uv add ./whl/fubon_neo-2.2.4-cp37-abi3-win_amd64.whl
    * 必須是python 3.12以上版本才能安裝
* 測試：
  * 當天測試：會不成功。要隔天才會生效。

## 主要參數對照表(constants)

* https://www.fbs.com.tw/TradeAPI/docs/trading/library/python/EnumMatrix/#constants--%E6%AC%84%E4%BD%8D%E5%B0%8D%E6%87%89%E6%95%B8%E5%80%BC-