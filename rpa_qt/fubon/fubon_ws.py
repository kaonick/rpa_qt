import threading
import time

from fubon_neo.sdk import FubonSDK

from rpa_qt.fubon.fubon_auth import fubon_login
import json
import traceback

subscribe_ids = []  # 訂閱頻道 id 列表


class FubonWS:
    def __init__(self):
        self.sdk=fubon_login()
        self.sdk.init_realtime()  # 建立行情元件連線
        self.__relogin_lock = threading.Lock()

    def handle_connect(self):  # 連線成功 callback
        print("行情連接成功")

    def handle_disconnect(code, message):  # 連接斷線 callback
        print(f"行情連接斷線: {code}, {message}")

    def handle_message(self,message):  # 處理接收訊息 callback
        try:
            print(f"Received message: {message}")
            msg = json.loads(message)
            event = msg["event"]
            data = msg["data"]

            if event == "pong" or event == "heartbeat":
                return

            if event == "auth" or event == "authenticated":
                if data["message"] == "Authenticated successfully":
                    print("行情認證成功")

            if event == "subscribed":
                id = data["id"]

                if id in subscribe_ids:
                    print(f"Error: 訂閱 id {id} 已存在列表中")
                else:
                    subscribe_ids.append(id)

            elif event == "unsubscribed":
                id = data["id"]

                try:
                    subscribe_ids.remove(id)
                except:
                    print(f"Error: 查無此筆訂閱 id 資料, id {id}")

            print(f'market data message: {message}')

        except Exception as e:
            self.handle_error(f'Error parsing JSON: {e}', traceback.format_exc())

    def handle_error(self,error, traceback_info=None):  # 處理程式錯誤訊息 callback
        print(f'market data error: {error}')
        if traceback_info:
            print(f'Traceback:\n{traceback_info}')

    def ws_connect(self):
        stock = self.sdk.marketdata.websocket_client.stock
        stock.on("connect", self.handle_connect)
        stock.on("message", self.handle_message)
        stock.on("disconnect", self.handle_disconnect)
        stock.on("error", self.handle_error)

        stock.connect()  # WebSocket 連線

    ## *******************************************************************************************************
    # re-login 相關功能
    #　https://www.fbs.com.tw/TradeAPI/docs/trading/guide/advance/reconnect
    # Event callback
    def __handle_trade_ws_event(self, code, message):
        if code in ["300"]:
            self.__logger.info(f"交易連線異常，啟動重新連線 ..., code {code}")

            try:
                self.sdk.logout()
            except Exception as e:
                self.__logger.debug(f"Exception: {e}")
            finally:
                with self.__relogin_lock:
                    self.__logger.debug(f"Login (a) ...")
                    self.__re_login()

        elif code in ["302"]:
            self.__logger.info(f"交易連線中斷 ..., code {code}")

        else:
            self.__logger.debug(f"Trade ws event (debug) code {code}, msg {message}")

    # 重新連線登入功能
    def __re_login(self, retry_counter=0, max_retry=20):
        if retry_counter > max_retry:
            self.__logger.error(f"交易連線重試次數過多 {retry_counter}，延長重試時間")
            self.__is_alive = False
            time.sleep(5)

        try:
            self.__is_relogin_running = True
            self.__logger.debug(f"re_login retry attempt {retry_counter}")

            self.accounts = None
            self.active_account = None
            if self.sdk is not None:
                try:
                    self.sdk.logout()
                finally:
                    self.sdk = None

            # Establish connection
            self.__logger.info("建立主機連線 ...")
            try:
                self.sdk = FubonSDK() if self.__connection_ip is None else FubonSDK(self.__connection_ip)
            except Exception as e:
                self.__logger.error(f"交易主機連線錯誤 msg: {e}")
                if isinstance(e, str) and "11001" not in e:
                    self.__is_alive = False
                    return False
                else:
                    time.sleep(5)
                    self.__logger.debug(f"Retry Login (a) ...")
                    return self.__re_login(retry_counter=retry_counter + 1, max_retry=max_retry)

        except Exception as e:
            self.__logger.error(f"交易主機連線錯誤 msg: {e}")
            self.__is_alive = False
            return False



if __name__ == '__main__':

    fubon_ws = FubonWS()
    fubon_ws.ws_connect()
    while True:
        time.sleep(1)
