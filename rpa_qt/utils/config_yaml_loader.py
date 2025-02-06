import os
import sys
from functools import lru_cache
from pydantic import BaseModel
import yaml

from rpa_qt.root import ROOT_DIR


def open_yaml(yaml_path='./config/config.yaml'):
    try:
        with open(yaml_path, 'r', encoding="utf-8") as stream:
            try:
                # Converts yaml document to python object
                d = yaml.safe_load(stream)
                # d=yaml.load(stream, Loader=FullLoader)
                # for key, val in d.items():
                #     print(key, " : ", val,"\n")
                return d
            except yaml.YAMLError as e:
                print(e)


    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        print
        # 確保config_yaml執行時，可以讀取。
        if yaml_path == 'config.yaml':
            return None
        d = open_yaml(yaml_path='config.yaml')
        return d


class Settings(BaseModel):
    ad_auth: bool = False
    ldap_url: str = None
    ldap_domain: str = None
    jwt_secret_key: str=None
    has_proxy: bool=False
    proxy_url: str=None
    no_proxy: str=None
    web_base_url: str = None
    db_url: str=None
    project_root: str=None

    file_root_dir: str=None

    se_grid_user: str=None
    se_grid_key: str=None
    se_grid_url: str=None
    user_profile_root: str=None
    chrome_path: str=None
    chrome_remote_ip: str=None

    # es
    es_url: str=None
    es_user: str=None
    es_password: str=None

    # telegram-message
    telegram_token: str=None
    telegram_chat_id: str=None
    telegram_bot_url: str=None


@lru_cache()
def get_settings(yaml_path='./config/config.yaml'):
    if sys.platform == 'linux':
        # linux or image，透過volume掛載，所以路徑不同
        yaml_path = '/app/data/config/config.yaml'
        if os.path.exists(yaml_path) == False:
            raise Exception(f'config.yaml not found in {yaml_path}')


    d=open_yaml(yaml_path=yaml_path)

    # config = from_dict(data_class=Settings, data=d)
    config=Settings()
    if d is not None:
        config.ad_auth=d['ad_auth']
        config.ldap_url=d['ldap_url']
        config.ldap_domain=d['ldap_domain']
        config.jwt_secret_key=d['jwt_secret_key']
        config.has_proxy = d['has_proxy']
        config.proxy_url=d['proxy_url'] #避免帳密外洩，改用環境變數設定。
        # config.proxy_url=os.getenv("HTTP_PROXY")  #透過環境變數設定http_proxy會造成command line proxy異常？
        config.no_proxy=d['no_proxy']

        config.web_base_url = d['web_base_url']
        config.db_url=d['db_url']
        config.project_root=d['project_root']

        config.file_root_dir = d['file']['root_dir']

        config.se_grid_user=d['se_grid_user']
        config.se_grid_key=d['se_grid_key']
        config.se_grid_url=d['se_grid_url']
        config.user_profile_root=d['user_profile_root']
        config.chrome_path=d['chrome_path']
        config.chrome_remote_ip=d['chrome_remote_ip']

        # es
        config.es_url=d['es_url']
        config.es_user=d['es_user']
        config.es_password=d['es_password']

        # telegram-message
        config.telegram_token=d['telegram_token']
        config.telegram_chat_id=d['telegram_chat_id']
        config.telegram_bot_url=d['telegram_bot_url']



    return config

# print('project root='+ROOT_DIR)
settings=get_settings(yaml_path=f'{ROOT_DIR}/refs/config.yaml')


if __name__ == '__main__':
    # d=open_yaml()
    # settings=Settings()
    # settings.database_name=d['database_name']
    # settings.db_user=d['db_user']
    # settings.db_password=d['db_password']
    #
    # print(settings.database_name)

    settings=get_settings(f'D:/CONFIG/config.yaml')
    print(settings)
