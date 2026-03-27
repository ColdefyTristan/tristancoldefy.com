from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


class MtgDokuGrid(SQLModel, table=True):
    """Une grille 3×3 MTGDoku pré-calculée."""

    __tablename__ = "mtgdoku_grid"

    id: int | None = Field(default=None, primary_key=True)

    difficulty: str = Field(sa_column=Column(String(10), nullable=False, index=True))
    score: float = Field()
    difficulty_score: float = Field()

    # Hash md5 du contenu (rows + cols + cells) — garantit l'unicité réelle de la grille
    content_hash: str = Field(sa_column=Column(String(32), nullable=False, unique=True))

    # Données complètes de la grille (rows, cols, cells, conditions…)
    grid_data: dict = Field(
        sa_column=Column(JSONB, nullable=False),
    )


class MtgDokuDailyGame(SQLModel, table=True):
    """Partie quotidienne MTGDoku : une grille par difficulté."""

    __tablename__ = "mtgdoku_daily_game"
    __table_args__ = (UniqueConstraint("day", name="uq_mtgdoku_daily_game_day"),)

    id: int | None = Field(default=None, primary_key=True)

    day: date = Field(sa_column=Column(Date, nullable=False, unique=True, index=True))

    easy_grid_id: int | None = Field(
        sa_column=Column(Integer, ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True)
    )
    medium_grid_id: int | None = Field(
        sa_column=Column(Integer, ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True)
    )
    hard_grid_id: int | None = Field(
        sa_column=Column(Integer, ForeignKey("mtgdoku_grid.id", ondelete="SET NULL"), nullable=True)
    )

    easy_grid: MtgDokuGrid | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[MtgDokuDailyGame.easy_grid_id]"}
    )
    medium_grid: MtgDokuGrid | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[MtgDokuDailyGame.medium_grid_id]"}
    )
    hard_grid: MtgDokuGrid | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[MtgDokuDailyGame.hard_grid_id]"}
    )
