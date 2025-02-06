"""
https://www.finlab.tw/%e8%b6%85%e7%b0%a1%e5%96%ae-machine-learning-%e9%a0%90%e6%b8%ac%e8%82%a1%e5%83%b9/
https://www.finlab.tw/pandas-%e9%ad%94%e6%b3%95%e7%ad%86%e8%a8%981-%e5%b8%b8%e7%94%a8%e6%8b%9b%e5%bc%8f%e7%b8%bd%e8%a6%bd/
https://www.finlab.tw/qlib-intro/

"""

import requests
from io import StringIO
import pandas as pd
import numpy as np

datestr = '20180131'

# 下載股價
r = requests.post('https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=ALL')

# 整理資料，變成表格
df = pd.read_csv(StringIO(r.text.replace("=", "")),
            header=["證券代號" in l for l in r.text.split("\n")].index(True)-1)

# 整理一些字串：
df = df.apply(lambda s: pd.to_numeric(s.astype(str).str.replace(",", "").replace("+", "1").replace("-", "-1"), errors='coerce'))

# 顯示出來
df.head()