"""
https://stackoverflow.com/questions/65619496/python-improving-performance-writing-to-database-in-seperate-thread
提供客服對話記錄的資料庫存取功能
利用queue跟threading來實現非同步寫入資料庫
"""

import threading
import queue
from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.data.vo_crud import VoCRUD




class SqlWriterThread(threading.Thread):

    def __init__(self,table_name,module_path, maxsize=8):
        super().__init__()
        self.table_name = table_name
        self.dao = VoCRUD(db_url=settings.db_url)
        self.dao.register(module_path=module_path,table_name=table_name)

        self.is_debug = True

        self.q = queue.Queue(maxsize)
        # TODO: Can expose q.put directly if you don't need to
        # intercept the call
        # self.put = q.put
        self.start()

    def put(self, vo):
        if self.is_debug:
            print(f"DEBUG: Putting...{vo}")
        self.q.put(vo)

    def run(self):
        # dao = VoCRUD(db_url=settings.db_url)
        while True:
            # get all the statements you can, waiting on first
            statements = [self.q.get()]
            try:
                while True:
                    statements.append(self.q.get(block=False)) #, block=False
            except queue.Empty:
                pass
            try:
                # early exit before connecting if channel is closed.
                if statements[0] is None:
                    return

                try:
                    if self.is_debug:
                        print("Debug: Executing\n", "--------\n".join(f"{id(s)} {s}" for s in statements))
                    # todo: need to detect closed connection, then reconnect and resart loop
                    for statement in statements:
                        if statement is None:
                            return
                        try:
                            self.dao.insert([statement])
                        except Exception as e:
                            print("Error: ", e)
                            try:
                                self.dao.update(table_name=self.table_name, data=[statement])
                            except Exception as e:
                                print("Error: ", e)
                finally:
                    pass
            finally:
                for _ in statements:
                    self.q.task_done()
                    if self.is_debug:
                        print("Debug: Task done")


