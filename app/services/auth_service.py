import secrets
from typing import Optional

from flask_jwt_extended import create_access_token, create_refresh_token

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.utilities import create_password_hash


class AuthService:
    def __init__(self):
        self.user_repository = UserRepository()

    def _does_user_exist(self, email: str) -> bool:
        self.current_user_dict: dict = self.user_repository.get_by_email(email)
        if self.current_user_dict:
            return True
        return False

    def register_user(
        self,
        name: str,
        username: str,
        email: str,
        password: str,
        phone_number: str = None,
    ) -> tuple[Optional[User], Optional[str]]:
        if self._does_user_exist(email):
            return None, "User already exists"

        new_user = User(
            name=name,
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
        )
        self.user_repository.add(new_user)
        return new_user, None

    def authenticate_user(
        self, email: str, password: str
    ) -> tuple[Optional[dict], Optional[str]]:
        if not (
            self._does_user_exist(email)
            and (
                secrets.compare_digest(
                    self.current_user_dict["password_hash"],
                    create_password_hash(password),
                )
            )
        ):
            return None, "The email or password is incorrect"

        access_token = create_access_token(identity=self.current_user_dict["_id"])
        refresh_token = create_refresh_token(identity=self.current_user_dict["_id"])

        # Exclude sensitive data like password_hash before returning user data
        user_safe = {
            k: v for k, v in self.current_user_dict.items() if k != "password_hash"
        }
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user_safe,
        }, None
