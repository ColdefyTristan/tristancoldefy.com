from datetime import date
from enum import StrEnum

from sqlalchemy import Column, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class RowColumn(StrEnum):
    skin_number = "skin_number"
    family_mastery = "family_mastery"
    colorwheel = "colorwheel"
    mobility = "mobility"
    randomness = "randomness"
    cc_quantity = "cc_quantity"
    intension = "intension"
    vote = "vote"
    regime = "regime"
    pilosite = "pilosite"


ALL_ROW_COLUMNS: list[RowColumn] = list(RowColumn)


class RiftdleDailyGame(SQLModel, table=True):
    __tablename__ = "riftdle_daily_game"
    __table_args__ = (UniqueConstraint("day", name="uq_riftdle_daily_game_day"),)

    id: int | None = Field(default=None, primary_key=True)

    day: date = Field(sa_column=Column(Date, nullable=False, unique=True, index=True))

    champ_name: str = Field(foreign_key="champ_data.name", nullable=False)

    row_columns: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )

    winner_count: int = Field(default=0, ge=0)
