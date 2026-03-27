import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.mtg.mtgdoku_attempt import MtgDokuAttempt, MtgDokuAttemptGuess


def test_attempt_is_created_for_user(attempt_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user)
    assert attempt.id is not None
    assert attempt.user_id == user.id
    assert attempt.won_easy is False
    assert attempt.won_medium is False
    assert attempt.won_hard is False
    assert attempt.finished_at is None


def test_attempt_unique_per_user_per_day(session, attempt_factory, user_factory):
    user = user_factory()
    attempt_factory(user, day=date(2026, 1, 1))
    with pytest.raises(IntegrityError):
        attempt_factory(user, day=date(2026, 1, 1))


def test_two_users_can_have_attempt_same_day(attempt_factory, user_factory):
    user1 = user_factory()
    user2 = user_factory()
    a1 = attempt_factory(user1, day=date(2026, 1, 1))
    a2 = attempt_factory(user2, day=date(2026, 1, 1))
    assert a1.id != a2.id


def test_same_user_can_have_attempts_on_different_days(attempt_factory, user_factory):
    user = user_factory()
    a1 = attempt_factory(user, day=date(2026, 1, 1))
    a2 = attempt_factory(user, day=date(2026, 1, 2))
    assert a1.id != a2.id


def test_win_flags_can_be_set_independently(session, attempt_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user, won_easy=True, won_medium=False, won_hard=True)
    session.refresh(attempt)
    assert attempt.won_easy is True
    assert attempt.won_medium is False
    assert attempt.won_hard is True


def test_guess_is_linked_to_attempt(guess_factory, attempt_factory, card_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user)
    card = card_factory()
    guess = guess_factory(attempt, card, difficulty="medium", cell_row=0, cell_col=1, is_valid=True)

    assert guess.id is not None
    assert guess.attempt_id == attempt.id
    assert guess.oracle_id == card.oracle_id
    assert guess.cell_row == 0
    assert guess.cell_col == 1
    assert guess.is_valid is True


def test_guesses_ordered_by_position(session, guess_factory, attempt_factory, card_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user)
    cards = [card_factory() for _ in range(3)]

    guess_factory(attempt, cards[2], position=2, difficulty="hard")
    guess_factory(attempt, cards[0], position=0, difficulty="easy")
    guess_factory(attempt, cards[1], position=1, difficulty="medium")

    guesses = session.exec(
        select(MtgDokuAttemptGuess)
        .where(MtgDokuAttemptGuess.attempt_id == attempt.id)
        .order_by(MtgDokuAttemptGuess.position)
    ).all()

    assert [g.position for g in guesses] == [0, 1, 2]
    assert [g.difficulty for g in guesses] == ["easy", "medium", "hard"]


def test_guess_cascade_delete_with_attempt(session, guess_factory, attempt_factory, card_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user)
    card = card_factory()
    guess_factory(attempt, card)

    session.delete(attempt)
    session.commit()

    remaining = session.exec(
        select(MtgDokuAttemptGuess).where(MtgDokuAttemptGuess.attempt_id == attempt.id)
    ).all()
    assert len(remaining) == 0


def test_guess_across_all_difficulties(guess_factory, attempt_factory, card_factory, user_factory):
    user = user_factory()
    attempt = attempt_factory(user)
    cards = [card_factory() for _ in range(3)]

    g_easy   = guess_factory(attempt, cards[0], position=0, difficulty="easy",   cell_row=0, cell_col=0)
    g_medium = guess_factory(attempt, cards[1], position=1, difficulty="medium", cell_row=1, cell_col=2)
    g_hard   = guess_factory(attempt, cards[2], position=2, difficulty="hard",   cell_row=2, cell_col=1)

    assert g_easy.difficulty == "easy"
    assert g_medium.difficulty == "medium"
    assert g_hard.difficulty == "hard"
