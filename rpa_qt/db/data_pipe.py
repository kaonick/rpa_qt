from rpa_qt.db.vo import SearchCase, SearchResult
from rpa_qt.utils.data.data_queue import SqlWriterThread

dbpipe_SearchCase= SqlWriterThread(module_path="rpa_qt.db.vo",table_name="SearchCase")
dbpipe_SearchSource= SqlWriterThread(module_path="rpa_qt.db.vo",table_name="SearchSource")
dbpipe_SearchResult= SqlWriterThread(module_path="rpa_qt.db.vo",table_name="SearchResult")




if __name__ == '__main__':

    for i in range(10):
        vo = SearchCase(case_id=f"test{i}{i}", question="test")
        dbpipe_SearchCase.put(vo)


    for i in range(10):
        vo = SearchResult(case_id=f"test{i}{i}", site_name="test{i}",item=f"item{i}")
        dbpipe_SearchResult.put(vo)