
"""
生成DAO用：自動生成新的DAO檔案，並替換內容。
input:
    ref_dao=user_dao
    new_dao_name=abc
    table_class=Abc
    table_name=abc
then:
    copy user_dao.py to abc_dao.py
    then in abc_dao.py, replace Abc to Abc, abc to abc

"""

import shutil
import os

# ==== 輸入參數 ====
# 注意輸入小寫
ref="user"
new="stockRecord"
# ==================
# capitalized first letter
aref=ref.capitalize()
anew=new[0].upper()+new[1:] if len(new)>1 else new.upper()
# anew=new.capitalize()


ref_dao = f"dao_{ref}.py"
new_dao_name = f"dao_{new}.py"
old_class = aref   # user_dao.py 裡的 table class
new_class = anew   # 新的 table class
old_table = ref   # user_dao.py 裡的 table 名稱
new_table = new    # 新的 table 名稱
# ==================

# 1. 複製檔案
shutil.copy(ref_dao, new_dao_name)

# 2. 替換內容
with open(new_dao_name, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(old_class, new_class)
content = content.replace(old_table, new_table)

with open(new_dao_name, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 已產生 {new_dao_name}")
