import pytest
from app.models import User, UserEmailAddress, EmailVerificationToken
from sqlmodel import select


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "UserNoEmail", "password": "TestPassword123!"},
        {
            "username": "UserWithEmail",
            "email": "test_mail@example.com",
            "password": "TestPassword123!",
        },
    ],
)
def test_register_accepts_optional_email(session, client, payload):
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    user_id = data.get("user", data)["id"]

    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    assert user is not None
    if payload.get("email"):
        assert user.pending_email_id is not None


def test_register_accepts_duplicate_pending_email(session, client, user_factory):
    user_factory(email="duplicate_email@example.com", is_email_primary=False)
    r = client.post(
        "/auth/register",
        json={
            "username": "duplicateUsername",
            "email": "duplicate_email@example.com",
            "password": "TestPassword123!",
        },
    )
    assert r.status_code == 201
    data = r.json()
    user_id = data.get("user", data)["id"]

    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    assert user is not None
    assert user.pending_email_id is not None


def test_register_returns_409_on_duplicate_username(client, user_factory):
    user_factory(username="duplicateUsername")
    r = client.post(
        "/auth/register",
        json={"username": "duplicateUsername", "password": "TestPassword123!"},
    )

    assert r.status_code == 409
    assert r.json()["code"] == "USERNAME_TAKEN"


def test_register_returns_409_on_duplicate_primary_email(client, user_factory):
    user = user_factory(email="duplicate_email@example.com", is_email_primary=True)
    r = client.post(
        "/auth/register",
        json={
            "username": "newUsername",
            "email": "duplicate_email@example.com",
            "password": "TestPassword123!",
        },
    )

    assert r.status_code == 409
    assert r.json()["code"] == "EMAIL_TAKEN"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "UserWithoutPassword"},
        {"username": "userWithEmptyEmail", "email": "", "password": "TestPassword123!"},
        {
            "username": "userWithWrongEmail",
            "email": "false_email@nothing",
            "password": "TestPassword123!",
        },
    ],
)
def test_register_returns_422_on_invalid_payload(client, payload):
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 422


def test_register_with_mail_create_verification_token(client, session):
    r = client.post(
        "/auth/register",
        json={
            "username": "test_username",
            "email": "test_email@exemple.com",
            "password": "TestPassword123!",
        },
    )
    assert r.status_code == 201
    data = r.json()
    user_id = data.get("user", data)["id"]

    stmt = select(UserEmailAddress).where(UserEmailAddress.user_id == user_id)
    user_email = session.exec(stmt).first()

    assert user_email is not None

    stmt_last = (
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.email_id == user_email.id,
            EmailVerificationToken.consumed_at.is_(None),
            EmailVerificationToken.revoked_at.is_(None),
        )
        .order_by(EmailVerificationToken.created_at.desc())
    )
    assert session.exec(stmt_last).first() is not None
