from sqlmodel import Session

from app.models.mtg.mtg_deck import DeckEntry
from app.models.mtg.mtg_tag import TagDefinition, TagValueOption, DeckEntryTag
from app.services.mtg.exceptions import EntityNotFound


def add_card_tag(
    session: Session,
    deck_entry: DeckEntry,
    tag_def: TagDefinition,
    tag_value_option: TagValueOption,
    weight: int,
) -> DeckEntryTag:
    if tag_value_option.tag_definition_id != tag_def.id:
        raise EntityNotFound("tag_value_def")

    card_tag = DeckEntryTag(
        deck_entry_id=deck_entry.id,
        tag_definition_id=tag_def.id,
        tag_value_option_id=tag_value_option.id,
        weight=weight,
    )
    session.add(card_tag)
    session.flush()
    return card_tag


def remove_card_tag(session: Session, deck_entry_tag: DeckEntryTag) -> None:
    session.delete(deck_entry_tag)


def set_card_tag_value(
    session: Session,
    deck_entry_tag: DeckEntryTag,
    tag_value_option: TagValueOption,
) -> None:
    if tag_value_option.tag_definition_id != deck_entry_tag.tag_definition_id:
        raise EntityNotFound("tag_value_def")

    deck_entry_tag.tag_value_option_id = tag_value_option.id
    session.add(deck_entry_tag)


def set_card_tag_weight(
    session: Session, deck_entry_tag: DeckEntryTag, weight: int
) -> None:
    deck_entry_tag.weight = weight
    session.add(deck_entry_tag)
