"""

"""
import logging
from abc import abstractmethod
from selenium import webdriver
from selenium.webdriver.remote.client_config import ClientConfig
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from rpa_qt.db.vo import Browser, SearchCase
from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.selenium_utils import check_dirver_status


class TaskBase:

    def __init__(self, browser: Browser):
        # start chrome browser
        # source_project_path = "D:/00WS-TMP/PYTHON/rpa-ap/src/rpa_qt"
        # run_chrome3(source_project_path=source_project_path)
        # time.sleep(5)
        self.browser = browser
        self.driver = None
        self.create_driver()

    @abstractmethod
    def check_alive(self):
        pass

    def create_driver_remote(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")

            # chrome_options.add_argument("window-size=1920,1080")
            # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

            # chrome_options.add_argument('headless') # 无头模式
            # chrome_options.add_argument("--log-level=3")  # 0: INFO, 1: WARNING, 2: ERROR, 3: FATAL

            # chrome_options.add_argument("--headless")
            # chrome_options.add_argument("--test-type")
            # chrome_options.add_argument("--disable-gpu")
            # chrome_options.add_argument("--no-first-run")
            # chrome_options.add_argument("--no-default-browser-check")
            # chrome_options.add_argument("--ignore-certificate-errors")
            # chrome_options.add_argument("--start-maximized")

            # 【透過proxy chrome 顯示】
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.browser.browser_remote_port}")

            # import chromedriver_autoinstaller
            # chromedriver_autoinstaller.install()

            # chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            chrome_options.binary_location = settings.chrome_path
            # self.driver = webdriver.Chrome(options=chrome_options)
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # 測試作法: 測試指定driver_path，但是似乎沒有作用
            # driver_path = Service(
            #     r'C:\Program Files\Google\Chrome\Application\chrome.exe')  # add your own path
            # self.driver = webdriver.Chrome(service=driver_path, options=chrome_options)

            # 防bot偵測用
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logging.info(f"create remote driver success ...{self.browser.browser_remote_port}")
        except Exception as err:
            logging.error("Error ...")
            print("Error ...")
            print(err)
            logging.error(f"Error ...{err}")
            # sys.exit(1);
            if self.driver:
                self.driver.close()
                self.driver.quit()
                self.driver = None

    def create_driver_local(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")

            # 【獨立執行】
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            # 防bot偵測用
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as err:
            print("Error ...")
            print(err)
            # sys.exit(1);
            if self.driver:
                self.driver.close()
                self.driver.quit()
                self.driver = None

    def create_driver_grid(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            # chrome_options.add_argument("--start-maximized")
            # 重要<以下兩項都要>防止：DevToolsActivePort file doesn't exist
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("--no-sandbox");  # Bypass OS security model
            # chrome_options.add_argument('--profile-directory=Default')
            # chrome_options.add_argument("--user-data-dir=/tmp/chrome_profiles") # 加了會無法開啟
            # chrome_options.add_argument("--user-data-dir=/tmp/user_profiles")  # 使用本地profiles，但是會造成無法產生driver
            # chrome_options.add_argument("--profile-directory=Person 1")

            user = settings.se_grid_user
            key = settings.se_grid_key
            driver_url = settings.se_grid_url
            client_config = ClientConfig(remote_server_addr=driver_url, username=user, password=key)

            self.driver = webdriver.Remote(
                command_executor=driver_url,
                options=chrome_options,
                client_config=client_config
            )
            print(f"driver_name={self.driver.name},title={self.driver.title},session_id={self.driver.session_id}")

            # self.driver = webdriver.Remote(
            #     command_executor="http://127.0.0.1:4444/wd/hub",
            #     options=chrome_options
            # )
            # https://USERNAME:ACCESS_KEY@HUB_SUBDOMAIN.gridlastic.com/wd/hub

            # 防bot偵測用
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as err:
            print("Error ...")
            print(err)
            # sys.exit(1);
            if self.driver:
                self.driver.close()
                self.driver.quit()
                self.driver = None

    def create_driver(self):
        try:

            # 防bot偵測用
            # user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            # chrome_options.add_argument('user-agent={0}'.format(user_agent))

            # # 防bot偵測用 adding argument to disable the AutomationControlled flag
            # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            #
            # # 防bot偵測用 exclude the collection of enable-automation switches
            # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            #
            # # 防bot偵測用 turn-off userAutomationExtension
            # chrome_options.add_experimental_option("useAutomationExtension", False)

            # chrome_options.add_argument("--headless=old")
            # chrome_options.binary_location = "d:/dev_env/chromedriver/123/chromedriver.exe"

            # 以下三擇一
            if self.browser.driver_type == "grid_driver":
                self.create_driver_grid()
            elif self.browser.driver_type == "remote_driver":
                self.create_driver_remote()
            else:
                self.create_driver_local()

        except Exception as err:
            print("Error ...")
            print(err)
            logging.error(f"Error ...{err}")
            # sys.exit(1);
            if self.driver:
                self.driver.close()
                self.driver.quit()
                self.driver = None

    def open_page(self, url):
        try:
            if self.driver is None:
                self.create_driver()

            # 防止driver開太久，timeout
            if check_dirver_status(self.driver) is False:
                self.create_driver()

            self.driver.get(url)
            logging.info(f"open_page success ...{url}")

            # 開新分頁(一)
            # self.driver.execute_script(f'''window.open("{url}","_blank");''')
            # 開新分頁(二)
            # # Open a new window
            # self.driver.execute_script("window.open('');")
            # # Switch to the new window
            # self.driver.switch_to.window(self.driver.window_handles[1])
            # self.driver.get(url)
        except Exception as err:
            print("Error ...")
            print(err)
            logging.error(f"Error ...{err}")
            # sys.exit(1);

    def get_data(self):
        pass

    @abstractmethod
    def run(self, search_case: SearchCase):
        pass

    def close(self):
        if self.driver:
            self.driver.close()
            self.driver.quit()
            self.driver = None
            logging.info(f"close driver success ...")
