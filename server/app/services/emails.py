from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import UserEmailAddress, User, EmailVerificationToken


def normalize_email(email: str) -> str:
    return email.strip().lower()


def add_pending_email(session: Session, user: User, email_str: str) -> UserEmailAddress:
    email_normalised = normalize_email(email_str)

    stmt = select(UserEmailAddress).where(
        UserEmailAddress.user_id == user.id,
        UserEmailAddress.email == email_normalised,
    )
    addr = session.exec(stmt).first()

    if addr:
        if addr.verified_at is not None:
            raise HTTPException(400, "this email is already verified for this user")

        user.pending_email_id = addr.id
        return addr

    addr = UserEmailAddress(user_id=user.id, email=email_normalised)
    session.add(addr)
    session.flush()

    user.pending_email_id = addr.id
    return addr


def set_primary_email(user: User, user_email: UserEmailAddress) -> None:

    if user_email.user_id != user.id:
        raise HTTPException(400, "email does not belong to this user")

    if user_email.verified_at is None:
        raise HTTPException(400, "email is not verified")

    if user.primary_email_id == user_email.id:
        return

    user.primary_email_id = user_email.id

    if user.pending_email_id == user_email.id:
        user.pending_email_id = None


def verify_pending_email(
    session: Session,
    user: User,
    pending_email: UserEmailAddress,
    email_token: EmailVerificationToken,
    now,
) -> None:
    pending_email.verified_at = now
    email_token.consumed_at = now
    set_primary_email(user=user, user_email=pending_email)
