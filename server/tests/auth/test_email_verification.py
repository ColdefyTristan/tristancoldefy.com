from datetime import timedelta

from sqlmodel import select

from app.models.tables import UserEmailAddress, EmailVerificationToken
from app.security import generate_raw_token, hmac_token
from app.settings import settings
from app.utils.time import utcnow_naive


def _create_valid_token(session, user) -> str:
    """Insère directement un token de vérification valide pour le pending email de l'user."""
    user_email = session.exec(
        select(UserEmailAddress).where(UserEmailAddress.id == user.pending_email_id)
    ).first()
    assert user_email is not None

    raw_token = generate_raw_token()
    token_hash = hmac_token(raw_token, settings.EMAIL_TOKEN_SECRET)
    verif_token = EmailVerificationToken(
        token_hash=token_hash,
        expires_at=utcnow_naive() + timedelta(seconds=300),
        email_id=user_email.id,
    )
    session.add(verif_token)
    session.commit()
    return raw_token


# --- POST /auth/email/verification/send ---


def test_send_verification_returns_401_without_auth(client):
    r = client.post("/auth/email/verification/send")
    assert r.status_code == 401


def test_send_verification_returns_404_when_no_pending_email(auth_client):
    ctx = auth_client(email=None)
    r = ctx["client"].post("/auth/email/verification/send")
    assert r.status_code == 404
    assert r.json()["code"] == "PENDING_EMAIL_MISSING"


# --- POST /auth/email/verification/verify ---


def test_verify_email_returns_200_on_valid_token(session, client, user_factory):
    user = user_factory(email="to_verify@example.com", is_email_primary=False)
    raw_token = _create_valid_token(session, user)

    r = client.post("/auth/email/verification/verify", json={"token": raw_token})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_verify_email_sets_primary_email(session, client, user_factory):
    user = user_factory(email="new_primary@example.com", is_email_primary=False)
    raw_token = _create_valid_token(session, user)

    client.post("/auth/email/verification/verify", json={"token": raw_token})

    session.refresh(user)
    assert user.primary_email_id is not None


def test_verify_email_clears_pending_email(session, client, user_factory):
    user = user_factory(email="clear_pending@example.com", is_email_primary=False)
    raw_token = _create_valid_token(session, user)

    client.post("/auth/email/verification/verify", json={"token": raw_token})

    session.refresh(user)
    assert user.pending_email_id is None


def test_verify_email_returns_401_on_invalid_token(client, user_factory):
    user_factory(email="dummy@example.com", is_email_primary=False)
    r = client.post("/auth/email/verification/verify", json={"token": "invalid-token"})
    assert r.status_code == 401
    assert r.json()["code"] == "EMAIL_TOKEN_INVALID"


def test_verify_email_returns_401_on_expired_token(session, client, user_factory):
    user = user_factory(email="expired@example.com", is_email_primary=False)
    user_email = session.exec(
        select(UserEmailAddress).where(UserEmailAddress.id == user.pending_email_id)
    ).first()

    raw_token = generate_raw_token()
    token_hash = hmac_token(raw_token, settings.EMAIL_TOKEN_SECRET)
    expired_token = EmailVerificationToken(
        token_hash=token_hash,
        expires_at=utcnow_naive() - timedelta(seconds=1),
        email_id=user_email.id,
    )
    session.add(expired_token)
    session.commit()

    r = client.post("/auth/email/verification/verify", json={"token": raw_token})
    assert r.status_code == 401
    assert r.json()["code"] == "EMAIL_TOKEN_INVALID"


def test_verify_email_returns_401_on_consumed_token(session, client, user_factory):
    user = user_factory(email="consumed@example.com", is_email_primary=False)
    raw_token = _create_valid_token(session, user)

    r1 = client.post("/auth/email/verification/verify", json={"token": raw_token})
    assert r1.status_code == 200

    r2 = client.post("/auth/email/verification/verify", json={"token": raw_token})
    assert r2.status_code == 401
    assert r2.json()["code"] == "EMAIL_TOKEN_INVALID"