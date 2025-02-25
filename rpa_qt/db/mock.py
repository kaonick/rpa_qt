from rpa_qt.db.vo import Browser
from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.data.vo_crud import VoCRUD
from rpa_qt.utils.data.vo_parser import load_xls, df_to_sqlmodel
from rpa_qt.utils.project_utils import save_image, url2file_name, crawl_logo


def mock_browsers_tmp():
    browsers = []

    # create 10 browsers
    for i in range(10):
        port = f"952{i + 1}"
        browser = Browser(site_name=f"site_{i+1}",browser_name=f"chrome_{port}", web_url="https://www.google.com", browser_remote_port=f"{port}")
        browsers.append(browser)

    db_exe = VoCRUD(db_url=settings.db_url)
    db_exe.insert(data=browsers)

    return browsers

def mock_insert_browsers():
    file_path="D:/00近期工作/2024/20241026(專案)資材管理組_市場價格搜尋系統/網站驗證記錄.xlsx"
    df=load_xls(file_path,"browser")
    data=df_to_sqlmodel(df, "rpa_qt.db.vo", "Browser")
    db_exe = VoCRUD(db_url=settings.db_url)
    db_exe.insert(data=data)


def mock_supplier_logo_crawler():
    file_path="D:/00近期工作/2024/20241026(專案)資材管理組_市場價格搜尋系統/網站驗證記錄.xlsx"
    df=load_xls(file_path,"browser")
    data=df_to_sqlmodel(df, "rpa_qt.db.vo", "Browser")

    for item in data:
        print(f"site_name={item.site_name},site_url={item.site_url}")
        # https: // logo.clearbit.com / www.stackoverflow.com
        url=f"https://logo.clearbit.com/{item.site_url}"
        file_name=item.site_logo
        result=save_image(url=url, path=f"d:/temp3/rpa_qt/supplier_logo/{file_name}.png")
        if not result:
            logo_urls=crawl_logo(item.site_url)
            if len(logo_urls)>0:
                url=logo_urls[0]
                save_image(url=url, path=f"d:/temp3/rpa_qt/supplier_logo/{file_name}.png")
            else:
                print(f"Error:crawl_logo not found")

# 生成logo檔案用
def mock_browser_read():
    file_path="D:/00近期工作/2024/20241026(專案)資材管理組_市場價格搜尋系統/網站驗證記錄.xlsx"
    df=load_xls(file_path,"browser")
    data=df_to_sqlmodel(df, "rpa_qt.db.vo", "Browser")

    for item in data:
        file_name = url2file_name(item.site_url)
        print(file_name)


def mock_chart_of_accounting():
    file_path = "C:/Users/Nick/Downloads/簡易會計科目表.xlsx"
    df = load_xls(file_path,sheet_name="工作表1")
    print(df.head())

if __name__ == '__main__':
    # mock_insert_browsers()
    # mock_supplier_logo_crawler()
    # mock_browser_read()
    mock_chart_of_accounting()

