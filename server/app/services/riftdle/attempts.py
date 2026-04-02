from datetime import date
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.riftdle.riftdle_attempt import RiftdleAttempt


def get_attempt_for_user_by_day(
    session: Session, *, user_id: int, day: date
) -> RiftdleAttempt | None:
    stmt = (
        select(RiftdleAttempt)
        .where(RiftdleAttempt.user_id == user_id, RiftdleAttempt.day == day)
        .options(selectinload(RiftdleAttempt.guesses))  # load guesses in one go
    )
    return session.exec(stmt).first()


def list_attempts_for_user(
    session: Session, *, user_id: int, limit: int = 30, offset: int = 0
) -> list[RiftdleAttempt]:
    stmt = (
        select(RiftdleAttempt)
        .where(RiftdleAttempt.user_id == user_id)
        .order_by(RiftdleAttempt.day.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())


def attempt_to_day_out(attempt: RiftdleAttempt):
    # sécurité: forcer l’ordre en DB (position) au cas où la relation ne respecte pas l’ordre
    champions = [
        g.champion_name for g in sorted(attempt.guesses, key=lambda x: x.position)
    ]
    return {
        "day": attempt.day,
        "is_finished": attempt.finished_at is not None,
        "champions": champions,
        "clues": attempt.clues,
        "clue_points": attempt.clue_points,
    }
