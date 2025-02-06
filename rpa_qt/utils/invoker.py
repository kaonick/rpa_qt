"""
Date: 2024/8/23
    create vo by init data
version: 0.0.1
by Nick Kao
"""
import importlib
import logging
import sys
from typing import Any

module_cache = {}  # 模組快取，避免重複import。因為載入很慢。


def import_module(module_name: str):
    if module_name not in module_cache:
        try:
            module_cache[module_name] = importlib.import_module(module_name)
        except Exception as e:
            logging.error(f"import_module error: {e}")
    return module_cache[module_name]


def import_class(module_name: str, class_name: str) -> Any:
    module = import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


def load_class(module_name: str, class_name: str, init_data=None) -> Any:
    # module = importlib.import_module(module_name)
    # class_ = getattr(module, class_name)

    class_ = import_class(module_name, class_name)

    if init_data:
        instance = class_(**init_data)
    else:
        instance = class_()
    return instance


if __name__ == '__main__':
    module_name = "llmz.plugins.task_da_sql2.ddl_db"
    class_name = "Domain"

    class_ = import_class(module_name, class_name)
    print(class_)
    class_ = import_class(module_name, class_name)
    print(class_)

    # class_name = "Form"
    # init_data = {"form_id": "form_id", "block_id": "block_id", "itm": "f",
    #        "column_name": "column_name", "label_name": "column_name", "data_name": "column_name"}
    # class_name = "Columns"
    #
    # obj=load_class(module_name,class_name,init_data)
    # print(obj)
