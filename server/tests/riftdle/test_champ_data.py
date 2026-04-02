def test_get_champ_data_returns_200(client, champ_factory):
    champ_factory(name="Lux", mobility=3)
    r = client.get("/riftdle/champ_data/Lux")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Lux"
    assert data["data"]["mobility"] == 3


def test_get_champ_data_is_case_insensitive(client, champ_factory):
    champ_factory(name="Lux")
    r = client.get("/riftdle/champ_data/lux")
    assert r.status_code == 200


def test_get_champ_data_returns_404_for_unknown_champion(client):
    r = client.get("/riftdle/champ_data/UnknownChampion")
    assert r.status_code == 404
    assert r.json()["code"] == "INVALID_CHAMPION_NAME"


def test_get_daily_game_returns_200(client, champ_factory, daily_game_factory):
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    r = client.get("/riftdle/daily_game")
    assert r.status_code == 200
    assert r.json()["champ_name"] == "Jinx"


def test_get_daily_game_returns_404_when_none(client):
    r = client.get("/riftdle/daily_game")
    assert r.status_code == 404
    assert r.json()["code"] == "NO_DAILY_GAME"
