from typing import TypedDict

from pymongo.errors import DuplicateKeyError, PyMongoError

from app.db.session import get_collection


class StoredUser(TypedDict):
    email: str
    name: str
    password: str


class AuthRepository:
    def __init__(self) -> None:
        self.collection = get_collection("users")
        self.collection.create_index("email", unique=True)

    def get_by_email(self, email: str) -> StoredUser | None:
        doc = self.collection.find_one({"email": email}, {"_id": 0, "email": 1, "name": 1, "password": 1})

        if doc is None:
            return None

        return StoredUser(email=doc["email"], name=doc["name"], password=doc["password"])

    def create_user(self, *, email: str, name: str, password: str) -> bool:
        try:
            result = self.collection.insert_one({"email": email, "name": name, "password": password})
            return bool(result.inserted_id)
        except DuplicateKeyError:
            return False
        except PyMongoError:
            raise