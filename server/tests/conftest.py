import os
import pytest
import uuid

from sqlmodel import SQLModel, Session, create_engine
import app.models.tables
from app.models.tables import User
from app.security import hash_password
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db import get_session
from app.services.auth.emails import add_pending_email, set_primary_email
from app.utils.time import utcnow_naive


DEFAULT_PASSWORD = "TestPassword123!"


@pytest.fixture(scope="session")
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "La variable d'environnement TEST_DATABASE_URL est requise. "
            "Exemple : postgresql+psycopg://app:password@localhost:5432/test_db"
        )
    return create_engine(url)


@pytest.fixture
def session(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    SQLModel.metadata.create_all(engine)

    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_verified_email "
                "ON user_email_address(email) "
                "WHERE verified_at IS NOT NULL"
            )
        )
        conn.commit()

    with Session(engine) as session:
        yield session


@pytest.fixture(scope="session")
def default_password_hash():
    return hash_password(DEFAULT_PASSWORD)


@pytest.fixture(scope="session")
def default_password():
    return DEFAULT_PASSWORD


@pytest.fixture
def user_factory(session, default_password_hash):
    def create_user(**overrides):
        email = overrides.get("email", f"test_{uuid.uuid4().hex}@example.com")
        is_email_primary = overrides.get("is_email_primary", False)
        user = User(
            username=overrides.get("username", f"user_{uuid.uuid4().hex[:8]}"),
            is_active=overrides.get("is_active", True),
            password_hash=overrides.get("password_hash", default_password_hash),
        )
        session.add(user)
        session.flush()
        if email:
            user_email_address = add_pending_email(
                session=session, user=user, email_str=email
            )
            if is_email_primary:
                user_email_address.verified_at = utcnow_naive()
                set_primary_email(user=user, user_email=user_email_address)

        session.commit()
        session.refresh(user)
        return user

    return create_user


@pytest.fixture
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client, user_factory, default_password):
    def create_auth(**overrides):
        remember_me = overrides.pop("remember_me", False)
        user = user_factory(**overrides)
        r = client.post(
            "/auth/login",
            json={
                "identifier": user.username,
                "password": default_password,
                "remember_me": remember_me,
            },
        )

        assert r.status_code == 200
        assert client.cookies.get("session_id") is not None

        return {"client": client, "user": user, "response": r}

    return create_auth