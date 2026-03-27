import hashlib
import json
import uuid
import pytest

from app.models.mtg.mtg_card import MtgCard
from app.models.mtg.mtgdoku_grid import MtgDokuGrid, MtgDokuDailyGame
from app.models.mtg.mtgdoku_attempt import MtgDokuAttempt, MtgDokuAttemptGuess
from app.utils.time import today_paris_date


def _content_hash(grid_data: dict) -> str:
    payload = json.dumps(
        {"rows": grid_data["rows"], "cols": grid_data["cols"], "cells": grid_data["cells"]},
        sort_keys=True,
    )
    return hashlib.md5(payload.encode()).hexdigest()

SAMPLE_GRID_DATA = {
    "score": 12.5,
    "difficulty": {"label": "medium", "score": 450},
    "min_known": 42,
    "min_total": 50,
    "rows": [
        {"conditions": [{"id": "creature", "label": "Creature", "weight": 1.0, "total": 1000, "known": 800}], "total": 1000, "known": 800},
        {"conditions": [{"id": "white_only", "label": "White only", "weight": 0.9, "total": 300, "known": 250}], "total": 300, "known": 250},
        {"conditions": [{"id": "flying", "label": "Flying", "weight": 0.8, "total": 400, "known": 320}], "total": 400, "known": 320},
    ],
    "cols": [
        {"conditions": [{"id": "cmc_3", "label": "CMC 3", "weight": 0.8, "total": 500, "known": 420}], "total": 500, "known": 420},
        {"conditions": [{"id": "legendary", "label": "Legendary", "weight": 0.7, "total": 600, "known": 480}], "total": 600, "known": 480},
        {"conditions": [{"id": "lifelink", "label": "Lifelink", "weight": 0.5, "total": 150, "known": 100}], "total": 150, "known": 100},
    ],
    "cells": [
        [{"total": 80, "known": 65}, {"total": 90, "known": 72}, {"total": 42, "known": 35}],
        [{"total": 55, "known": 44}, {"total": 70, "known": 58}, {"total": 28, "known": 22}],
        [{"total": 60, "known": 50}, {"total": 65, "known": 52}, {"total": 30, "known": 24}],
    ],
}


@pytest.fixture
def card_factory(session):
    def create(**overrides):
        card = MtgCard(
            oracle_id=overrides.get("oracle_id", str(uuid.uuid4())),
            name=overrides.get("name", f"Test Card {uuid.uuid4().hex[:6]}"),
            color_identity=overrides.get("color_identity", []),
            colors=overrides.get("colors", []),
            converted_mana_cost=overrides.get("converted_mana_cost", 0),
            type_line=overrides.get("type_line", None),
            oracle_text=overrides.get("oracle_text", None),
            power=overrides.get("power", None),
            toughness=overrides.get("toughness", None),
            edhrec_rank=overrides.get("edhrec_rank", None),
        )
        session.add(card)
        session.commit()
        session.refresh(card)
        return card

    return create


@pytest.fixture
def grid_factory(session):
    def create(**overrides):
        grid_data = overrides.get("grid_data", SAMPLE_GRID_DATA)
        grid = MtgDokuGrid(
            difficulty=overrides.get("difficulty", "medium"),
            score=overrides.get("score", 10.0),
            difficulty_score=overrides.get("difficulty_score", 400.0),
            content_hash=overrides.get("content_hash", (_content_hash(grid_data)[:24] + uuid.uuid4().hex[:8])),
            grid_data=grid_data,
        )
        session.add(grid)
        session.commit()
        session.refresh(grid)
        return grid

    return create


@pytest.fixture
def daily_game_factory(session, grid_factory):
    def create(**overrides):
        easy_grid = overrides.get("easy_grid", grid_factory(difficulty="easy"))
        medium_grid = overrides.get("medium_grid", grid_factory(difficulty="medium"))
        hard_grid = overrides.get("hard_grid", grid_factory(difficulty="hard"))
        game = MtgDokuDailyGame(
            day=overrides.get("day", today_paris_date()),
            easy_grid_id=easy_grid.id,
            medium_grid_id=medium_grid.id,
            hard_grid_id=hard_grid.id,
        )
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

    return create


@pytest.fixture
def attempt_factory(session):
    def create(user, **overrides):
        attempt = MtgDokuAttempt(
            user_id=user.id,
            day=overrides.get("day", today_paris_date()),
            won_easy=overrides.get("won_easy", False),
            won_medium=overrides.get("won_medium", False),
            won_hard=overrides.get("won_hard", False),
        )
        session.add(attempt)
        session.commit()
        session.refresh(attempt)
        return attempt

    return create


@pytest.fixture
def guess_factory(session):
    def create(attempt, card, **overrides):
        guess = MtgDokuAttemptGuess(
            attempt_id=attempt.id,
            position=overrides.get("position", 0),
            difficulty=overrides.get("difficulty", "medium"),
            cell_row=overrides.get("cell_row", 0),
            cell_col=overrides.get("cell_col", 0),
            oracle_id=card.oracle_id,
            is_valid=overrides.get("is_valid", False),
        )
        session.add(guess)
        session.commit()
        session.refresh(guess)
        return guess

    return create
