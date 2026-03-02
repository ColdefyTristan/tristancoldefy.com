from sqlmodel import Session, select
from fastapi import HTTPException
from datetime import timedelta

from sqlalchemy import update

from app.constants import (
    EMAIL_VERIFICATION_COOLDOWN,
    EMAIL_VERIFICATION_EXPIRATION_TIME,
)
from app.models.tables import User, UserEmailAddress, EmailVerificationToken

from app.utils.time import utcnow_naive
from app.security import generate_raw_token, hmac_token
from app.settings import settings


def revoke_active_email_verification_tokens(
    session: Session, email_id: int, now=utcnow_naive
) -> int:
    stmt = (
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.email_id == email_id,
            EmailVerificationToken.consumed_at.is_(None),
            EmailVerificationToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    res = session.exec(stmt)

    return res.rowcount or 0


def create_email_verification_token(
    session: Session, user: User, user_email: UserEmailAddress
) -> str:  # return le token
    stmt_last = (
        select(EmailVerificationToken)
        .where(
            EmailVerificationToken.email_id == user_email.id,
            EmailVerificationToken.consumed_at.is_(None),
            EmailVerificationToken.revoked_at.is_(None),
        )
        .order_by(EmailVerificationToken.created_at.desc())
    )
    last_active = session.exec(stmt_last).first()

    now = utcnow_naive()
    if last_active and now - last_active.created_at < timedelta(
        seconds=EMAIL_VERIFICATION_COOLDOWN
    ):
        raise HTTPException(
            429,
            details={
                "code": "EMAIL_VERIFICATION_RATE_LIMITED",
                "message": "Too many verification emails sent in a short time. Please try again later.",
                "fields": {"email_verification": "rate_limited"},
            },
        )

    if last_active:
        revoke_active_email_verification_tokens(
            session=session, email_id=user_email.id, now=now
        )

    user_email.verification_sent_at = now

    raw_token = generate_raw_token()
    token_hash = hmac_token(token=raw_token, secret=settings.EMAIL_TOKEN_SECRET)

    expires_at = now + timedelta(seconds=EMAIL_VERIFICATION_EXPIRATION_TIME)

    verif_token = EmailVerificationToken(
        token_hash=token_hash,
        expires_at=expires_at,
        email_id=user_email.id,
    )

    session.add(verif_token)

    return raw_token


def deliver_email_verification(
    user_email: UserEmailAddress, token: str, email_sender=None
):
    # now = utcnow_naive()
    # expires_at = now + timedelta(seconds=EMAIL_VERIFICATION_EXPIRATION_TIME)

    if not email_sender:
        return {"ok": False}

    email_sender.send_verification_email(user_email=user_email, token=token)

    # verification_url = f"{settings.FRONTEND_BASE_URL}/verify-email?token={token}"
    # email_sender.send_verification_email(to=email.email, verification_url=verification_url)

    return {"ok": True}


def confirm_email_verification(token: str) -> UserEmailAddress:
    pass
