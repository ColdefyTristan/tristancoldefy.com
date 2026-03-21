from sqlmodel import Session, select

from app.models.mtg.mtg_deck import Deck
from app.services.mtg.exceptions import DeckNotFound, DeckAccessForbidden


def get_deck(session: Session, deck_id: int, user_id: int) -> Deck:
    deck = session.get(Deck, deck_id)
    if deck is None:
        raise DeckNotFound()
    if deck.user_id != user_id:
        raise DeckAccessForbidden()
    return deck


def rename_deck(session: Session, deck: Deck, name: str) -> None:
    deck.name = name
    session.add(deck)
