from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "connect-back-python"
    app_env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"

    mongo_uri: str = "mongodb://localhost:27017/auth-demo"
    mongo_db_name: str = "auth-demo"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
