from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_connector: str
    database_aconnector: str
    database_hostname: str
    database_username: str
    database_password: str
    database_port: int
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # Email settings
    smtp_server: str
    smtp_port: int
    mail_user: str
    mail_password: str
    sender_email: str

    redis_host: str
    redis_port: int

    google_credentials_json_path: str
    gemini_api_key: str

    base_url: str




    class Config:
        # env_file = ".env" # 必須在跟main.py在同一目錄下，所有參數都對應才能。
        env_file = "d:/00WS-TMP/rpa_qt/rpa_qt/backend/.env"  # 測試用。


settings = Settings()
