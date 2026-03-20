from datetime import date
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.familledle.familledle_attempt import FamilledleAttempt


def get_attempt_for_user_by_day(
    session: Session, *, user_id: int, day: date
) -> FamilledleAttempt | None:
    stmt = (
        select(FamilledleAttempt)
        .where(FamilledleAttempt.user_id == user_id, FamilledleAttempt.day == day)
        .options(selectinload(FamilledleAttempt.guesses))  # load guesses in one go
    )
    return session.exec(stmt).first()


def list_attempts_for_user(
    session: Session, *, user_id: int, limit: int = 30, offset: int = 0
) -> list[FamilledleAttempt]:
    stmt = (
        select(FamilledleAttempt)
        .where(FamilledleAttempt.user_id == user_id)
        .order_by(FamilledleAttempt.day.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(stmt).all())


def attempt_to_day_out(attempt: FamilledleAttempt):
    # sécurité: forcer l'ordre en DB (position) au cas où la relation ne respecte pas l’ordre
    champions = [
        g.champion_name for g in sorted(attempt.guesses, key=lambda x: x.position)
    ]
    return {
        "day": attempt.day,
        "is_finished": attempt.finished_at is not None,
        "champions": champions,
    }
