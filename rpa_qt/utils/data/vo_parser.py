"""
Date: 2024/8/23
version: 0.0.1
by Nick Kao

幫我生成各方法的使用說明：
1. load_data
2. sqmodel_to_df_not_order
3. sqlmodel_to_df
4. df_to_sqlmodel
5. get_datatype
6. df_gen_sqlmodel
7. sqlmodel_to_db
8. handle_nas

異常排除：
1. nan補值
2. 資料型態不符：int>bigint,varchar>text：遇到時，要手動修改資料庫，這部份生成vo時，無法依資料大小自動生成

"""

from typing import List

import pandas as pd

# from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, create_engine, select

from rpa_qt.utils.invoker import import_class, load_class


def load_data(path: str):
    # return pd.read_csv(path,encoding='unicode_escape')
    return pd.read_csv(path,encoding='cp950' ,encoding_errors = "strict",) #big5, cp950, big5hkscs

def load_xls(file_path: str,sheet_name:str):
    xls = pd.ExcelFile(file_path)
    # xls.sheet_names  # see all sheet names
    df=xls.parse(sheet_name)
    return df




def sqmodel_to_df_not_order(objs: List[SQLModel]) -> pd.DataFrame:
    """Convert a SQLModel objects into a pandas DataFrame."""
    records = [i.dict() for i in objs]
    df = pd.DataFrame.from_records(records)
    return df


# better
def sqlmodel_to_df(objects: List[SQLModel], set_index: bool = False) -> pd.DataFrame:
    """Converts SQLModel objects into a Pandas DataFrame.
    Usage
    ----------
    df = sqlmodel_to_df(list_of_sqlmodels)
    Parameters
    ----------
    :param objects: List[SQLModel]: List of SQLModel objects to be converted.
    :param set_index: bool: Sets the first column, usually the primary key, to dataframe index."""

    records = [obj.dict() for obj in objects]
    columns = list(objects[0].schema()["properties"].keys())
    df = pd.DataFrame.from_records(records, columns=columns)
    return df.set_index(columns[0]) if set_index else df


def df_to_sqlmodel(df: pd.DataFrame, module_path, class_name) -> List[SQLModel]:
    """Convert a pandas DataFrame into a a list of SQLModel objects."""
    df = handle_nas(df) # 防止nan
    objs = [load_class(module_path, class_name, row) for row in df.to_dict('records')]
    return objs


def get_datatype(df_datatype):
    match df_datatype:
        case "int64":
            return "int"
        case "float64":
            return "float"
        case "object":
            return "str"
        case "bool":
            return "bool"
        case _:
            return "str"


def df_gen_sqlmodel(df: pd.DataFrame, class_name) -> str:
    """Convert a pandas DataFrame into a a list of SQLModel objects."""

    s = f"class {class_name}(SQLModel, table=True):"
    # 加入pk，預設第一欄為pk，
    s = s + "\n\t__table_args__ = ("
    s = s + f"\n\t\tPrimaryKeyConstraint('{df.columns[0]}'),"
    s = s + "\n\t)"

    for c in df.columns:
        data_type = df[c].dtype
        print(c)
        print(data_type)
        # refs: Optional[str] = Field(default=None)
        s = s + "\n\t" + c + ": Optional[" + get_datatype(data_type) + "] = Field(default=None)"

    return s


def sqlmodel_add_to_db(objects: List[SQLModel], engine):
    """Converts SQLModel objects into a Pandas DataFrame and stores it in a database.
    Usage
    ----------
    sqlmodel_to_db(list_of_sqlmodels, "sqlite:///example.db")
    Parameters
    ----------
    :param objects: List[SQLModel]: List of SQLModel objects to be converted.
    :param db_url: str: URL to the database where the DataFrame will be stored."""
    # engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        c = 0
        for obj in objects:
            try:
                session.add(obj)
                c += 1
            except Exception as e:
                print(e)
        if c != len(objects):
            session.rollback()
            is_pass = False
            return {"ok": is_pass, "error": "add error"}
        else:
            try:
                session.commit()
                ids = [obj.id for obj in objects]
                is_pass = True
                return {"ok": is_pass, "ids": ids}
            except Exception as e:
                print(e)
                is_pass = False
                error = str(e)
                return {"ok": is_pass, "error": error}


