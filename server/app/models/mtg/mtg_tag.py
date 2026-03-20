from typing import TYPE_CHECKING, Optional
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

from app.utils.time import utcnow_naive
from app.models.mtg.enums import TagKind, TagValueKind, TagSourceKind

if TYPE_CHECKING:
    from app.models.mtg.mtg_deck import Deck, DeckEntry


class TagDefinition(SQLModel, table=True):
    __tablename__ = "tag_definition"

    id: int | None = Field(default=None, primary_key=True)

    deck_id: int | None = Field(default=None, foreign_key="deck.id", index=True)

    name: str = Field(max_length=120, index=True)
    tag_kind: TagKind = Field(index=True)
    value_kind: TagValueKind = Field(default=TagValueKind.NONE)

    has_rate: bool = Field(default=False)
    minimum_per_entry: int = Field(default=0, ge=0)

    created_at: datetime = Field(default_factory=utcnow_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow_naive, nullable=False)

    deck: Optional["Deck"] = Relationship(back_populates="tag_definitions")
    value_options: list["TagValueOption"] = Relationship(
        back_populates="tag_definition"
    )
    deck_entry_tags: list["DeckEntryTag"] = Relationship(
        back_populates="tag_definition"
    )


class TagValueOption(SQLModel, table=True):
    __tablename__ = "tag_value_option"
    __table_args__ = (
        UniqueConstraint(
            "tag_definition_id",
            "normalized_value",
            name="uq_tag_value_option_definition_normalized_value",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    tag_definition_id: int = Field(foreign_key="tag_definition.id", index=True)

    value: str = Field(max_length=120)
    normalized_value: str = Field(max_length=120, index=True)
    sort_order: int = Field(default=0)

    created_at: datetime = Field(default_factory=utcnow_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow_naive, nullable=False)

    tag_definition: "TagDefinition" = Relationship(back_populates="value_options")
    deck_entry_tags: list["DeckEntryTag"] = Relationship(
        back_populates="tag_value_option"
    )


class DeckEntryTag(SQLModel, table=True):
    __tablename__ = "deck_entry_tag"

    id: int | None = Field(default=None, primary_key=True)
    deck_entry_id: int = Field(foreign_key="deck_entry.id", index=True)
    tag_definition_id: int = Field(foreign_key="tag_definition.id", index=True)

    tag_value_option_id: int | None = Field(
        default=None,
        foreign_key="tag_value_option.id",
        index=True,
    )
    integer_value: int | None = Field(default=None)
    rate: int | None = Field(default=None, ge=0, le=10)

    source_kind: TagSourceKind = Field(default=TagSourceKind.USER)

    created_at: datetime = Field(default_factory=utcnow_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow_naive, nullable=False)

    deck_entry: "DeckEntry" = Relationship(back_populates="tags")
    tag_definition: "TagDefinition" = Relationship(back_populates="deck_entry_tags")
    tag_value_option: Optional["TagValueOption"] = Relationship(
        back_populates="deck_entry_tags"
    )
