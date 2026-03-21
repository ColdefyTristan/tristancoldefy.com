from datetime import datetime
import pytest

from _utils import _get_user_session_by_cookie_token
from app.services.auth.emails import add_pending_email


@pytest.mark.parametrize(
    "ctx_kwargs, extra_pending_email, expected",
    [
        # 1) pending only
        (
            {"email": "pending@example.com", "is_email_primary": False},
            None,
            {"primary": None, "pending": "pending@example.com"},
        ),
        # 2) primary only
        (
            {"email": "primary@example.com", "is_email_primary": True},
            None,
            {"primary": "primary@example.com", "pending": None},
        ),
        # 3) primary + pending
        (
            {"email": "primary2@example.com", "is_email_primary": True},
            "pending2@example.com",
            {"primary": "primary2@example.com", "pending": "pending2@example.com"},
        ),
    ],
)
def test_me_validation(auth_client, session, ctx_kwargs, extra_pending_email, expected):
    ctx = auth_client(**ctx_kwargs)
    client = ctx["client"]
    user = ctx["user"]

    if extra_pending_email:
        add_pending_email(session=session, user=user, email_str=extra_pending_email)
        session.commit()

    r = client.get("auth/me")
    assert r.status_code == 200

    payload = r.json()
    assert payload["id"] == user.id
    assert payload["username"] == user.username

    assert payload["email"]["primary"] == expected["primary"]
    assert payload["email"]["pending"] == expected["pending"]


def test_me_returns_401_without_cookie(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_401_on_invalid_session(client):
    # --- invalid token
    client.cookies.set("session_id", "invalid-token")
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_returns_401_on_expired_session(session, auth_client):
    # --- expired token (on crée une vraie session, puis on la force expirée en DB)
    ctx = auth_client()
    authed_client = ctx["client"]

    token = authed_client.cookies.get("session_id")
    assert token is not None

    us = _get_user_session_by_cookie_token(session, token)
    us.expires_at = datetime(2000, 1, 1)
    session.add(us)
    session.commit()

    r2 = authed_client.get("/auth/me")
    assert r2.status_code == 401
