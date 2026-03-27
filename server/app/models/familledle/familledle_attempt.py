from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import JSONB

from app.models.tables import User
from app.models.familledle.champ_data import ChampData
from app.models.familledle.schemas import ClueType
from app.utils.time import utcnow_naive, today_paris_date


class FamilledleAttempt(SQLModel, table=True):
    __tablename__ = "familledle_attempt"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_familledle_attempt_user_day"),
        Index("ix_familledle_attempt_user_day", "user_id", "day"),
        Index("ix_familledle_attempt_day", "day"),
    )

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    day: date = Field(default_factory=today_paris_date)

    created_at: datetime = Field(default_factory=utcnow_naive)
    finished_at: datetime | None = None

    try_count: int = Field(default=0, ge=0)

    clues: list[ClueType] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=text("'[]'")),
    )
    clue_points: int = Field(default=0, ge=0, le=3)

    guesses: list["FamilledleAttemptGuess"] = Relationship(back_populates="attempt")
    user: "User" = Relationship()


class FamilledleAttemptGuess(SQLModel, table=True):
    __tablename__ = "familledle_attempt_guess"
    __table_args__ = (
        UniqueConstraint("attempt_id", "position", name="uq_attempt_guess_position"),
        Index("ix_attempt_guess_attempt_pos", "attempt_id", "position"),
    )

    id: int | None = Field(default=None, primary_key=True)

    attempt_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("familledle_attempt.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    position: int = Field(ge=0)

    champion_name: str = Field(
        sa_column=Column(
            ForeignKey("champ_data.name", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    created_at: datetime = Field(default_factory=utcnow_naive)

    attempt: FamilledleAttempt = Relationship(back_populates="guesses")
    champion: "ChampData" = Relationship()
