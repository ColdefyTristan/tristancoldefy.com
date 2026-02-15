from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from app.db import get_session
from app.models import User, UserSession
from app.security import hash_token
from app.utils.time import utcnow_naive
from app.constants import IDLE_TIMEOUT_SECONDS, TOUCH_MIN_INTERVAL_SECONDS


@dataclass
class AuthContext:
    user: User
    user_session: UserSession


def get_current_auth(
    request: Request,
    session: Session = Depends(get_session),
) -> AuthContext:
    token = request.cookies.get("session_id")
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "NOT_AUTHENTICATED",
                "message": "Authentication required.",
                "fields": {"session_id": "missing"},
            },
        )

    token_h = hash_token(token)

    stmt = select(UserSession).where(UserSession.session_token_hash == token_h)
    user_session = session.exec(stmt).first()
    if not user_session:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "SESSION_INVALID",
                "message": "Invalid session.",
                "fields": {"session_id": "invalid"},
            },
        )

    now = utcnow_naive()
    if user_session.revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "SESSION_REVOKED",
                "message": "Session revoked.",
                "fields": {"session_id": "revoked"},
            },
        )
    if user_session.expires_at <= now or (
        user_session.idle_expires_at and user_session.idle_expires_at <= now
    ):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "SESSION_EXPIRED",
                "message": "Session expired.",
                "fields": {"session_id": "expired"},
            },
        )

    user = session.get(User, user_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "USER_INACTIVE",
                "message": "User account is inactive.",
                "fields": {"user": "inactive"},
            },
        )

    touch_session(session, user_session, now, IDLE_TIMEOUT_SECONDS)

    authContext = AuthContext(user=user, user_session=user_session)

    return authContext


def get_current_auth_optional(
    request: Request,
    session: Session = Depends(get_session),
) -> Optional[AuthContext]:
    try:
        return get_current_auth(request, session)
    except HTTPException:
        return None


def touch_session(
    db: Session, s: UserSession, now: datetime, idle_timeout_seconds: int
) -> None:
    if s.idle_expires_at is None:
        return

    if (
        s.last_seen_at
        and (now - s.last_seen_at).total_seconds() < TOUCH_MIN_INTERVAL_SECONDS
    ):
        return

    s.last_seen_at = now
    s.idle_expires_at = now + timedelta(seconds=idle_timeout_seconds)
    db.add(s)
