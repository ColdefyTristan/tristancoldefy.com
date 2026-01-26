import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models import UserEmailAddress
from app.utils.time import utcnow_naive


def test_duplicate_unverified_emails_are_allowed(session, user_factory):
    u1 = user_factory()
    u2 = user_factory()

    e1 = UserEmailAddress(user_id=u1.id, email="a@example.com", verified_at=None)
    e2 = UserEmailAddress(user_id=u2.id, email="a@example.com", verified_at=None)

    session.add_all([e1, e2])
    session.commit()
    rows = session.exec(
        select(UserEmailAddress).where(UserEmailAddress.email == "a@example.com")
    ).all()
    assert len(rows) == 2
    assert all(r.verified_at is None for r in rows)


def test_email_becomes_unique_once_verified(session, user_factory):
    u1 = user_factory()
    u2 = user_factory()

    e1 = UserEmailAddress(user_id=u1.id, email="b@example.com", verified_at=None)
    e2 = UserEmailAddress(user_id=u2.id, email="b@example.com", verified_at=None)

    session.add_all([e1, e2])
    session.commit()

    e1.verified_at = utcnow_naive()
    session.add(e1)
    session.commit()
    session.refresh(e1)
    assert e1.verified_at is not None

    e2.verified_at = utcnow_naive()
    session.add(e2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.refresh(e2)
    assert e2.verified_at is None
