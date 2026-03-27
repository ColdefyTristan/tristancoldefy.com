"""Integration tests for the mtgdoku API endpoints."""
import pytest

from app.services.mtg.doku_categories import ALL_CATEGORIES


# ---------------------------------------------------------------------------
# GET /mtgdoku/categories
# ---------------------------------------------------------------------------


def test_list_categories_returns_all(client):
    r = client.get("/mtgdoku/categories")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == len(ALL_CATEGORIES)


def test_list_categories_structure(client):
    r = client.get("/mtgdoku/categories")
    for cat in r.json():
        assert "id" in cat
        assert "label" in cat
        assert "group" in cat


# ---------------------------------------------------------------------------
# GET /mtgdoku/category-stats
# ---------------------------------------------------------------------------


def test_category_stats_returns_all(client):
    r = client.get("/mtgdoku/category-stats")
    assert r.status_code == 200
    assert len(r.json()) == len(ALL_CATEGORIES)


def test_category_stats_zero_when_no_cards(client):
    r = client.get("/mtgdoku/category-stats")
    for item in r.json():
        assert item["count"] == 0


def test_category_stats_exact_monocolor(client, card_factory):
    card_factory(colors=["W"], color_identity=["W"], converted_mana_cost=1)
    card_factory(colors=["U"], color_identity=["U"], converted_mana_cost=2)
    # Bicolor card — should NOT match c=w or c=u exact
    card_factory(colors=["W", "U"], color_identity=["W", "U"], converted_mana_cost=2)

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["c=w"] == 1
    assert by_id["c=u"] == 1
    assert by_id["c=wu"] == 1


def test_category_stats_colorless(client, card_factory):
    card_factory(colors=[], color_identity=[], type_line="Artifact")
    card_factory(colors=["W"], color_identity=["W"])

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["c=c"] == 1


def test_category_stats_atleast_color(client, card_factory):
    card_factory(colors=["W"], color_identity=["W"])
    card_factory(colors=["W", "U"], color_identity=["W", "U"])
    card_factory(colors=["U"], color_identity=["U"])

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["c>w"] == 2  # mono-W and WU
    assert by_id["c>u"] == 2  # mono-U and WU


def test_category_stats_cmc(client, card_factory):
    card_factory(converted_mana_cost=2)
    card_factory(converted_mana_cost=2)
    card_factory(converted_mana_cost=3)

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["cmc=2"] == 2
    assert by_id["cmc=3"] == 1
    assert by_id["cmc=1"] == 0


def test_category_stats_type(client, card_factory):
    card_factory(type_line="Creature — Human")
    card_factory(type_line="Legendary Creature — Dragon")
    card_factory(type_line="Instant")

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["type=creature"] == 2
    assert by_id["type=legendary"] == 1
    assert by_id["type=instant"] == 1
    assert by_id["type=enchantment"] == 0


def test_category_stats_power_toughness(client, card_factory):
    card_factory(type_line="Creature", power="3", toughness="2")
    card_factory(type_line="Creature", power="3", toughness="3")

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id["pow=3"] == 2
    assert by_id["tou=2"] == 1
    assert by_id["tou=3"] == 1
    assert by_id["pow=1"] == 0


def test_category_stats_keyword(client, card_factory):
    card_factory(oracle_text="Flying. When this enters, draw a card.")
    card_factory(oracle_text="Trample, haste.")
    card_factory(oracle_text="")

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id['o:"flying"'] == 1
    assert by_id['o:"trample"'] == 1
    assert by_id['o:"haste"'] == 1
    assert by_id['o:"reach"'] == 0


def test_category_stats_mention(client, card_factory):
    card_factory(oracle_text="Exile target creature.")
    card_factory(oracle_text="Put a +1/+1 counter on target creature.")
    card_factory(oracle_text="Discard a card, then draw a card.")

    r = client.get("/mtgdoku/category-stats")
    by_id = {d["id"]: d["count"] for d in r.json()}

    assert by_id['o:"exile"'] == 1
    assert by_id['o:"+1/+1"'] == 1
    assert by_id['o:"discard"'] == 1
    assert by_id['o:"sacrifice"'] == 0


# ---------------------------------------------------------------------------
# GET /mtgdoku/pair-count
# ---------------------------------------------------------------------------


def test_pair_count_unknown_category(client):
    r = client.get("/mtgdoku/pair-count", params={"cat1": "c=w", "cat2": "unknown"})
    assert r.status_code == 200
    assert r.json()["error"] == "unknown_category"


def test_pair_count_both_unknown(client):
    r = client.get("/mtgdoku/pair-count", params={"cat1": "bad1", "cat2": "bad2"})
    assert "error" in r.json()


def test_pair_count_zero_when_no_cards(client):
    r = client.get("/mtgdoku/pair-count", params={"cat1": "c=w", "cat2": "type=creature"})
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_pair_count_correct_intersection(client, card_factory):
    # White creature
    card_factory(colors=["W"], color_identity=["W"], type_line="Creature — Human", power="2", toughness="2")
    # White enchantment (not a creature)
    card_factory(colors=["W"], color_identity=["W"], type_line="Enchantment — Aura")
    # Blue creature (not white)
    card_factory(colors=["U"], color_identity=["U"], type_line="Creature — Merfolk", power="1", toughness="1")

    r = client.get("/mtgdoku/pair-count", params={"cat1": "c=w", "cat2": "type=creature"})
    assert r.status_code == 200
    data = r.json()
    assert data["cat1"] == "c=w"
    assert data["cat2"] == "type=creature"
    assert data["count"] == 1


def test_pair_count_cmc_and_keyword(client, card_factory):
    card_factory(converted_mana_cost=2, oracle_text="Flying.")
    card_factory(converted_mana_cost=2, oracle_text="Trample.")
    card_factory(converted_mana_cost=3, oracle_text="Flying.")

    r = client.get("/mtgdoku/pair-count", params={"cat1": "cmc=2", "cat2": 'o:"flying"'})
    assert r.json()["count"] == 1


def test_pair_count_response_includes_both_ids(client):
    r = client.get("/mtgdoku/pair-count", params={"cat1": "cmc=1", "cat2": "type=instant"})
    data = r.json()
    assert data["cat1"] == "cmc=1"
    assert data["cat2"] == "type=instant"
