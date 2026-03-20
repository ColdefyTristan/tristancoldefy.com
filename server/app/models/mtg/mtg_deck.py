from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from app.utils.time import utcnow_naive
from app.models.mtg.enums import DeckEntryZone

if TYPE_CHECKING:
    from app.models.mtg.mtg_tag import TagDefinition, DeckEntryTag


class Deck(SQLModel, table=True):
    __tablename__ = "deck"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_deck_user_id_name"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(max_length=120, index=True)

    created_at: datetime = Field(default_factory=utcnow_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow_naive, nullable=False)

    deck_entries: list["DeckEntry"] = Relationship(back_populates="deck")
    tag_definitions: list["TagDefinition"] = Relationship(back_populates="deck")


class DeckEntry(SQLModel, table=True):
    __tablename__ = "deck_entry"
    __table_args__ = (
        UniqueConstraint(
            "deck_id",
            "mtg_card_id",
            "zone",
            name="uq_deck_entry_deck_card_zone",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    deck_id: int = Field(foreign_key="deck.id", index=True)
    mtg_card_id: int = Field(foreign_key="mtg_card.id", index=True)
    quantity: int = Field(default=1, ge=1)
    zone: DeckEntryZone = Field(default=DeckEntryZone.MAINBOARD)

    created_at: datetime = Field(default_factory=utcnow_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow_naive, nullable=False)

    deck: "Deck" = Relationship(back_populates="deck_entries")
    tags: list["DeckEntryTag"] = Relationship(back_populates="deck_entry")
