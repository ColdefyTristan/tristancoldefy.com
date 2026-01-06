from app.security import hash_token
from sqlmodel import select
from app.models import UserSession


def _get_user_session_by_cookie_token(session, token: str) -> UserSession:
    token_h = hash_token(token)
    stmt = select(UserSession).where(UserSession.session_token_hash == token_h)
    us = session.exec(stmt).first()
    assert us is not None
    return us
