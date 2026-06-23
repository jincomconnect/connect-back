import os
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

    demo_user_email: str = "demo@example.com"
    demo_user_password: str = "password123"
    demo_user_name: str = "Demo User"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


def _resolve_env_files() -> tuple[str, ...]:
    app_env = os.getenv("APP_ENV", "").strip().lower()

    if not app_env and os.path.exists(".env"):
        with open(".env", encoding="utf-8") as env_file:
            for line in env_file:
                normalized_line = line.strip()

                if not normalized_line or normalized_line.startswith("#"):
                    continue

                if normalized_line.startswith("APP_ENV="):
                    app_env = normalized_line.split("=", 1)[1].strip().lower()
                    break

    if not app_env:
        app_env = "dev"

    env_aliases = {
        "dev": "development",
        "development": "development",
        "test": "test",
        "prod": "production",
        "production": "production",
    }
    normalized_env = env_aliases.get(app_env, app_env)

    return (".env", f".env.{normalized_env}")


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=_resolve_env_files())
