from app.core.settings import get_settings


class DatabaseConfig:
    """Placeholder until database client/session manager is implemented."""

    def __init__(self) -> None:
        settings = get_settings()
        self.mongo_uri = settings.mongo_uri
        self.mongo_db_name = settings.mongo_db_name


db_config = DatabaseConfig()
