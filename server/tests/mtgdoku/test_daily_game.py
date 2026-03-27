import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.mtg.mtgdoku_grid import MtgDokuGrid, MtgDokuDailyGame


def test_grid_is_created_with_correct_fields(grid_factory):
    grid = grid_factory(difficulty="hard", score=5.0, difficulty_score=150.0)
    assert grid.id is not None
    assert grid.difficulty == "hard"
    assert grid.score == 5.0
    assert grid.difficulty_score == 150.0


def test_grid_data_is_stored_and_retrieved(session, grid_factory):
    grid = grid_factory()
    retrieved = session.get(MtgDokuGrid, grid.id)
    assert retrieved.grid_data["difficulty"]["label"] == "medium"
    assert len(retrieved.grid_data["rows"]) == 3
    assert len(retrieved.grid_data["cols"]) == 3
    assert len(retrieved.grid_data["cells"]) == 3


def test_daily_game_links_three_grids(daily_game_factory, grid_factory):
    easy = grid_factory(difficulty="easy")
    medium = grid_factory(difficulty="medium")
    hard = grid_factory(difficulty="hard")
    game = daily_game_factory(easy_grid=easy, medium_grid=medium, hard_grid=hard)

    assert game.easy_grid_id == easy.id
    assert game.medium_grid_id == medium.id
    assert game.hard_grid_id == hard.id


def test_daily_game_unique_per_day(session, daily_game_factory):
    daily_game_factory(day=date(2026, 1, 1))
    with pytest.raises(IntegrityError):
        daily_game_factory(day=date(2026, 1, 1))


def test_daily_game_allows_different_days(daily_game_factory):
    g1 = daily_game_factory(day=date(2026, 1, 1))
    g2 = daily_game_factory(day=date(2026, 1, 2))
    assert g1.id != g2.id


def test_daily_game_grid_ids_can_be_null(session, grid_factory):
    easy = grid_factory(difficulty="easy")
    game = MtgDokuDailyGame(
        day=date(2026, 6, 1),
        easy_grid_id=easy.id,
        medium_grid_id=None,
        hard_grid_id=None,
    )
    session.add(game)
    session.commit()
    session.refresh(game)
    assert game.medium_grid_id is None
    assert game.hard_grid_id is None
