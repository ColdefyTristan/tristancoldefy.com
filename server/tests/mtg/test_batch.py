import uuid
import pytest

from sqlmodel import select

from app.models.mtg.mtg_deck import Deck, DeckEntry, DeckBatchResult
from app.models.mtg.mtg_tag import TagDefinition, TagValueOption, DeckEntryTag
from app.models.mtg.enums import TagKind, TagValueKind


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

URL = "/decks/{deck_id}/apply-operations"


def batch(deck_id, operations, base_version=1, batch_id=None):
    return (
        URL.format(deck_id=deck_id),
        {
            "batch_id": batch_id or f"batch_{uuid.uuid4().hex}",
            "base_version": base_version,
            "operations": operations,
        },
    )


def rename_deck_op(name="Renamed"):
    return {"type": "rename_deck", "operation_id": "op_001", "name": name}


def add_card_op(oracle_card_id, local_id="local_card_1", zone="mainboard", quantity=1):
    return {
        "type": "add_card",
        "operation_id": "op_add_card",
        "card_local_id": local_id,
        "oracle_card_id": oracle_card_id,
        "zone": zone,
        "quantity": quantity,
    }


# ---------------------------------------------------------------------------
# Auth & access control
# ---------------------------------------------------------------------------


def test_batch_requires_auth(client, deck_factory):
    deck = deck_factory()
    url, payload = batch(deck.id, [rename_deck_op()])
    r = client.post(url, json=payload)
    assert r.status_code == 401


def test_batch_returns_403_for_wrong_user(client, auth_client, deck_factory):
    owner = auth_client()
    other = auth_client()

    deck = deck_factory(user=owner["user"])
    url, payload = batch(deck.id, [rename_deck_op()])

    other["client"].post("/auth/login")
    r = other["client"].post(url, json=payload)
    assert r.status_code == 403
    assert r.json()["error"] == "forbidden_deck_access"


def test_batch_returns_404_for_unknown_deck(auth_client):
    ac = auth_client()
    url, payload = batch(999999, [rename_deck_op()])
    r = ac["client"].post(url, json=payload)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Version conflict
# ---------------------------------------------------------------------------


def test_batch_returns_409_on_version_conflict(auth_client, deck_factory):
    ac = auth_client()
    deck = deck_factory(user=ac["user"], version=5)
    url, payload = batch(deck.id, [rename_deck_op()], base_version=3)
    r = ac["client"].post(url, json=payload)
    assert r.status_code == 409
    assert r.json()["error"] == "conflict_version"


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


def test_batch_rejects_empty_operations(auth_client, deck_factory):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    url = URL.format(deck_id=deck.id)
    r = ac["client"].post(url, json={"batch_id": "b1", "base_version": 1, "operations": []})
    assert r.status_code == 422


def test_batch_rejects_duplicate_operation_ids(auth_client, deck_factory):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    url, payload = batch(deck.id, [rename_deck_op(), rename_deck_op()])
    r = ac["client"].post(url, json=payload)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Version increment & rename_deck
# ---------------------------------------------------------------------------


