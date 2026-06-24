from app.core.settings import get_settings
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


_mongo_client: MongoClient | None = None


class DatabaseConfig:
    """Database configuration and lazy MongoDB client management."""

    def __init__(self) -> None:
        settings = get_settings()
        self.mongo_uri = settings.mongo_uri
        self.mongo_db_name = settings.mongo_db_name


db_config = DatabaseConfig()


def get_mongo_client() -> MongoClient:
    global _mongo_client

    if _mongo_client is None:
        _mongo_client = MongoClient(db_config.mongo_uri, serverSelectionTimeoutMS=1500)

    return _mongo_client


def get_database() -> Database:
    return get_mongo_client()[db_config.mongo_db_name]


def get_collection(name: str) -> Collection:
    return get_database()[name]


def close_mongo_client() -> None:
    global _mongo_client

    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
