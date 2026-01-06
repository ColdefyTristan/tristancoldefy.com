from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Annotated
from pydantic import EmailStr, StringConstraints, field_validator
from sqlalchemy import Column, Integer, ForeignKey


from app.utils.time import utcnow_naive


class UserEmailAddress(SQLModel, table=True):
    __tablename__ = "user_email_address"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", name="fk_user_email_address_user_id"),
        )
    )
    email: EmailStr = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow_naive)
    is_active: bool = Field(default=True)

    verified_at: datetime | None = Field(default=None)
    verification_sent_at: datetime | None = Field(default=None)

    user: "User" = Relationship(
        back_populates="emails",
        sa_relationship_kwargs={"foreign_keys": lambda: [UserEmailAddress.user_id]},
    )

    verification_tokens: list["EmailVerificationToken"] = Relationship(
        back_populates="user_email_address",
        sa_relationship_kwargs={
            "foreign_keys": lambda: [EmailVerificationToken.email_id],
            "cascade": "all, delete-orphan",
        },
    )


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    primary_email_id: int | None = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                "user_email_address.id", use_alter=True, name="fk_user_primary_email"
            ),
            nullable=True,
        )
    )

    pending_email_id: int | None = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                "user_email_address.id", use_alter=True, name="fk_user_pending_email"
            ),
            nullable=True,
        )
    )

    emails: list["UserEmailAddress"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": [UserEmailAddress.user_id]},
    )

    primary_email: UserEmailAddress | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": lambda: [User.primary_email_id]},
    )

    pending_email: UserEmailAddress | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": lambda: [User.pending_email_id]},
    )

    password_hash: str
    created_at: datetime = Field(default_factory=utcnow_naive)
    is_active: bool = Field(default=True)


class UserSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id", index=True)

    session_token_hash: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=utcnow_naive)
    expires_at: datetime = Field(index=True)
    idle_expires_at: datetime | None = Field(index=True)

    last_seen_at: datetime = Field(default_factory=utcnow_naive)

    revoked_at: datetime | None = Field(default=None, index=True)

    # ip: str | None = None


class PasswordResetToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id", index=True)

    token_hash: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=utcnow_naive)
    expires_at: datetime = Field(index=True)

    used_at: datetime | None = Field(default=None, index=True)


class EmailVerificationToken(SQLModel, table=True):
    __tablename__ = "email_verification_token"
    id: int | None = Field(default=None, primary_key=True)
    email_id: int = Field(foreign_key="user_email_address.id", index=True)
    token_hash: str = Field(unique=True)
    created_at: datetime = Field(default_factory=utcnow_naive)
    expires_at: datetime = Field(index=True)

    consumed_at: datetime | None = Field(default=None, index=True)
    revoked_at: datetime | None = None

    user_email_address: "UserEmailAddress" = Relationship(
        back_populates="verification_tokens",
        sa_relationship_kwargs={
            "foreign_keys": lambda: [EmailVerificationToken.email_id]
        },
    )


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
        # exemple simple : au moins 1 chiffre
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
