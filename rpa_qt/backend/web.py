import asyncio
import datetime
import os
from typing import Dict, Any
import json

import pandas as pd
import uvicorn
from fastapi import FastAPI,Body,BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pathlib import Path

import redis
from rpa_qt.background_task.celery_task_runner import run_task
from rpa_qt.db.data_pipe import dbpipe_SearchCase

from rpa_qt.db.vo import SearchCase, Browser, SearchSource
from rpa_qt.sys.task_manager import TaskManager
from rpa_qt.utils.config_yaml_loader import settings
from rpa_qt.utils.data.vo_crud import VoCRUD
from rpa_qt.utils.project_utils import get_case_code
from rpa_qt.utils.time_utils import get_now_code

# from rpa_qt.utils.data.util_data import file_to_list

# Create an instance of the FastAPI class
app = FastAPI()

# redis_client = redis.Redis(host = "localhost", port = 6379, db = 0, decode_responses = True)


origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Define a route
@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def get_health():
    # 測試用
    return {"status": "OK"}



"""
http://localhost:9401/get_suppliers
"""
@app.get("/get_suppliers")
async def get_suppliers():
    table_name_browser = "Browser"
    module_path_browser = "rpa_qt.db.vo"
    dao = VoCRUD(db_url=settings.db_url)
    dao.register(module_path=module_path_browser, table_name=table_name_browser)

    result=dao.select(table_name_browser, sql="select * from browser where available=1", params={})
    return result



task_manager=TaskManager()
async def search_steaming_response(case_id:str,browser_dict:{}):
    start_time = datetime.datetime.now()

    table_name = "SearchSource"
    module_path = "rpa_qt.db.vo"
    dao = VoCRUD(db_url=settings.db_url)
    dao.register(module_path=module_path, table_name=table_name)
    dao.register(module_path=module_path, table_name="SearchResult")
    all_browser = browser_dict.keys()
    done_browsers = []
    while True:
        left_browsers = all_browser - done_browsers
        if len(left_browsers) == 0:
            if len(done_browsers) != len(all_browser):
                # 除錯用：
                raise Exception("done_browsers != all_browser")
            break

        end_time = datetime.datetime.now()
        cost_time = end_time - start_time
        cost_time_seconds = cost_time.total_seconds()
        if cost_time_seconds > 90:
            print(f"over times...cost_time_seconds={cost_time_seconds}")
            break

        # left_browsers to str like "('pchome','yahoo','momoshop')"

        # left_browsers_str="("
        # for i,site_id in enumerate(left_browsers):
        #     if i==0:
        #         left_browsers_str = left_browsers_str + "'" + site_id + "'"
        #     else:
        #         left_browsers_str=left_browsers_str+",'"+site_id+"'"
        # left_browsers_str=left_browsers_str+")"


        left_browsers_str = str(tuple(left_browsers)).replace(",)", ")")

        sql=f"select * from searchsource where case_id = '{case_id}' and site_id in {left_browsers_str} order by site_id"

        # results = dao.data_read(table_name,
        #                        sql="select * from searchsource where case_id = %(case_id)s and site_id in %(site_id)s",
        #                        params={"case_id": f"'{case_id}'", "site_id": left_browsers_str})

        results = dao.select(table_name, sql=sql, params={})

        """
        select * from searchsource where case_id = '20241224174508129274_dcc9246f2c' and site_id in ('pchome', 'carrefour', 'fpgshopping', 'yahoo', 'momoshop');
        """

        if results and results["ok"]:
            data = results["data"]
            for item in data:
                site_group = {}  # 用site_id分組
                vo: SearchSource = item
                done_browsers.append(vo.site_id)

                if vo.result_rows>0:
                    # read search result
                    search_results = dao.select("SearchResult",
                                                sql="select * from searchresult where case_id = :case_id and site_id = :site_id ORDER BY site_id",
                                                params={"case_id": case_id,"site_id": vo.site_id})

                    if search_results and search_results["ok"]:
                        data = search_results["data"]

                        data_json=[ item.model_dump_json() for item in data]

                        site_group[vo.site_id] = data_json
                    else:
                        site_group[vo.site_id] = []
                else:
                    site_group[vo.site_id] = []

                json_object = json.dumps(site_group, indent=4)
                yield json_object+ "\n"
                # yield vo.model_dump_json() + "\n"
                await asyncio.sleep(0.5)
        else:
            if not results["ok"]:
                print(f"sql error={results['error']}")

        await asyncio.sleep(0.5)

    # send END
    await asyncio.sleep(0.5)
    site_group={"END": []}
    json_object = json.dumps(site_group, indent=4)
    yield json_object + "\n"

