"""

參考指令：

search_input = self.browser.find_element(By.XPATH, "//input[@data-di-id='di-id-73261104-430e022a']")
self.browser.execute_script('arguments[0].setAttribute("text","{}");'.format(question), search_input)

"""

import time

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.remote.command import Command

def check_dirver_status(driver):
    try:
        driver.execute(Command.GET_TITLE)
        return True
    except Exception as e:
        return False


def create_browser_driver():
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--headless=old")
        # chrome_options.binary_location = "d:/dev_env/chromedriver/123/chromedriver.exe"
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.maximize_window()
        # browser = webdriver.Chrome(options=chrome_options) #        "d:/dev_env/chromedriver-win64/chromedriver.exe" chrome_options=chrome_options
        return driver
    except Exception as err:
        print("Error ...")
        print(err)
        # sys.exit(1);
        if driver:
            driver.close()
            driver.quit()
            browser = None

# 載入網頁，並且等待id元素出現
def with_until_page_load(driver,url:str,id:str):
    driver.get(url)
    delay = 3  # seconds
    try:
        myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, id)))
        print("Page is ready!")
        return True
    except TimeoutException:
        print("Loading took too much time!")
        return False

def expand_root_element(driver,element):
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
    return shadow_root


def save_screen_shot(driver, file_name):
    driver.save_screenshot(file_name)

def scroll_to(driver,y:int):
    driver.execute_script(f"window.scrollTo(0, {y});")  # Scroll by y

def scroll_to_bottom(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

def scroll_to_bottom_stepbystep(driver):
    # Get the initial scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    step=500
    all_scroll=0
    # Scroll step by step
    while True:
        # Scroll down by a fixed amount
        driver.execute_script(f"window.scrollBy(0, {step});")  # Scroll by 500 pixels
        time.sleep(1.5)  # Wait for content to load (adjust time as needed)

        # Check the new scroll height
        # new_height = driver.execute_script("return document.body.scrollHeight")
        all_scroll=all_scroll+step
        # Break if we have reached the bottom
        if all_scroll >= last_height:
            break

    print("Reached the bottom of the page.")

    return


if __name__ == '__main__':
    driver=None
    try:
        driver=create_browser_driver()
        url="https://www.ti.com/sitesearch/en-us/docs/universalsearch.tsp?langPref=en-US&nr=462&searchTerm=SK-AM62B-P1#q=SK-AM62B-P1"
        id="db-sync"
        result=with_until_page_load(driver,url,id)
        print(result)

        if result:
            path="d:/temp3/ti.png"
            save_screen_shot(driver,path)

            # time.sleep(10)
            # print(driver.page_source)




            # pass
            tag_with_shadow_root =driver.find_element(By.TAG_NAME, "ti-tool-snapshot")
            a01_ShadowRoot = expand_root_element(driver,tag_with_shadow_root)
            print(a01_ShadowRoot.session.page_source)

            # testing
            a02 = a01_ShadowRoot.find_elements(By.CSS_SELECTOR, "ti-card")

            for a02_element in a02:
                # 取得shadowRoot
                #a02_ShadowRoot = driver.execute_script('return arguments[0].shadowRoot', a02_element)

                span_list=a02_element.find_elements(By.CSS_SELECTOR, "span")
                for span in span_list:
                    print(span.text)




            a02 = a01_ShadowRoot.session.find_element(By.TAG_NAME, "ti-card")

            ele = driver.execute_script(
                "return arguments[0].getElementsByTagName('ti-card')",a01_ShadowRoot)
            print(ele.text)


            a02 = a01_ShadowRoot.find_element(By.CLASS_NAME, 'ti-card-plain-white hydrated')



            a02_ShadowRoot = expand_root_element(driver, a02)

            #price = a02_ShadowRoot.find_element(By.XPATH, "//span[@class='ti-tool-snapshot-price']")

            # price=browser.find_element(By.XPATH, "//span[@class='ti-tool-snapshot-price']")



            price_element=driver.find_element(By.CLASS_NAME, "ti-tool-snapshot-price")
            # price_element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ti-tool-snapshot-price")))
            print(price_element.text)
    except Exception as err:
        print("Error ...")
        print(err)
        # sys.exit(1);
        if driver:
            driver.close()
            driver.quit()
            driver = None
    finally:
        if driver:
            driver.close()
            driver.quit()
            driver = None