import pytest
from fastapi.testclient import TestClient
from app.main import app
from _utils import _get_user_session_by_cookie_token


@pytest.mark.parametrize(
    "bad_password", ["wrong", "Wrong", "", "123", "TestPassword123! "]
)
def test_login_returns_401_on_wrong_password(client, user_factory, bad_password):
    user = user_factory()
    r = client.post(
        "/auth/login",
        json={
            "identifier": user.username,
            "password": bad_password,
            "remember_me": False,
        },
    )
    assert r.status_code == 401


def test_login_sets_session_cookie_on_success(client, user_factory, default_password):
    user = user_factory()
    r = client.post(
        "/auth/login",
        json={
            "identifier": user.username,
            "password": default_password,
            "remember_me": False,
        },
    )
    assert r.status_code == 200
    assert r.cookies.get("session_id") is not None


def test_login_remember_me_changes_db_expiration(
    session, client, user_factory, default_password
):
    user = user_factory()

    r1 = client.post(
        "/auth/login",
        json={
            "identifier": user.username,
            "password": default_password,
            "remember_me": False,
        },
    )
    token1 = r1.cookies.get("session_id")
    assert token1 is not None
    us1 = _get_user_session_by_cookie_token(session, token1)

    r2 = client.post(
        "/auth/login",
        json={
            "identifier": user.username,
            "password": default_password,
            "remember_me": True,
        },
    )
    token2 = r2.cookies.get("session_id")
    assert token2 is not None
    us2 = _get_user_session_by_cookie_token(session, token2)

    assert us1.expires_at < us2.expires_at


def test_login_returns_401_on_inactive_user(client, user_factory, default_password):
    user = user_factory(is_active=False)

    r = client.post(
        "/auth/login",
        json={
            "identifier": user.username,
            "password": default_password,
            "remember_me": False,
        },
    )

    assert r.status_code == 401
    assert r.json()["code"] == "INVALID_CREDENTIALS"


def test_login_accepts_email_or_username(client, user_factory, default_password):
    user = user_factory(email="test_mail@exemple.com", is_email_primary=True)
    # username
    with TestClient(app) as c1:
        r1 = client.post(
            "/auth/login",
            json={
                "identifier": user.username,
                "password": default_password,
                "remember_me": False,
            },
        )
        assert r1.status_code == 200
        assert r1.cookies.get("session_id") is not None
    # email
    with TestClient(app) as c2:
        r2 = client.post(
            "/auth/login",
            json={
                "identifier": "test_mail@exemple.com",
                "password": default_password,
                "remember_me": False,
            },
        )
        assert r2.status_code == 200
        assert r2.cookies.get("session_id") is not None


def test_email_must_be_primary_to_login(client, user_factory, default_password):
    user = user_factory(email="test_mail@exemple.com", is_email_primary=False)

    with TestClient(app) as c1:
        r1 = client.post(
            "/auth/login",
            json={
                "identifier": "test_mail@exemple.com",
                "password": default_password,
                "remember_me": False,
            },
        )
        assert r1.status_code == 401
