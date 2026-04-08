from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    role: Literal["owner", "mechanic"] = "owner"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
