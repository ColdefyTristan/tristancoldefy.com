from _utils import _get_user_session_by_cookie_token


def test_logout_returns_204_and_clears_cookie(auth_client):
    ctx = auth_client()
    client = ctx["client"]

    assert client.cookies.get("session_id") is not None
    r = client.post("/auth/logout")
    assert r.status_code == 204
    assert client.cookies.get("session_id") is None


def test_logout_revokes_session(session, auth_client):
    ctx = auth_client()
    client = ctx["client"]
    token = ctx["response"].cookies.get("session_id")

    r = client.post("/auth/logout")
    assert r.status_code == 204

    user_session = _get_user_session_by_cookie_token(session, token)
    assert user_session.revoked_at is not None


def test_logout_returns_401_without_session(client):
    r = client.post("/auth/logout")
    assert r.status_code == 401
