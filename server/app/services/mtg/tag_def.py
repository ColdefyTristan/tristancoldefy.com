from sqlmodel import Session, select

from app.models.mtg.mtg_deck import Deck
from app.models.mtg.mtg_tag import TagDefinition, TagValueOption, DeckEntryTag
from app.models.mtg.enums import TagKind, TagValueKind
from app.services.mtg.exceptions import (
    ImmutableTagDef,
    TagDefHasDependencies,
    TagValueDefHasDependencies,
    DuplicateTagValue,
)


def _assert_mutable(tag_def: TagDefinition) -> None:
    if tag_def.deck_id is None:
        raise ImmutableTagDef()


def create_tag_def(session: Session, deck: Deck, name: str) -> TagDefinition:
    tag_def = TagDefinition(
        deck_id=deck.id,
        name=name,
        tag_kind=TagKind.USER_ONLY,
        value_kind=TagValueKind.OPTION,
    )
    session.add(tag_def)
    session.flush()
    return tag_def


def remove_tag_def(session: Session, tag_def: TagDefinition) -> None:
    _assert_mutable(tag_def)

    has_values = session.exec(
        select(TagValueOption).where(TagValueOption.tag_definition_id == tag_def.id).limit(1)
    ).first()
    if has_values:
        raise TagDefHasDependencies()

    has_card_tags = session.exec(
        select(DeckEntryTag).where(DeckEntryTag.tag_definition_id == tag_def.id).limit(1)
    ).first()
    if has_card_tags:
        raise TagDefHasDependencies()

    session.delete(tag_def)


def rename_tag_def(session: Session, tag_def: TagDefinition, name: str) -> None:
    _assert_mutable(tag_def)
    tag_def.name = name
    session.add(tag_def)


def add_tag_value_def(
    session: Session, tag_def: TagDefinition, value: str, weight: int
) -> TagValueOption:
    _assert_mutable(tag_def)

    normalized = value.strip().lower()
    existing = session.exec(
        select(TagValueOption).where(
            TagValueOption.tag_definition_id == tag_def.id,
            TagValueOption.normalized_value == normalized,
        )
    ).first()
    if existing is not None:
        raise DuplicateTagValue()

    option = TagValueOption(
        tag_definition_id=tag_def.id,
        value=value.strip(),
        normalized_value=normalized,
        weight=weight,
    )
    session.add(option)
    session.flush()
    return option


def remove_tag_value_def(session: Session, tag_value_option: TagValueOption) -> None:
    tag_def = session.get(TagDefinition, tag_value_option.tag_definition_id)
    if tag_def:
        _assert_mutable(tag_def)

    has_card_tags = session.exec(
        select(DeckEntryTag)
        .where(DeckEntryTag.tag_value_option_id == tag_value_option.id)
        .limit(1)
    ).first()
    if has_card_tags:
        raise TagValueDefHasDependencies()

    session.delete(tag_value_option)


def rename_tag_value_def(
    session: Session, tag_value_option: TagValueOption, value: str
) -> None:
    tag_def = session.get(TagDefinition, tag_value_option.tag_definition_id)
    if tag_def:
        _assert_mutable(tag_def)

    tag_value_option.value = value.strip()
    tag_value_option.normalized_value = value.strip().lower()
    session.add(tag_value_option)


def set_tag_value_def_weight(
    session: Session, tag_value_option: TagValueOption, weight: int
) -> None:
    tag_def = session.get(TagDefinition, tag_value_option.tag_definition_id)
    if tag_def:
        _assert_mutable(tag_def)

    tag_value_option.weight = weight
    session.add(tag_value_option)
