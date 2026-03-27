import pytest

from app.models.familledle.champ_data import ChampData
from app.models.familledle.daily_game import FamilledleDailyGame
from app.utils.time import today_paris_date


@pytest.fixture
def champ_factory(session):
    def create(**overrides):
        champ = ChampData(
            name=overrides.get("name", "Tristana"),
            skin_number=overrides.get("skin_number", 0),
            family_mastery=overrides.get("family_mastery", []),
            mobility=overrides.get("mobility", 3),
            randomness=overrides.get("randomness", 1),
            cc_quantity=overrides.get("cc_quantity", 2),
            icon_url=overrides.get("icon_url", "https://example.com/icon.png"),
            mean_hex=overrides.get("mean_hex", "#AABBCC"),
            mean_hue=overrides.get("mean_hue", 180),
        )
        session.add(champ)
        session.commit()
        session.refresh(champ)
        return champ

    return create


@pytest.fixture
def daily_game_factory(session):
    def create(**overrides):
        game = FamilledleDailyGame(
            day=overrides.get("day", today_paris_date()),
            champ_name=overrides["champ_name"],
            row_columns=overrides.get("row_columns", []),
        )
        session.add(game)
        session.commit()
        session.refresh(game)
        return game

    return create
