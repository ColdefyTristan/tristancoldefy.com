from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

from app.models.tables import User
from app.utils.time import utcnow_naive, today_paris_date
from datetime import date


class MtgDokuAttempt(SQLModel, table=True):
    """Tentative quotidienne d'un joueur sur les 3 grilles MTGDoku."""

    __tablename__ = "mtgdoku_attempt"
    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_mtgdoku_attempt_user_day"),
        Index("ix_mtgdoku_attempt_user_day", "user_id", "day"),
        Index("ix_mtgdoku_attempt_day", "day"),
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

    won_easy: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )
    won_medium: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )
    won_hard: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )

    guesses: list["MtgDokuAttemptGuess"] = Relationship(
        back_populates="attempt",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    user: "User" = Relationship()


class MtgDokuAttemptGuess(SQLModel, table=True):
    """Une carte essayée dans une case d'une grille MTGDoku."""

    __tablename__ = "mtgdoku_attempt_guess"
    __table_args__ = (
        Index("ix_mtgdoku_guess_attempt_pos", "attempt_id", "position"),
    )

    id: int | None = Field(default=None, primary_key=True)

    attempt_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("mtgdoku_attempt.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    # Ordre chronologique de l'essai (toutes difficultés confondues)
    position: int = Field(sa_column=Column(Integer, nullable=False))

    # Quelle grille
    difficulty: str = Field(sa_column=Column(String(10), nullable=False))

    # Quelle case (0-2)
    cell_row: int = Field(sa_column=Column(SmallInteger, nullable=False))
    cell_col: int = Field(sa_column=Column(SmallInteger, nullable=False))

    # Carte essayée
    oracle_id: str = Field(
        sa_column=Column(
            String(36),
            ForeignKey("mtg_card.oracle_id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )

    is_valid: bool = Field(
        sa_column=Column(Boolean, nullable=False, server_default="false")
    )

    created_at: datetime = Field(default_factory=utcnow_naive)

    attempt: MtgDokuAttempt = Relationship(back_populates="guesses")
