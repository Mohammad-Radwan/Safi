import re
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utilities import create_password_hash


class User(BaseModel):
    name: str = Field(..., min_length=3, max_length=30, description="User Full Name")
    username: str = Field(
        ..., min_length=3, max_length=18, description="Unique username"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password_hash: str = Field(..., alias="password")
    user_id: UUID = Field(default_factory=uuid4)
    phone_number: Optional[str] = None

    @field_validator("password_hash", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return create_password_hash(v)

    class Config:
        populate_by_name = True


class RegisterUser(BaseModel):
    name: str = Field(..., min_length=3, max_length=30, description="User Full Name")
    username: str = Field(
        ..., min_length=3, max_length=18, description="Unique username"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8)

    phone_number: Optional[str] = None

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginUser(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
