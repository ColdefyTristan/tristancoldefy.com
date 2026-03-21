from sqlmodel import Session, select

from app.models.mtg.mtg_card import MtgCard
from app.models.mtg.mtg_deck import Deck, DeckEntry
from app.models.mtg.enums import DeckEntryZone
from app.services.mtg.exceptions import EntityNotFound


def _get_mtg_card(session: Session, oracle_card_id: str) -> MtgCard:
    card = session.exec(
        select(MtgCard).where(MtgCard.oracle_id == oracle_card_id)
    ).first()
    if card is None:
        raise EntityNotFound("card")
    return card


def add_card(
    session: Session,
    deck: Deck,
    oracle_card_id: str,
    zone: DeckEntryZone,
    quantity: int,
) -> DeckEntry:
    mtg_card = _get_mtg_card(session, oracle_card_id)

    existing = session.exec(
        select(DeckEntry).where(
            DeckEntry.deck_id == deck.id,
            DeckEntry.mtg_card_id == mtg_card.id,
            DeckEntry.zone == zone,
        )
    ).first()

    if existing is not None:
        existing.quantity += quantity
        session.add(existing)
        return existing

    entry = DeckEntry(
        deck_id=deck.id,
        mtg_card_id=mtg_card.id,
        zone=zone,
        quantity=quantity,
    )
    session.add(entry)
    session.flush()  # populate entry.id
    return entry


def remove_card(session: Session, deck_entry: DeckEntry) -> None:
    session.delete(deck_entry)


def move_card_to_zone(session: Session, deck_entry: DeckEntry, zone: DeckEntryZone) -> None:
    deck_entry.zone = zone
    session.add(deck_entry)


def set_card_quantity(session: Session, deck_entry: DeckEntry, quantity: int) -> None:
    deck_entry.quantity = quantity
    session.add(deck_entry)