# 僅供測試用
@app.get("/search2")
async def search2(q:str, background_tasks: BackgroundTasks):
    case_id=get_case_code()

    print(f"case_id={case_id}")
    # case_id="20241223114719158257_4cfaa30a9a"
    question = "AP-04SRGA"  # 空氣清淨機
    search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())
    browser_dict = task_manager.get_all_browsers()


    """
        遇到StreamingResponse就無法執行background_tasks？
        https://github.com/fastapi/fastapi/discussions/11022
        
    """
    background_tasks.add_task(task_manager.run, search_case)

    response=StreamingResponse(search_steaming_response(case_id=case_id, browser_dict=browser_dict),
                      media_type='text/event-stream')
    # response=StreamingResponse(search_steaming_anwser(case_id=case_id, browser_dict=browser_dict))
    # background_tasks running


    return response

# ***
@app.get("/after_search")
async def after_search(case_id: str):
    browser_dict = task_manager.get_all_browsers()
    response = StreamingResponse(search_steaming_response(case_id=case_id, browser_dict=browser_dict),
                                 media_type='text/event-stream')
    return response

# ***
@app.get("/search")
async def search(q:str):
    case_id=get_case_code()
    # case_id="20241223114719158257_4cfaa30a9a"
    # question = "AP-04SRGA"  # 空氣清淨機
    question = q
    search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())

    # 方案一：採非同步執行，先存入案件，然後透過背景任務去進行爬蟲任務。目的是要確保多人使用時，運用資料庫作為queue，然後一筆一筆慢慢執行。
    dbpipe_SearchCase.put(search_case)
    return search_case

@app.get("/search_OLD")
async def search_OLD(q:str, background_tasks: BackgroundTasks):
    case_id=get_case_code()
    # case_id="20241223114719158257_4cfaa30a9a"
    # question = "AP-04SRGA"  # 空氣清淨機
    question = q
    search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())

    run_method_one=True
    if run_method_one:
        # 方案一：採非同步執行，先存入案件，然後透過背景任務去進行爬蟲任務。目的是要確保多人使用時，運用資料庫作為queue，然後一筆一筆慢慢執行。
        dbpipe_SearchCase.put(search_case)
    else:
        # 方案二：採同步執行，透過background_tasks執行。此方法限制只能一個人單純執行，會造成當兩人同時執行時，造成干擾，造成爬蟲異常。
        # background_tasks running
        background_tasks.add_task(task_manager.run, search_case)

    return search_case


# 僅供測試用
@app.get("/celery_search")
def celery_search(q:str):
    case_id=get_case_code()
    # case_id="20241223114719158257_4cfaa30a9a"
    # question = "AP-04SRGA"  # 空氣清淨機
    question = q
    search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())

    from celery import Celery
    app = Celery('celery_start',
                 broker='redis://localhost:6379/1',
                 )
    data = (search_case.model_dump_json(),)  # sample data
    # app.send_task('rpa_qt.tmp_celery.celery_start.hello_world', data)
    app.send_task('celery_task_runner.run_task', data)
    # run_task.delay(search_case.model_dump_json())
    # run_task.apply_async((search_case,), countdown=0)
    return search_case


