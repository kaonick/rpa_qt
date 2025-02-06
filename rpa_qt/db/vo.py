from sqlmodel import Field, Session, SQLModel, create_engine, select, Column, PrimaryKeyConstraint, UniqueConstraint
from typing import Optional, ClassVar

from rpa_qt.utils.config_yaml_loader import settings
from pydantic.fields import PrivateAttr

"""
要爬的網站定義：
"""
class Browser(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
        UniqueConstraint("site_id", name="unique_constraint_site_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    site_id: str = Field(default=None, nullable=False)  # 網站代號：原則上是網址中間名稱，例如：www.amazon.com，site_id:amazon
    site_name: str = Field(default=None, nullable=False)  # 網站簡稱：例如：ALI, TI
    site_logo: str = Field(default=None, nullable=True)  # 網站logo
    site_url: str = Field(default=None, nullable=True)  # 網站首頁
    site_crawl_url: str = Field(default=None, nullable=True)  # 爬蟲網址
    driver_type: str = Field(default=None, nullable=True)  # driver類型，預設:grid_driver, remote_driver,local_driver
    browser_name: str = Field(default=None, nullable=False)  # 瀏覽器名稱，預設:chrome
    browser_remote_port: str = Field(default=None, nullable=True)  # browser_romote_port：9527~
    country_code: str = Field(default=None, nullable=True)  # 國家代碼:TW, CN
    pid: int = Field(default=-1, nullable=False)  # 供檢查是否alive用。
    available: bool = Field(default=True, nullable=False)  # 有效的。
    itm: str = Field(default=None, nullable=True)  # 項次，排序用，例如:001,002,003
    # 可能還需要網站的登入帳號與密碼之類的資訊

    # 私有變數
    _worker_id: str = PrivateAttr(default=None)

    @property
    def get_worker_id(self):
        return self._worker_id

    def set_worker_id(self, worker_id):
        self._worker_id = worker_id

"""
針對remote_driver記錄不同的worker、site的pid
"""
class WorkerBrowser(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
        UniqueConstraint("worker_id","site_id" ,name="unique_constraint_case_id_site_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    worker_id: str = Field(default=None, nullable=False)
    site_id: str = Field(default=None, nullable=False)  # 網站代號：原則上是網址中間名稱，例如：www.amazon.com，site_id:amazon
    driver_type: str = Field(default=None, nullable=True)  # driver類型，預設:grid_driver, remote_driver,local_driver
    browser_remote_port: str = Field(default=None, nullable=True)  # browser_romote_port：9527~
    pid: int = Field(default=-1, nullable=False)  # 供檢查是否alive用。


def browser_to_worker(browser: Browser):
    return WorkerBrowser(worker_id=browser.get_worker_id, site_id=browser.site_id, driver_type=browser.driver_type, browser_remote_port=browser.browser_remote_port, pid=browser.pid)


"""
材料類別對應爬取的網站：
"""
class PartTypeCrawlwerSite(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    part_type: str = Field(default=None, nullable=False)  # 材料類別
    site_name: str = Field(default=None, nullable=True)  # 網站簡稱

"""
爬取案件
"""
class SearchCase(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
        UniqueConstraint("case_id", name="unique_constraint_case_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: str = Field(default=None, nullable=False)  # 搜尋案號(系統)
    question: str = Field(default=None, nullable=False)  # 搜尋內容
    user: str = Field(default=None, nullable=True)  # 使用者(記錄使用者資訊，通常是email)
    vhno: str = Field(default=None, nullable=True)  # 來源單號：請購單
    item: str = Field(default=None, nullable=True)  # 來源項次：請購單
    part_no: str = Field(default=None, nullable=True)  # 料號
    brand: str = Field(default=None, nullable=True)  # 廠牌
    model: str = Field(default=None, nullable=True)  # 型號
    txtm: str = Field(default=None, nullable=True)  # 異動時間:建立時間
    oktm: str = Field(default=None, nullable=True)  # 處理完成時間
    worker: str = Field(default=None, nullable=True)  # 分配的爬蟲worker

"""
爬取結果
"""
class SearchSource(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
        UniqueConstraint("case_id","site_id" ,name="unique_constraint_case_id_site_id"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: str = Field(default=None, nullable=False)  # 搜尋案號(系統)
    site_id: str = Field(default=None, nullable=False)  # 搜尋網站簡稱
    search_url: str = Field(default=None, nullable=True)  # 搜尋的網址
    result_picture: str = Field(default=None, nullable=True)  # 網站snapshot照片檔名
    result_rows: int = Field(default=0, nullable=False)  # 筆數
    txtm: str = Field(default=None, nullable=True)  # 異動時間(爬取時間)

class SearchResult(SQLModel, table=True):
    __table_args__ = (
        PrimaryKeyConstraint('id'),
        UniqueConstraint("case_id","site_id", "item", name="unique_constraint_case_id_site_id_item"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: str = Field(default=None, nullable=False)  # 搜尋案號(系統)
    site_id: str = Field(default=None, nullable=False)  # 搜尋網站簡稱
    # 搜尋的品項
    item: str = Field(default=None, nullable=False)  # 項次
    title: str = Field(default=None, nullable=True)  # 品名
    description: str = Field(default=None, nullable=True)  # 說明(其它細節，用md,或json存放)
    unit: str = Field(default=None, nullable=True)  # 單位
    price: str = Field(default=None, nullable=True)  # 價格
    currency: str = Field(default=None, nullable=True)  # 幣別
    exchange_rate: str = Field(default=None, nullable=True)  # 匯率
    item_href: str = Field(default=None, nullable=True)  # 品項超連結(原網站)
    item_image_href: str = Field(default=None, nullable=True)  # 照片超連結(原網站)
    item_image: str = Field(default=None, nullable=True)  # 照片檔名
    txtm: str = Field(default=None, nullable=True)  # 異動時間(爬取時間)




def db_init():
    # db_url = 'mysql+mysqlconnector://root:ps123@localhost:3306/my_da'
    db_url = settings.db_url
    engine = create_engine(db_url, echo=True)
    # SQLModel.metadata.create_all(engine)
    # Browser.__table__.create(engine)
    # SearchCase.__table__.create(engine)
    # SearchSource.__table__.create(engine)
    # SearchResult.__table__.create(engine)
    WorkerBrowser.__table__.create(engine)
    # PartTypeCrawlwerSite.__table__.create(engine)

if __name__ == '__main__':
    db_init()
