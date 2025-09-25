from rpa_qt.backend.model.models import StockRecord, get_now_day
from rpa_qt.utils.time_utils import get_now_code


class SourceObject1:
    def __init__(self, name, age):
        self.name = name
        self.age = age


class SourceObject2:
    def __init__(self, country, city):
        self.country = country
        self.city = city


class TargetObject:
    def __init__(self, name=None, age=None, location=None):
        self.name = name
        self.age = age
        self.location = location


def auto_map(target_obj, **source_objs):
    """
    自動將來源物件的資料配對並填入目標物件中。

    Args:
        target_obj: 目标物件。
        **source_objs: 多個來源物件，以關鍵字參數形式傳入。

    Returns:
        已填入資料的目標物件。
    """
    # 遍歷所有來源物件
    for source_name, source_obj in source_objs.items():
        print(type(source_obj))
        print(source_obj.get_all_attributes())
        # Combine instance and class variables, prioritizing instance variables in case of a name clash
        source_class = type(source_obj)
        all_variables = {**source_class.__dict__, **source_obj.__dict__}

        # Filter out methods and dunder attributes for a cleaner output
        filtered_vars = {
            key: value for key, value in all_variables.items()
            if not key.startswith('__') and not callable(value)
        }



        # 遍歷來源物件的屬性
        for key, value in source_obj.__dict__.items():
            # 檢查目標物件是否包含該屬性
            if hasattr(target_obj, key):
                # 如果屬性存在且值不為None，則進行賦值
                setattr(target_obj, key, value)
            else:
                # 這裡可以根據需要添加更複雜的配對邏輯，例如：
                # 根據關鍵詞或相似度進行模糊配對。
                # 範例：如果來源物件有 'city' 和 'country'，而目標物件有 'location'
                # 則可以嘗試將 'city' 和 'country' 組合成 'location' 的值
                # (但這個範例為了簡潔，只做精確名稱比對)
                pass

    return target_obj


def to_stock_record(inv, unrealized):
    vo = StockRecord()

    vo.order_code=get_now_code()
    vo.symbol=inv.stock_no
    vo.name=
    vo.quantity=unrealized.today_qty
    vo.init_buy_date=inv.date
    vo.avg_cost_price=unrealized.cost_price
    vo.current_price=
    vo.highest_price=
    vo.profit_rate=
    vo.stop_loss_rate=0.05  # 停損標準，float，不可空白
    vo.take_profit_rate=0.03  # 停利標準，float，不可空白
    vo.stop_loss_price=  # 停損價格，float，不可空白
    vo.take_profit_begin_price =  # 停利起算價格，float，不可空白
    vo.take_profit_price=  # 停利價格，float，不可空白
    vo.fallback_rate=  # 回跌率，float，不可空白

    # if current_price is higher than take_profit_begin_price, then set current_status="take_profit_stage" otherwise "stop_loss_stage"
    vo.current_status=("take_profit_stage" if vo.current_price > vo.take_profit_begin_price else "stop_loss_stage") # 目前狀態：停損階段或停利階段，不可空白
    vo.trade_history="" # 交易記錄，可空白

    # if current_price is lower than stop_loss_price then set strategy="stop_loss"
    # if current_price is higher than take_profit_begin_price and lower than  take_profit_price then set strategy="take_profit"
    # if profit_rate is higher than 10% then set strategy="first_add"
    # if profit_rate is higher than 20% then set strategy="second_add"
    # if holding days is more than 60 days(from init_buy_date till now) and current_price lower than take_profit_begin_price then set strategy="timeout_sell"
    # otherwise "observe"
    vo.strategy = (
        "stop_loss" if vo.current_price < vo.stop_loss_price else
        "take_profit" if vo.current_price > vo.take_profit_begin_price and vo.current_price < vo.take_profit_price else
        "second_add" if vo.profit_rate > 0.2 else
        "first_add" if vo.profit_rate > 0.1 else
        "timeout_sell" if (int(get_now_day()) - int(vo.init_buy_date)) > 60 and vo.current_price < vo.take_profit_begin_price else
        "observe"
    )
    # 應採策略：觀望、停利、停損、第一次加碼、第二次加碼、逾時賣出，可空白

    vo.settlement_date=  # 結算日期，yyyymmdd，可空白
    vo.total_cost=  # 成本總額，float，不可空白
    vo.profit_amount=  # 損益金額，float，可空白
    vo.final_profit_rate=  # 損益率，float，可空白
    vo.review= # 結算檢討，string(500)，可空白

    vo.data_time=get_now_code()  # 異動時間，預設 get_now_code()，不可空白



    record.symbol = inv.stock_no
    record.name =
    record.quantity = unrealized.today_qty
    record.init_buy_date = inv.buy_date

    # 其他屬性根據需要進行映射
    record.avg_cost_price=unrealized.cost_price

    UnrealizedData
    {
        date: "2025/09/23",
        branch_no: "20706",
        account: "825678",
        stock_no: "0050",
        buy_sell: Buy,
        order_type: Stock,
        cost_price: 37.685,
        tradable_qty: 18844,
        today_qty: 18844,
        unrealized_profit: 388626,
        unrealized_loss: 0,
    }

    return record

if __name__ == '__main__':

    # 範例使用
    source1 = SourceObject1(name="John Doe", age=30)
    source2 = SourceObject2(country="USA", city="New York")
    target = TargetObject()

    # 執行自動配對
    mapped_target = auto_map(target_obj=target, source1=source1, source2=source2)

    # 顯示結果
    print(f"Name: {mapped_target.name}")
    print(f"Age: {mapped_target.age}")
    print(f"Location: {mapped_target.location}")