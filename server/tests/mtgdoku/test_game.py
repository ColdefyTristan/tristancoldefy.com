"""Tests d'intégration pour les routes de jeu MTGDoku (guess, check, attempt)."""
import pytest

from app.models.mtg.mtgdoku_attempt import MtgDokuAttempt, MtgDokuAttemptGuess
from app.models.mtg.mtgdoku_grid import MtgDokuDailyGame
from sqlmodel import select


# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------

CREATURE_WHITE_GRID = {
    "score": 10.0,
    "difficulty": {"label": "medium", "score": 400},
    "min_known": 10,
    "min_total": 12,
    "rows": [
        {"conditions": [{"id": "c=w", "label": "White only", "weight": 0.9, "total": 300, "known": 250}], "total": 300, "known": 250},
        {"conditions": [{"id": "type=creature", "label": "Creature", "weight": 1.0, "total": 1000, "known": 800}], "total": 1000, "known": 800},
        {"conditions": [{"id": "cmc=2", "label": "CMC 2", "weight": 0.8, "total": 500, "known": 400}], "total": 500, "known": 400},
    ],
    "cols": [
        {"conditions": [{"id": "type=legendary", "label": "Legendary", "weight": 0.7, "total": 600, "known": 480}], "total": 600, "known": 480},
        {"conditions": [{"id": 'o:"flying"', "label": "Flying", "weight": 0.8, "total": 400, "known": 320}], "total": 400, "known": 320},
        {"conditions": [{"id": 'o:"lifelink"', "label": "Lifelink", "weight": 0.5, "total": 150, "known": 100}], "total": 150, "known": 100},
    ],
    "cells": [
        [{"total": 20, "known": 15}, {"total": 30, "known": 22}, {"total": 10, "known": 8}],
        [{"total": 50, "known": 40}, {"total": 60, "known": 50}, {"total": 25, "known": 20}],
        [{"total": 15, "known": 12}, {"total": 20, "known": 16}, {"total": 8, "known": 6}],
    ],
}


@pytest.fixture
def game_with_grid(session, grid_factory, daily_game_factory):
    """Partie du jour avec une grille medium dont les conditions sont vérifiables en test."""
    grid = grid_factory(difficulty="medium", grid_data=CREATURE_WHITE_GRID)
    easy_grid = grid_factory(difficulty="easy")
    hard_grid = grid_factory(difficulty="hard")
    game = daily_game_factory(easy_grid=easy_grid, medium_grid=grid, hard_grid=hard_grid)
    return game, grid


@pytest.fixture
def white_creature_card(card_factory):
    """Carte blanche créature légendaire avec flying et lifelink, CMC 2."""
    return card_factory(
        name="Serra Angel",
        colors=["W"],
        color_identity=["W"],
        type_line="Legendary Creature — Angel",
        oracle_text="Flying. Lifelink.",
        converted_mana_cost=2,
    )


@pytest.fixture
def blue_card(card_factory):
    """Carte bleue — ne remplit pas les conditions White only."""
    return card_factory(
        name="Counterspell",
        colors=["U"],
        color_identity=["U"],
        type_line="Instant",
        oracle_text="Counter target spell.",
        converted_mana_cost=2,
    )


# ---------------------------------------------------------------------------
# GET /mtgdoku/check
# ---------------------------------------------------------------------------

