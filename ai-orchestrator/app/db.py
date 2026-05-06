from __future__ import annotations

import os

from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/auth-demo")
        _client = AsyncIOMotorClient(uri)
    return _client


def get_db():
    return get_client()[_db_name()]


def _db_name() -> str:
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/auth-demo")
    # extract the db name from the URI path, fall back to "auth-demo"
    path = uri.rsplit("/", 1)[-1].split("?")[0]
    return path or "auth-demo"