# def db_to_sqlmodel(engine, classObj: SQLModel) -> List[SQLModel]:
#     """select data from table_name with where_clause"""
#     # engine = create_engine(db_url)
#     with Session(engine) as session:
#         statement = select(classObj)  # .where(SQLModel.name == "Example 1")
#         results: List[classObj] = session.exec(statement).all()
#
#         # objs = session.exec(f"SELECT * FROM {table_name} WHERE {where_clause}")
#     return results

def db_read_to_sqlmodel(engine, classObj: SQLModel, where_clause=None) -> List[SQLModel]:
    """select data from table_name with where_clause

    where_clause = SQLModel.name == "Example 1"

    """
    # engine = create_engine(db_url)
    with Session(engine) as session:
        if where_clause is None:
            statement = select(classObj)
        else:
            statement = select(classObj).where(where_clause)
        # statement = select(classObj)  # .where(SQLModel.name == "Example 1")
        results: List[classObj] = session.exec(statement).all()

        # objs = session.exec(f"SELECT * FROM {table_name} WHERE {where_clause}")
    return results


def json_to_sqlmodel(row_json, module_path, class_name):
    # 直接轉Books(dict)
    obj = load_class(module_path, class_name, row_json)
    return obj


# 為了避免sql exception，所以要將所有nan補值
def handle_nas(df, default_date='2020-01-01'):
    """
    :param df: a dataframe
    :param d: current iterations run_date
    :return: a data frame with replacement of na values as either 0 for numeric fields, 'na' for text and False for bool
    """
    for f in df.columns:

        # integer
        if df[f].dtype == "int64":
            df[f] = df[f].fillna(0)

        # dates
        elif df[f].dtype == '<M8[ns]':
            df[f] = df[f].fillna(pd.to_datetime(default_date))

        # float
        elif df[f].dtype == 'float64':
            df[f] = df[f].fillna(0.0)
        # boolean
        elif df[f].dtype == 'bool':
            df[f] = df[f].fillna(False)

        # string
        else:
            df[f] = df[f].fillna('')

    return df


def exe_csv_to_sqlmodel_to_db():
    path = 'd:/temp3/books.csv'
    df = load_data(path)
    print(df.head())
    print(df.columns)
    print(df.dtypes)
    print("*********")
    df = handle_nas(df)

    print(df.isna().any())

    # gen vo
    s = df_gen_sqlmodel(df, "Books")
    print(s)

    objs = df_to_sqlmodel(df, "autobee.tmp.vo", "Books")
    print(len(objs))
    db_url = "mysql+mysqlconnector://root:ps123@localhost:3306/autobee"
    engine = create_engine(db_url)
    sqlmodel_add_to_db(objs, engine)


def exe_db_to_sqlmodel():
    db_url = "mysql+mysqlconnector://root:ps123@localhost:3306/autobee"
    engine = create_engine(db_url)
    module_name = "autobee.tmp.vo"
    # init_data = {"form_id": "form_id", "block_id": "block_id", "itm": "f",
    #        "column_name": "column_name", "label_name": "column_name", "data_name": "column_name"}
    class_name = "Books"

    # obj=load_class(module_name,class_name,init_data=None)
    class_ = import_class(module_name, class_name)
    results = db_read_to_sqlmodel(engine, class_)
    print(len(results))

    df = sqlmodel_to_df(results)
    print(df.head())

    return df


if __name__ == '__main__':
    exe_csv_to_sqlmodel_to_db()  # 要手動修改資料庫結構，varchat>text, int>bigint
    # exe_db_to_sqlmodel()
