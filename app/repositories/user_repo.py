from typing import Optional

from app.models.user import User

from .base import IRepository


class UserRepository(IRepository):
    def __init__(self):
        super().__init__()
        self.collection = self.db["users"]

    def add(self, user: User) -> str:
        user_data = user.model_dump(exclude_none=True)
        user_data["_id"] = str(user.user_id)
        self.collection.insert_one(user_data)
        return str(user.user_id)

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return self.collection.find_one({"_id": user_id})

    def get_by_email(self, email: str) -> Optional[dict]:
        return self.collection.find_one({"email": email})

    def get_by_username(self, username: str) -> Optional[dict]:
        return self.collection.find_one({"username": username})

    def update(self, user_id: str, data: dict):
        self.collection.update_one({"_id": user_id}, {"$set": data})

    def delete(self, user_id: str):
        self.collection.delete_one({"_id": user_id})