"""
http://localhost:9401/get_search_result?case_id=20241223114719158257_4cfaa30a9a
"""
@app.get("/get_search_result")
async def get_search_result(case_id:str):
    table_name = "SearchResult"
    module_path = "rpa_qt.db.vo"
    dao = VoCRUD(db_url=settings.db_url)
    dao.register(module_path=module_path, table_name=table_name)

    result=dao.select(table_name, sql="select * from searchresult where case_id = :case_id ORDER BY site_id", params={"case_id": case_id})

    if result and result["ok"]:
        data=result["data"]
        site_group={}  # 用site_id分組
        now_site_id=""
        for item in data:
            if now_site_id!=item.site_id:
                now_site_id=item.site_id
                site_group[now_site_id]=[]
            else:
                pass
            site_group[now_site_id].append(item)

        result["data"]=site_group

    return result

"""
http://localhost:9401/downloadfile?file_name=www_taobao_com.png&task_id=supplier_logo
"""
@app.get('/downloadfile')
async def downloadfile(file_name: str,task_id:str=None,user_id:str=None):

    path=''
    if task_id is not None:
        path=path+'/'+task_id
    if user_id is not None:
        path=path+'/'+user_id

    file_location = f'{settings.file_root_dir}{path}/{file_name}'  # os.sep is used to seperate with a \

    # check if file exists
    # if os.path.exists(file_location) == False:
    #     file_location = f'{settings.file_root_dir}{path}/ftc_logo.png'

    return FileResponse(file_location, media_type='application/octet-stream', filename=file_name)

# streaming response
"""
http://localhost:9401/streaming
"""
# 僅供測試用
async def fake_data_streamer():
    table_name_browser = "Browser"
    module_path_browser = "rpa_qt.db.vo"
    dao = VoCRUD(db_url=settings.db_url)
    dao.register(module_path=module_path_browser, table_name=table_name_browser)

    results=dao.select(table_name_browser, sql="select * from browser where available=1", params={})
    if results and results["ok"]:
        data=results["data"]
        for item in data:
            vo:Browser=item
            yield vo.model_dump_json()+"\n"
            await asyncio.sleep(0.5)



    # for i in range(10):
    #     yield b'some fake data\n\n'
    #     await asyncio.sleep(0.5)

# 僅供測試用
@app.get('/streaming')
async def streaming():
    return StreamingResponse(fake_data_streamer(), media_type='text/event-stream')
    # or, use:
    '''
    headers = {'X-Content-Type-Options': 'nosniff'}
    return StreamingResponse(fake_data_streamer(), headers=headers, media_type='text/plain')
    '''

# 僅供測試用
async def stream_call(question:str):
    for i in range(10):
        yield b'some fake data\n\n'
        await asyncio.sleep(0.5)


# 僅供測試用
@app.get('/streaming_search')
async def streaming_search(q:str):
    start_time = datetime.datetime.now()
    task_manager=TaskManager()
    end_time = datetime.datetime.now()
    print(f"system begin cost time={end_time-start_time}")

    case_id=get_case_code()
    question = "AP-04SRGA"  # 空氣清淨機
    search_case=SearchCase(case_id=case_id,question=question,user="anonymous",txtm=get_now_code())

    start_time = datetime.datetime.now()

    # task_manager.run(search_case=search_case)

    # await task_manager.arun(search_case=search_case)

    # loop = asyncio.get_event_loop()
    # task = loop.create_task(task_manager.run(search_case=search_case))
    # loop.run_until_complete(task)

    # https://apifox.com/apiskills/fastapi-concurrent-requests/
    tasks = []
    task = asyncio.create_task(task_manager.arun(search_case=search_case))
    tasks.append(task)
    results = await asyncio.gather(*tasks)
    print("go go go")
    end_time = datetime.datetime.now()
    print(f"search cost time={end_time-start_time}")

    return StreamingResponse(fake_data_streamer(), media_type='text/event-stream')





def setup_static_files(app: FastAPI):
    """
    Setup the static files directory.
    Args:
        app (FastAPI): FastAPI app.
        path (str): Path to the static files directory.
    """
    main_path = Path(__file__).parent  # main.py所在目錄
    static_files_dir = main_path / "frontend"

    app.mount(
        "/",
        StaticFiles(directory=static_files_dir, html=True),
        name="static",
    )


setup_static_files(app)

if __name__ == '__main__':
    # ws_max_size: int = 16777216*8

    uvicorn.run(app, host="0.0.0.0", port=9401) # for debug