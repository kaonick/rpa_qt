from fastapi import HTTPException, APIRouter

from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter(
    prefix="",
    tags=["Products"]
)



class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    stock: int
    description: Optional[str] = None

# 模擬資料庫
products_db: Dict[int, Product] = {
    1: Product(id=1, name="筆記型電腦", price=1200.50, stock=50, description="功能強大的筆記型電腦"),
    2: Product(id=2, name="滑鼠", price=25.00, stock=200, description="無線光學滑鼠"),
    3: Product(id=3, name="鍵盤", price=75.20, stock=150, description="機械式鍵盤"),
    4: Product(id=4, name="顯示器", price=300.00, stock=80, description="27吋4K顯示器"),
    5: Product(id=5, name="耳機", price=150.75, stock=120, description="降噪耳機"),
    6: Product(id=6, name="智慧型手機", price=800.00, stock=60, description="最新款智慧型手機"),
    7: Product(id=7, name="平板電腦", price=400.00, stock=70, description="輕薄平板電腦"),
    8: Product(id=8, name="外接硬碟", price=100.00, stock=90, description="1TB外接硬碟"),
    9: Product(id=9, name="路由器", price=60.00, stock=110, description="高速無線路由器"),
    10: Product(id=10, name="USB隨身碟", price=20.00, stock=300, description="64GB USB隨身碟"),
    11: Product(id=11, name="攝影機", price=250.00, stock=40, description="高清攝影機"),
    12: Product(id=12, name="印表機", price=150.00, stock=30, description="多功能印表機"),
    13: Product(id=13, name="掃描器", price=120.00, stock=25, description="高解析掃描器"),
    14: Product(id=14, name="投影機", price=500.00, stock=15, description="便攜式投影機"),
    15: Product(id=15, name="智慧手錶", price=200.00, stock=85, description="健康監測智慧手錶"),
    16: Product(id=16, name="遊戲主機", price=400.00, stock=20, description="最新款遊戲主機"),
    17: Product(id=17, name="電競椅", price=180.00, stock=45, description="人體工學電競椅"),
    18: Product(id=18, name="電腦桌", price=220.00, stock=35, description="可調高度電腦桌"),
    19: Product(id=19, name="滑鼠墊", price=15.00, stock=250, description="大型滑鼠墊"),
    20: Product(id=20, name="網路攝影機", price=80.00, stock=55, description="高清網路攝影機"),

}

# 取得下一個可用的 ID
def get_next_id():
    return max(products_db.keys(), default=0) + 1

@router.get("/api/products", response_model=List[Product])
def get_products(search: Optional[str] = None):
    """查詢所有產品或根據名稱搜尋"""
    if search:
        return [p for p in products_db.values() if search.lower() in p.name.lower()]
    return list(products_db.values())

@router.get("/api/lov", response_model=List[Product])
def get_lov(search: Optional[str] = None,page: Optional[int] = None,sort_by: Optional[str] = None,sort_dir: Optional[str] = None):
    """查詢所有產品或根據名稱搜尋"""
    result=None
    if search:
        result= [p for p in products_db.values() if search.lower() in p.name.lower()]
    else:
        result=list(products_db.values())

    if sort_by:
        reverse = sort_dir == "desc"
        result = sorted(result if result is not None else products_db.values(), key=lambda x: getattr(x, sort_by), reverse=reverse)
    if page is not None and page > 0:
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size
        result = (result if result is not None else list(products_db.values()))[start:end]
    if result is not None:
        return result


    return list(products_db.values())


@router.post("/api/products", response_model=Product, status_code=201)
def create_product(product: Product):
    """新增一個產品"""
    new_id = get_next_id()
    product.id = new_id
    products_db[new_id] = product
    return product

@router.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """根據 ID 取得單一產品"""
    product = products_db.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/api/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: Product):
    """更新一個產品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    product.id = product_id
    products_db[product_id] = product
    return product

@router.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    """刪除一個產品"""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted successfully"}