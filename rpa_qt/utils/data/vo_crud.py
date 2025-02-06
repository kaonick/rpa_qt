import json
import logging
from typing import Dict, Any

import pandas as pd


from rpa_qt.db.vo import Browser

from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.invoker import import_class, import_module
from rpa_qt.utils.data.vo_parser import json_to_sqlmodel, sqlmodel_add_to_db, db_read_to_sqlmodel, df_to_sqlmodel
from sqlmodel import Session, create_engine, select, text




class VoCRUD:

    def __init__(self, db_url: str = settings.db_url):
        self.db_url = db_url
        try:
            self.engine = create_engine(self.db_url)
        except Exception as e:
            logging.error(f"import_module error: {e}")
            raise e
        self.register_table = {}  # table_name:module_path

    def register(self, table_name: str, module_path: str):
        if table_name in self.register_table:
            pass
        else:
            self.register_table[table_name] = module_path
            import_module(module_path)

    def insert(self, data:[]) -> Dict[str, Any]:
        """Create data"""
        rows = []
        for row in data:
            rows.append(row)

        return sqlmodel_add_to_db(rows, self.engine)

    def select(self, table_name:str, sql:str, params:Dict) -> Dict[str, Any]:
        """Read data"""
        # query = '''SELECT *
        #            FROM "Historique"
        #            WHERE "index" BETWEEN :dstart AND :dfinish'''
        # pd.read_sql(query, con=conn, params={"dstart": start, "dfinish": end})
        # from sqlalchemy import create_engine

        # eng=create_engine(self.db_url)
        # conn=eng.connect()
        try:
            module_path = self.register_table[table_name]
            class_ = import_class(module_path, table_name)  # 很慢

            conn = self.engine.connect()
            sql_e=text(sql)

            query_string = sql % params
            print(f"query_string:{query_string}")

            df = pd.read_sql(text(sql), con=conn, params=params)  # text(sql) 很重要，這樣才會使用:參數格式。
            # df = pd.read_sql(sql, con=conn, params=params)
            conn.close()

            vos=df_to_sqlmodel(df, module_path, table_name) #不必要，太慢了。

            return {'ok': True, 'data': vos}
        except Exception as e:
            return {'ok': False, 'error': error}

    def update(self, table_name:str, data:[]) -> Dict[str, Any]:
        """Update data"""
        module_path = self.register_table[table_name]
        class_ = import_class(module_path, table_name)  # 很慢

        with Session(self.engine) as session:
            c = 0
            error = 'error:'
            for vo in data:
                try:
                    statement = select(class_).where(class_.id == vo.id)
                    results = session.exec(statement)
                    row = results.one()
                    print("row:", row)

                    # row=vo
                    for key, value in iter(row):
                        if key == 'id':
                            continue
                        setattr(row, key, getattr(vo, key))  # getattr(vo, key) vo[key]
                    session.add(row)
                    session.commit()
                    session.refresh(row)
                    print("Updated :", row)
                    c += 1
                except Exception as e:
                    print(e)
                    error = error + "\n" + str(e)
            if c == len(data):
                return {'ok': True}
            else:
                return {'ok': False, 'error': error}


    def delete(self, table_name:str, data:[]) -> Dict[str, Any]:
        """Delete data"""

        module_path = self.register_table[table_name]
        class_ = import_class(module_path, table_name)  # 很慢

        with Session(self.engine) as session:

            c = 0
            error = 'error:'
            for vo in data:
                statement = select(class_).where(class_.id == vo.id)
                results = session.exec(statement)
                row = results.one()
                print("row:", row)

                try:
                    session.delete(row)
                    session.commit()
                    print("Deleted :", row)
                    c += 1
                except Exception as e:
                    print(e)
                    error = error + "\n" + str(e)
            if c == len(data):
                return {'ok': True}
            else:
                return {'ok': False, 'error': error}

    async def crud(self, payload: Dict[str, Any]):
        data = json.loads(json.dumps(payload))
        action = data['action']  # curd

        match action:
            case 'create':
                return self.insert(data)
            case 'read':
                return self.select(data)
            case 'update':
                return self.update(data)
            case 'delete':
                return self.delete(data)


def tmp_data_create(db_exe:VoCRUD):
    port="9999"
    browser = Browser(browser_name=f"chrome_{port}", web_url="https://www.google.com", chrome_remote_port=f"{port}")
    # db_exe = VoCRUD()
    db_exe.register("Browser", "rpa_qt.db.vo")
    result = db_exe.insert([browser])
    print(result)


def tmp_data_read(db_exe:VoCRUD):
    sql="select * from browser" # 注意要小寫？
    params={}
    # db_exe = VoCRUD()
    db_exe.register("Browser", "rpa_qt.db.vo")
    table_name = "Browser"
    result = db_exe.select(table_name, sql, params)
    print(result)


def tmp_data_update(db_exe:VoCRUD):
    # db_exe = VoCRUD()
    db_exe.register("Browser", "rpa_qt.db.vo")

    table_name="Browser"
    sql="select * from browser where browser_name='chrome_9999'"
    params={}

    result = db_exe.select(table_name, sql, params)
    data_4u = []
    if result['ok']:
        data = result['data']
        for row in data:
            row.browser_name = row.browser_name + "的描述"
            data_4u.append(row)

    result = db_exe.update(table_name, data_4u)
    print(result)











if __name__ == '__main__':
    db_exe = VoCRUD(db_url=settings.db_url)
    # tmp_data_create(db_exe)
    # tmp_data_read(db_exe)
    # tmp_data_update(db_exe)
    # tmp_data_delete(db_exe)

