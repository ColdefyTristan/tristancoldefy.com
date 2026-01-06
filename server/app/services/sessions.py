from sqlmodel import Session
from datetime import timedelta

from app.models import UserSession
from app.security import new_session_token, hash_token
from app.utils.time import utcnow_naive
from app.constants import IDLE_TIMEOUT_SECONDS, LONG_SESSION_DAYS, SHORT_SESSION_DAYS


def create_user_session(
    session: Session, user_id: int, remember_me: bool = False
) -> str:
    token = new_session_token()
    now = utcnow_naive()
    expires = now + timedelta(
        days=LONG_SESSION_DAYS if remember_me else SHORT_SESSION_DAYS
    )
    print(remember_me)
    s = UserSession(
        user_id=user_id,
        session_token_hash=hash_token(token),
        created_at=now,
        expires_at=expires,
        idle_expire_at=(
            None if remember_me else now + timedelta(seconds=IDLE_TIMEOUT_SECONDS)
        ),
        # ip=request.client.host if request.client else None,
    )
    session.add(s)

    return token
