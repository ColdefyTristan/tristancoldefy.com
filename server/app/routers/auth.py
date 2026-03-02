from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db import get_session
from app.models.tables import (
    User,
    UserEmailAddress,
    EmailVerificationToken,
)
from app.models.schemas import (
    RegisterRequest,
    LoginRequest,
    EmailTokenVerificationRequest,
)
from app.security import hash_password, verify_password, hmac_token
from app.deps import get_current_auth, AuthContext
from app.utils.time import utcnow_naive
from app.constants import LONG_SESSION_DAYS, SHORT_SESSION_DAYS
from app.services.auth.emails import (
    normalize_email,
    add_pending_email,
    verify_pending_email,
)
from app.services.auth.emails_verification import (
    create_email_verification_token,
    deliver_email_verification,
)
from app.services.auth.sessions import create_user_session
from app.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(
    payload: RegisterRequest,
    response: Response,
    session: Session = Depends(get_session),
):
    # check username unique
    existing = session.exec(
        select(User).where(User.username == payload.username)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "USERNAME_TAKEN",
                "message": "This username is already taken.",
                "fields": {"username": "already_taken"},
            },
        )

    stripped_email = (
        normalize_email(payload.email) if payload.email is not None else None
    )
    # check if mail is not None and unique
    if stripped_email:
        existing_email = session.exec(
            select(UserEmailAddress).where(
                UserEmailAddress.email == stripped_email,
                UserEmailAddress.verified_at.is_not(None),
            )
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "EMAIL_TAKEN",
                    "message": "This email address is already in use.",
                    "fields": {"email": "already_taken"},
                },
            )

    # create user
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    session.flush()

    if stripped_email:
        user_email = add_pending_email(
            session=session, user=user, email_str=stripped_email
        )
        email_token = create_email_verification_token(
            session=session, user=user, user_email=user_email
        )

    session_token = create_user_session(session, user.id, payload.remember_me)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "CONSTRAINT_VIOLATION",
                "message": "Request conflicts with existing data.",
                "fields": {},
            },
        )

    if stripped_email:
        deliver_email_verification(user_email=user_email, token=email_token)

    # 4) set cookie (HttpOnly)
    response.set_cookie(
        key="session_id",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        max_age=(LONG_SESSION_DAYS if payload.remember_me else SHORT_SESSION_DAYS)
        * 24
        * 60
        * 60,
        path="/",
    )

    return {"id": user.id, "username": user.username}


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    stmt = select(UserEmailAddress).where(
        (UserEmailAddress.verified_at.is_not(None))
        & (UserEmailAddress.email == normalize_email(payload.identifier))
    )
    identifier_email = session.exec(stmt).first()
    if identifier_email:
        stmt = select(User).where((User.id == identifier_email.user_id))
        user = session.exec(stmt).first()
    else:
        stmt = select(User).where((User.username == payload.identifier))
        user = session.exec(stmt).first()

    if (
        not user
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid identifier or password.",
                "fields": {"identifier": "invalid", "password": "invalid"},
            },
        )

    token = create_user_session(session, user.id, payload.remember_me)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SESSION_CONFLICT",
                "message": "Could not create session. Please retry.",
                "fields": {},
            },
        )

    response.set_cookie(
        key="session_id",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  ########### mettre true en prod
        max_age=(LONG_SESSION_DAYS if payload.remember_me else SHORT_SESSION_DAYS)
        * 24
        * 60
        * 60,
        path="/",
    )

    return {"ok": True, "user": {"id": user.id, "username": user.username}}


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    current_auth: AuthContext = Depends(get_current_auth),
    session: Session = Depends(get_session),
):

    current_auth.user_session.revoked_at = utcnow_naive()

    session.add(current_auth.user_session)

    response.delete_cookie("session_id", path="/")

    session.commit()


@router.get("/me")
def me(
    current_auth: AuthContext = Depends(get_current_auth),
    session: Session = Depends(get_session),
):
    user = current_auth.user

    primary_email = None
    if user.primary_email_id is not None:
        primary = session.exec(
            select(UserEmailAddress).where(
                UserEmailAddress.id == user.primary_email_id,
                UserEmailAddress.verified_at.is_not(None),
            )
        ).first()
        primary_email = primary.email if primary else None

    pending = session.exec(
        select(UserEmailAddress).where(
            UserEmailAddress.user_id == user.id,
            UserEmailAddress.verified_at.is_(None),
            UserEmailAddress.is_active.is_(True),
        )
    ).first()

    return {
        "id": user.id,
        "username": user.username,
        "email": {
            "primary": primary_email,
            "pending": pending.email if pending else None,
            "verification_sent_at": pending.verification_sent_at if pending else None,
        },
    }


@router.post("/email/verification/send")
def send_email_verification_endpoint(
    current_auth: AuthContext = Depends(get_current_auth),
    session: Session = Depends(get_session),
):

    user = current_auth.user
    if not user.pending_email_id:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "PENDING_EMAIL_MISSING",
                "message": "No pending email address to verify.",
                "fields": {"pending_email": "missing"},
            },
        )

    pending_email = session.get(UserEmailAddress, user.pending_email_id)
    if not pending_email or pending_email.user_id != user.id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PENDING_EMAIL_CONFLICT",
                "message": "Pending email does not match the current user.",
                "fields": {"pending_email_id": "conflict"},
            },
        )

    token = create_email_verification_token(
        session=session, user_email=pending_email, user=user
    )
    session.commit()
    result = deliver_email_verification(email=pending_email.email, token=token)
    return {"ok": True, "sent_at": result.sent_at, "expires_at": result.expires_at}


@router.post("/email/verification/verify")
def verify_email_verification_token_endpoint(
    payload: EmailTokenVerificationRequest,
    session: Session = Depends(get_session),
):
    now = utcnow_naive()

    hashed_token = hmac_token(payload.token, settings.EMAIL_TOKEN_SECRET)

    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token_hash == hashed_token,
        EmailVerificationToken.consumed_at.is_(None),
        EmailVerificationToken.revoked_at.is_(None),
        EmailVerificationToken.expires_at > now,
    )

    email_token = session.exec(stmt).first()

    if email_token is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "EMAIL_TOKEN_INVALID",
                "message": "Invalid or expired verification token.",
                "fields": {"token": "invalid"},
            },
        )

    pending_email = session.get(UserEmailAddress, email_token.email_id)
    # no email associated with token
    if not pending_email:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "EMAIL_TOKEN_INVALID",
                "message": "Invalid or expired verification token.",
                "fields": {"token": "invalid"},
            },
        )
    user = session.get(User, pending_email.user_id)
    # no user associated with mail
    if not user or user.pending_email_id != email_token.email_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "EMAIL_TOKEN_INVALID",
                "message": "Invalid or expired verification token.",
                "fields": {"token": "invalid"},
            },
        )

    try:
        verify_pending_email(
            session=session,
            user=user,
            pending_email=pending_email,
            email_token=email_token,
            now=now,
        )
        session.commit()
    except:
        session.rollback()
        raise

    return {"ok": True}
