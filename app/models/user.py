import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class User:
    email: str
    password_hash: str
    name: str
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    phone_number: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "phone_number": self.phone_number,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            user_id=data.get("_id"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            name=data.get("name"),
            phone_number=data.get("phone_number"),
        )
