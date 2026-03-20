from sqlmodel import SQLModel
from typing import Annotated
from pydantic import EmailStr, StringConstraints, field_validator


Username = Annotated[
    str, StringConstraints(min_length=3, max_length=25, pattern=r"^[a-zA-Z0-9_]+$")
]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class RegisterRequest(SQLModel):
    email: EmailStr | None = None
    username: Username
    password: Password
    remember_me: bool = False

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError("PASSWORD_MISSING_LOWER")
        if not any(c.isupper() for c in v):
            raise ValueError("PASSWORD_MISSING_UPPER")
        if not any(c.isdigit() for c in v):
            raise ValueError("PASSWORD_MISSING_DIGIT")
        if not any(not c.isalnum() for c in v):
            raise ValueError("PASSWORD_MISSING_SYMBOL")
        return v


class LoginRequest(SQLModel):
    identifier: str  # username OR email
    password: str
    remember_me: bool = False


class EmailTokenVerificationRequest(SQLModel):
    token: str
