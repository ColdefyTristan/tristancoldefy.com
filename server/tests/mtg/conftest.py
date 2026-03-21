import uuid
import pytest

from app.models.mtg.mtg_deck import Deck
from app.models.mtg.mtg_card import MtgCard


@pytest.fixture
def deck_factory(session, user_factory):
    def create(user=None, version=1, **kwargs):
        if user is None:
            user = user_factory()
        deck = Deck(
            user_id=user.id,
            name=kwargs.get("name", f"deck_{uuid.uuid4().hex[:8]}"),
            version=version,
        )
        session.add(deck)
        session.commit()
        session.refresh(deck)
        return deck

    return create


@pytest.fixture
def mtg_card(session):
    card = MtgCard(
        oracle_id=str(uuid.uuid4()),
        name="Lightning Bolt",
        color_identity=["R"],
        converted_mana_cost=1,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card
