"""
需要將question，轉換特殊符號，例如：SK-AM62B-P1 -> SK%2525252dAM62B%2525252dP1
"""
import logging
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from rpa_qt.base.task_base import TaskBase
from rpa_qt.db.vo import Browser, SearchCase

from rpa_qt.tmp_fins.column_dict import balance_sheet_dict, read_download_csv
from rpa_qt.tmp_fins.util_file import get_csv_files, delete_today_csv
from rpa_qt.utils import logger
from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.data.vo_parser import load_data
from rpa_qt.utils.logger import configure_log
from rpa_qt.utils.project_utils import get_case_code
from rpa_qt.utils.time_utils import get_now_code
from rpa_qt.utils.selenium_utils import save_screen_shot, scroll_to_bottom, scroll_to_bottom_stepbystep


class TaskGetData(TaskBase):

    def __init__(self, browser: Browser):
        super().__init__(browser=browser)

    def check_alive(self):
        return True

    def run(self, search_case: SearchCase):
        txtm = get_now_code()
        case_id = search_case.case_id
        site_id = self.browser.site_id
        search_url = self.browser.site_crawl_url
        result_picture_path = f"{case_id}_{site_id}.png"

        try:
            url = self.browser.site_crawl_url

            self.open_page(url)
            time.sleep(5)  # 重要：必要等待，否則print price不會執行。

            # scroll_to_bottom(self.driver)
            # time.sleep(2)
            # scroll_to_bottom_stepbystep(self.driver)

            if self.driver is None:
                raise Exception("browser can't open ...")
            logging.info(f"browser is opened ...")

            # find input id=year
            year_input = self.driver.find_element(By.ID, "year")
            year_input.send_keys("110")

            # find select id=season
            season_select = self.driver.find_element(By.ID, "season")
            season_select.send_keys("1")

            # 因為會有多個，所以需要逐一確認：
            # find button id=search
            search_divs = self.driver.find_elements(By.ID, "search_bar1")


            for search_div in search_divs:
                # find input type = "text" from search_div
                try:
                    search_button = search_div.find_element(By.CSS_SELECTOR, "input[type='button']")
                    search_button.click()
                    time.sleep(5)
                    break
                except Exception as err:
                    print("Error ...")


            # find all elements tag name "button" with style background-color:transparent;border:0;cursor:pointer;text-decoration:underline;
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[style='background-color:transparent;border:0;cursor:pointer;text-decoration:underline;']")
            for button in buttons:
                button.click()
                time.sleep(1)

            # read_download_csv()


            logging.info(f"save search source success ...")

            # time.sleep(3)
        except Exception as err:
            print("Error ...")
            print(err)
            # sys.exit(1);



if __name__ == '__main__':
    #
    import os

    os.environ['WDM_LOG'] = '0'

    configure_log()
    download_path = "C:/Users/n000000930/Downloads"
    delete_today_csv(download_path)

    income_statement_url = "https://mops.twse.com.tw/mops/web/t163sb04" # 損益表
    balance_sheet_url="https://mops.twse.com.tw/mops/web/t163sb05" # 資產負債表
    income_url="https://mops.twse.com.tw/mops/web/t163sb06" # 營益分析查詢彙總表
    cash_flow_url="https://mops.twse.com.tw/mops/web/t163sb20"

    browser = Browser(driver_type="local_driver",site_crawl_url=cash_flow_url)

    crawler = TaskGetData(browser=browser)

    case_id = get_case_code()
    question = "冰箱"  # 空氣清淨機
    search_case = SearchCase(case_id=case_id, question=question, user="anonymous", txtm=get_now_code(),
                             oktm=get_now_code())  # 注意：測試時oktm要填值

    crawler.run(search_case=search_case)

    # 第二案
    # case_id=get_case_code()
    # question = "藍海策略"  # 空氣清淨機
    # search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())
    # dbpipe_SearchCase.put(search_case)
    # crawler.run(search_case=search_case)

    # crawler.close()
