from sqlmodel import select

from app.models.familledle.familledle_attempt import FamilledleAttempt


def test_guess_returns_404_for_unknown_champion(client, champ_factory):
    champ_factory(name="Jinx")
    r = client.post("/familledle/attempts/guess", json={"champion_name": "UnknownChamp"})
    assert r.status_code == 404


def test_anonymous_guess_returns_result_without_db_write(session, client, champ_factory, daily_game_factory):
    champ_factory(name="Lux")
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")

    r = client.post("/familledle/attempts/guess", json={"champion_name": "Lux"})
    assert r.status_code == 200
    data = r.json()
    assert data["attempt"] is None
    assert data["guess"]["is_correct"] is False
    assert data["guess"]["champion_name"] == "Lux"

    attempts = session.exec(select(FamilledleAttempt)).all()
    assert len(attempts) == 0


def test_anonymous_correct_guess_returns_is_correct_true(client, champ_factory, daily_game_factory):
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    r = client.post("/familledle/attempts/guess", json={"champion_name": "Jinx"})
    assert r.status_code == 200
    assert r.json()["guess"]["is_correct"] is True


def test_authenticated_guess_creates_attempt_in_db(session, auth_client, champ_factory, daily_game_factory):
    champ_factory(name="Lux")
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    ctx = auth_client()

    r = ctx["client"].post("/familledle/attempts/guess", json={"champion_name": "Lux"})
    assert r.status_code == 200
    data = r.json()
    assert data["attempt"]["try_count"] == 1
    assert data["guess"]["is_correct"] is False

    attempt = session.exec(
        select(FamilledleAttempt).where(FamilledleAttempt.user_id == ctx["user"].id)
    ).first()
    assert attempt is not None
    assert attempt.try_count == 1
    assert attempt.finished_at is None


def test_authenticated_correct_guess_finishes_attempt(auth_client, champ_factory, daily_game_factory):
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    ctx = auth_client()

    r = ctx["client"].post("/familledle/attempts/guess", json={"champion_name": "Jinx"})
    assert r.status_code == 200
    data = r.json()
    assert data["attempt"]["finished_at"] is not None
    assert data["guess"]["is_correct"] is True


def test_guess_after_finished_attempt_returns_409(auth_client, champ_factory, daily_game_factory):
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    ctx = auth_client()
    authed = ctx["client"]

    authed.post("/familledle/attempts/guess", json={"champion_name": "Jinx"})
    r = authed.post("/familledle/attempts/guess", json={"champion_name": "Jinx"})
    assert r.status_code == 409


def test_get_today_attempt_returns_401_without_auth(client):
    r = client.get("/familledle/attempts/today")
    assert r.status_code == 401


def test_get_today_attempt_returns_false_when_no_attempt(auth_client):
    ctx = auth_client()
    r = ctx["client"].get("/familledle/attempts/today")
    assert r.status_code == 200
    assert r.json()["exists"] is False


def test_get_today_attempt_returns_attempt_after_guess(auth_client, champ_factory, daily_game_factory):
    champ_factory(name="Lux")
    champ_factory(name="Jinx")
    daily_game_factory(champ_name="Jinx")
    ctx = auth_client()
    authed = ctx["client"]

    authed.post("/familledle/attempts/guess", json={"champion_name": "Lux"})

    r = authed.get("/familledle/attempts/today")
    assert r.status_code == 200
    data = r.json()
    assert data["exists"] is True
    assert data["attempt"]["is_finished"] is False
    assert "Lux" in data["attempt"]["champions"]
