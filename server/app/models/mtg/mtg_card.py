from sqlmodel import SQLModel, Field
from sqlalchemy import (
    Column,
    UniqueConstraint,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY


class MtgCard(SQLModel, table=True):
    __tablename__ = "mtg_card"
    __table_args__ = (
        UniqueConstraint("oracle_id", name="uq_mtg_card_oracle_id"),
        Index("ix_mtg_card_name", "name"),
    )

    id: int | None = Field(default=None, primary_key=True)

    oracle_id: str = Field(sa_column=Column(String(36), nullable=False))

    name: str = Field(sa_column=Column(Text, nullable=False))

    image_url_small: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    image_url_medium: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    color_identity: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String(1)), nullable=False)
    )

    colors: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String(1)), nullable=False)
    )

    converted_mana_cost: int = Field(default=0, nullable=False)

    type_line: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    oracle_text: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    power: str | None = Field(default=None, sa_column=Column(String(10), nullable=True))

    toughness: str | None = Field(default=None, sa_column=Column(String(10), nullable=True))

    edhrec_rank: int | None = Field(default=None, nullable=True)