def test_batch_increments_deck_version(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    url, payload = batch(deck.id, [rename_deck_op("My Deck")])
    r = ac["client"].post(url, json=payload)
    assert r.status_code == 200
    assert r.json()["new_version"] == 2

    session.refresh(deck)
    assert deck.version == 2


def test_rename_deck(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    url, payload = batch(deck.id, [rename_deck_op("Renamed Deck")])
    ac["client"].post(url, json=payload)

    session.refresh(deck)
    assert deck.name == "Renamed Deck"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_batch_idempotent_replay(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    bid = f"batch_{uuid.uuid4().hex}"
    url, payload = batch(deck.id, [rename_deck_op("First Apply")], batch_id=bid)

    r1 = ac["client"].post(url, json=payload)
    assert r1.status_code == 200

    # Second submission with same batch_id must not reapply
    r2 = ac["client"].post(url, json=payload)
    assert r2.status_code == 200
    assert r2.json() == r1.json()

    session.refresh(deck)
    assert deck.version == 2  # incremented only once


# ---------------------------------------------------------------------------
# Card operations
# ---------------------------------------------------------------------------


def test_add_card_creates_deck_entry(auth_client, deck_factory, mtg_card, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])
    url, payload = batch(deck.id, [add_card_op(mtg_card.oracle_id)])

    r = ac["client"].post(url, json=payload)
    assert r.status_code == 200

    mappings = r.json()["local_to_server_mappings"]["cards"]
    assert len(mappings) == 1
    assert mappings[0]["local_id"] == "local_card_1"

    entry = session.get(DeckEntry, mappings[0]["server_id"])
    assert entry is not None
    assert entry.quantity == 1
    assert entry.zone.value == "mainboard"


def test_add_card_increments_quantity_on_duplicate(auth_client, deck_factory, mtg_card, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    # First batch: add 2 copies
    url, p1 = batch(deck.id, [add_card_op(mtg_card.oracle_id, quantity=2)])
    r1 = ac["client"].post(url, json=p1)
    server_id = r1.json()["local_to_server_mappings"]["cards"][0]["server_id"]

    # Second batch: add 3 more copies of the same card in the same zone
    url, p2 = batch(deck.id, [add_card_op(mtg_card.oracle_id, quantity=3)], base_version=2)
    ac["client"].post(url, json=p2)

    session.refresh(session.get(DeckEntry, server_id))
    entry = session.get(DeckEntry, server_id)
    assert entry.quantity == 5


def test_remove_card(auth_client, deck_factory, mtg_card, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, p1 = batch(deck.id, [add_card_op(mtg_card.oracle_id)])
    r1 = ac["client"].post(url, json=p1)
    server_id = r1.json()["local_to_server_mappings"]["cards"][0]["server_id"]

    url, p2 = batch(
        deck.id,
        [{"type": "remove_card", "operation_id": "op_rm", "card_ref": {"server_id": server_id}}],
        base_version=2,
    )
    ac["client"].post(url, json=p2)

    assert session.get(DeckEntry, server_id) is None


def test_set_card_quantity(auth_client, deck_factory, mtg_card, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, p1 = batch(deck.id, [add_card_op(mtg_card.oracle_id)])
    r1 = ac["client"].post(url, json=p1)
    server_id = r1.json()["local_to_server_mappings"]["cards"][0]["server_id"]

    url, p2 = batch(
        deck.id,
        [{"type": "set_card_quantity", "operation_id": "op_qty", "card_ref": {"server_id": server_id}, "quantity": 4}],
        base_version=2,
    )
    ac["client"].post(url, json=p2)

    entry = session.get(DeckEntry, server_id)
    assert entry.quantity == 4


def test_move_card_to_zone(auth_client, deck_factory, mtg_card, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, p1 = batch(deck.id, [add_card_op(mtg_card.oracle_id, zone="mainboard")])
    r1 = ac["client"].post(url, json=p1)
    server_id = r1.json()["local_to_server_mappings"]["cards"][0]["server_id"]

    url, p2 = batch(
        deck.id,
        [{"type": "move_card_to_zone", "operation_id": "op_mv", "card_ref": {"server_id": server_id}, "zone": "sideboard"}],
        base_version=2,
    )
    ac["client"].post(url, json=p2)

    entry = session.get(DeckEntry, server_id)
    assert entry.zone.value == "sideboard"


# ---------------------------------------------------------------------------
# Tag definition operations
# ---------------------------------------------------------------------------


def test_create_and_rename_tag_def(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, p1 = batch(deck.id, [
        {"type": "create_tag_def", "operation_id": "op_ctd", "tag_def_local_id": "local_td_1", "name": "Archetype"},
    ])
    r1 = ac["client"].post(url, json=p1)
    td_id = r1.json()["local_to_server_mappings"]["tag_defs"][0]["server_id"]

    url, p2 = batch(
        deck.id,
        [{"type": "rename_tag_def", "operation_id": "op_rtd", "tag_def_ref": {"server_id": td_id}, "name": "Role"}],
        base_version=2,
    )
    ac["client"].post(url, json=p2)

    td = session.get(TagDefinition, td_id)
    assert td.name == "Role"


def test_remove_tag_def_fails_with_dependencies(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, p1 = batch(deck.id, [
        {"type": "create_tag_def", "operation_id": "op_ctd", "tag_def_local_id": "local_td_1", "name": "Archetype"},
        {"type": "add_tag_value_def", "operation_id": "op_tvd", "tag_def_ref": {"local_id": "local_td_1"},
         "tag_value_def_local_id": "local_tvd_1", "value": "Aggro", "weight": 7},
    ])
    r1 = ac["client"].post(url, json=p1)
    td_id = r1.json()["local_to_server_mappings"]["tag_defs"][0]["server_id"]

    url, p2 = batch(
        deck.id,
        [{"type": "remove_tag_def", "operation_id": "op_rm", "tag_def_ref": {"server_id": td_id}}],
        base_version=2,
    )
    r2 = ac["client"].post(url, json=p2)
    assert r2.status_code == 422
    assert r2.json()["operation_errors"][0]["code"] == "tag_def_has_dependencies"


def test_immutable_global_tag_def(auth_client, deck_factory, session):
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    # Create a global tag def (deck_id=None) directly in DB
    global_td = TagDefinition(
        deck_id=None,
        name="Global Tag",
        tag_kind=TagKind.STRATEGY,
        value_kind=TagValueKind.OPTION,
    )
    session.add(global_td)
    session.commit()
    session.refresh(global_td)

    url, payload = batch(
        deck.id,
        [{"type": "rename_tag_def", "operation_id": "op_rtd", "tag_def_ref": {"server_id": global_td.id}, "name": "Hacked"}],
    )
    r = ac["client"].post(url, json=payload)
    assert r.status_code == 422
    assert r.json()["operation_errors"][0]["code"] == "immutable_tag_def"


# ---------------------------------------------------------------------------
# Full intra-batch local_id chain
# ---------------------------------------------------------------------------


def test_full_local_id_chain(auth_client, deck_factory, mtg_card, session):
    """
    Single batch: add card → create tag def → add tag value def → add card tag.
    All using local_ids. Validates the full local_to_server_mappings response.
    """
    ac = auth_client()
    deck = deck_factory(user=ac["user"])

    url, payload = batch(deck.id, [
        {
            "type": "add_card",
            "operation_id": "op_1",
            "card_local_id": "local_card_1",
            "oracle_card_id": mtg_card.oracle_id,
            "zone": "mainboard",
            "quantity": 2,
        },
        {
            "type": "create_tag_def",
            "operation_id": "op_2",
            "tag_def_local_id": "local_td_1",
            "name": "Archetype",
        },
        {
            "type": "add_tag_value_def",
            "operation_id": "op_3",
            "tag_def_ref": {"local_id": "local_td_1"},
            "tag_value_def_local_id": "local_tvd_1",
            "value": "Aggro",
            "weight": 7,
        },
        {
            "type": "add_card_tag",
            "operation_id": "op_4",
            "card_ref": {"local_id": "local_card_1"},
            "card_tag_local_id": "local_ct_1",
            "tag_def_ref": {"local_id": "local_td_1"},
            "tag_value_def_ref": {"local_id": "local_tvd_1"},
            "weight": 8,
        },
    ])

    r = ac["client"].post(url, json=payload)
    assert r.status_code == 200

    body = r.json()
    mappings = body["local_to_server_mappings"]
    assert len(mappings["cards"]) == 1
    assert len(mappings["tag_defs"]) == 1
    assert len(mappings["tag_value_defs"]) == 1
    assert len(mappings["card_tags"]) == 1

    card_tag_id = mappings["card_tags"][0]["server_id"]
    ct = session.get(DeckEntryTag, card_tag_id)
    assert ct is not None
    assert ct.weight == 8