def test_check_valid_card_for_cell(client, game_with_grid, white_creature_card):
    _, grid = game_with_grid
    # cell (0,0) = White only + Legendary
    r = client.get("/mtgdoku/check", params={
        "grid_id": grid.id,
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert r.status_code == 200
    assert r.json()["is_valid"] is True
    assert r.json()["card_name"] == "Serra Angel"


def test_check_invalid_card_for_cell(client, game_with_grid, blue_card):
    _, grid = game_with_grid
    # cell (0,0) = White only + Legendary — blue card should fail
    r = client.get("/mtgdoku/check", params={
        "grid_id": grid.id,
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    assert r.status_code == 200
    assert r.json()["is_valid"] is False


def test_check_unknown_grid_returns_404(client, white_creature_card):
    r = client.get("/mtgdoku/check", params={
        "grid_id": 99999,
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /mtgdoku/daily/guess — anonyme
# ---------------------------------------------------------------------------

def test_anonymous_guess_valid_card(client, game_with_grid, white_creature_card):
    r = client.post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["is_valid"] is True
    assert data["attempt"] is None


def test_anonymous_guess_invalid_card(client, game_with_grid, blue_card):
    r = client.post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    assert r.status_code == 200
    assert r.json()["is_valid"] is False
    assert r.json()["attempt"] is None


def test_anonymous_guess_does_not_create_attempt(session, client, game_with_grid, white_creature_card):
    client.post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert session.exec(select(MtgDokuAttempt)).first() is None


def test_anonymous_guess_unknown_card_returns_404(client, game_with_grid):
    r = client.post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": "00000000-0000-0000-0000-000000000000",
    })
    assert r.status_code == 404


def test_anonymous_guess_no_daily_game_returns_404(client, white_creature_card):
    r = client.post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /mtgdoku/daily/guess — authentifié
# ---------------------------------------------------------------------------

def test_authenticated_guess_creates_attempt(session, auth_client, game_with_grid, white_creature_card):
    ctx = auth_client()
    r = ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["attempt"] is not None
    assert data["attempt"]["won_medium"] is False

    attempt = session.exec(select(MtgDokuAttempt)).first()
    assert attempt is not None


def test_authenticated_valid_guess_is_stored(session, auth_client, game_with_grid, white_creature_card):
    ctx = auth_client()
    ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    guess = session.exec(select(MtgDokuAttemptGuess)).first()
    assert guess is not None
    assert guess.is_valid is True
    assert guess.cell_row == 0
    assert guess.cell_col == 0
    assert guess.difficulty == "medium"


def test_authenticated_invalid_guess_is_stored(session, auth_client, game_with_grid, blue_card):
    ctx = auth_client()
    ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium",
        "cell_row": 0,
        "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    guess = session.exec(select(MtgDokuAttemptGuess)).first()
    assert guess is not None
    assert guess.is_valid is False


def test_duplicate_card_in_same_cell_returns_409(auth_client, game_with_grid, blue_card):
    # blue_card est invalide → cellule non gagnée → déclenche CARD_ALREADY_TRIED
    ctx = auth_client()
    ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium", "cell_row": 0, "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    r = ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium", "cell_row": 0, "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    assert r.status_code == 409
    assert "CARD_ALREADY_TRIED" in r.json()["message"]


def test_won_cell_cannot_be_played_again(auth_client, game_with_grid, white_creature_card, blue_card):
    ctx = auth_client()
    # Valider la cellule (0,0)
    ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium", "cell_row": 0, "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    # Retenter sur la même cellule gagnée
    r = ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium", "cell_row": 0, "cell_col": 0,
        "oracle_id": blue_card.oracle_id,
    })
    assert r.status_code == 409
    assert "CELL_ALREADY_WON" in r.json()["message"]


def test_attempt_position_increments_across_difficulties(session, auth_client, game_with_grid, white_creature_card):
    ctx = auth_client()
    for diff in ("easy", "hard"):
        ctx["client"].post("/mtgdoku/daily/guess", json={
            "difficulty": diff, "cell_row": 0, "cell_col": 0,
            "oracle_id": white_creature_card.oracle_id,
        })
    guesses = session.exec(
        select(MtgDokuAttemptGuess).order_by(MtgDokuAttemptGuess.position)
    ).all()
    assert [g.position for g in guesses] == [0, 1]


# ---------------------------------------------------------------------------
# GET /mtgdoku/daily/attempt
# ---------------------------------------------------------------------------

def test_get_attempt_returns_401_without_auth(client, game_with_grid):
    r = client.get("/mtgdoku/daily/attempt")
    assert r.status_code == 401


def test_get_attempt_returns_404_when_no_attempt(auth_client, game_with_grid):
    ctx = auth_client()
    r = ctx["client"].get("/mtgdoku/daily/attempt")
    assert r.status_code == 404


def test_get_attempt_returns_attempt_after_guess(auth_client, game_with_grid, white_creature_card):
    ctx = auth_client()
    ctx["client"].post("/mtgdoku/daily/guess", json={
        "difficulty": "medium", "cell_row": 0, "cell_col": 0,
        "oracle_id": white_creature_card.oracle_id,
    })
    r = ctx["client"].get("/mtgdoku/daily/attempt")
    assert r.status_code == 200
    data = r.json()
    assert len(data["guesses"]) == 1
    assert data["guesses"][0]["card_name"] == "Serra Angel"
    assert data["guesses"][0]["is_valid"] is True
    assert data["finished_at"] is None
