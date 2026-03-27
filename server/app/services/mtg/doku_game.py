"""Service métier pour la partie MTGDoku."""

from __future__ import annotations

from sqlmodel import Session, select, func

from app.models.mtg.mtg_card import MtgCard
from app.models.mtg.mtgdoku_attempt import MtgDokuAttempt, MtgDokuAttemptGuess
from app.models.mtg.mtgdoku_grid import MtgDokuDailyGame, MtgDokuGrid
from app.models.tables import User
from app.services.mtg.doku_categories import CATEGORIES_BY_ID
from app.utils.time import today_paris_date, utcnow_naive

MAX_GUESSES_PER_DIFFICULTY = 999
DIFFICULTIES = ("easy", "medium", "hard")


# ---------------------------------------------------------------------------
# Vérification d'une carte sur une case
# ---------------------------------------------------------------------------

def check_card_for_cell(
    session: Session,
    grid: MtgDokuGrid,
    cell_row: int,
    cell_col: int,
    oracle_id: str,
) -> bool:
    """Vérifie en SQL si la carte remplit toutes les conditions de la case."""
    data = grid.grid_data
    row_conditions = [c["id"] for c in data["rows"][cell_row]["conditions"]]
    col_conditions = [c["id"] for c in data["cols"][cell_col]["conditions"]]
    condition_ids = row_conditions + col_conditions

    filters = []
    for cid in condition_ids:
        cat = CATEGORIES_BY_ID.get(cid)
        if cat is None:
            return False
        filters.append(cat.filter_expr())

    count = session.exec(
        select(func.count())
        .select_from(MtgCard)
        .where(MtgCard.oracle_id == oracle_id, *filters)
    ).one()

    return count > 0


# ---------------------------------------------------------------------------
# État d'un essai
# ---------------------------------------------------------------------------

def _won_flags(guesses: list[MtgDokuAttemptGuess]) -> dict[str, bool]:
    """Calcule won_easy/medium/hard depuis la liste des guesses."""
    won: dict[str, bool] = {d: False for d in DIFFICULTIES}
    for diff in DIFFICULTIES:
        diff_guesses = [g for g in guesses if g.difficulty == diff]
        valid_cells = {(g.cell_row, g.cell_col) for g in diff_guesses if g.is_valid}
        if len(valid_cells) == 9:
            won[diff] = True
    return won


def get_or_create_attempt(session: Session, user: User) -> MtgDokuAttempt:
    today = today_paris_date()
    attempt = session.exec(
        select(MtgDokuAttempt).where(
            MtgDokuAttempt.user_id == user.id,
            MtgDokuAttempt.day == today,
        )
    ).first()

    if not attempt:
        attempt = MtgDokuAttempt(user_id=user.id, day=today)
        session.add(attempt)
        session.flush()

    return attempt


# ---------------------------------------------------------------------------
# Jouer une carte
# ---------------------------------------------------------------------------

def play_guess(
    session: Session,
    attempt: MtgDokuAttempt,
    grid: MtgDokuGrid,
    cell_row: int,
    cell_col: int,
    oracle_id: str,
) -> tuple[MtgDokuAttemptGuess, bool]:
    """
    Ajoute un guess à l'essai. Retourne (guess, is_valid).
    Raises ValueError si la case est déjà gagnée ou le max de tentatives atteint.
    """
    difficulty = grid.difficulty
    existing = session.exec(
        select(MtgDokuAttemptGuess).where(
            MtgDokuAttemptGuess.attempt_id == attempt.id,
            MtgDokuAttemptGuess.difficulty == difficulty,
        )
    ).all()

    # Cellule déjà gagnée ?
    cell_won = any(
        g.cell_row == cell_row and g.cell_col == cell_col and g.is_valid
        for g in existing
    )
    if cell_won:
        raise ValueError("CELL_ALREADY_WON")

    # Max tentatives atteint ?
    diff_count = len(existing)
    if diff_count >= MAX_GUESSES_PER_DIFFICULTY:
        raise ValueError("MAX_GUESSES_REACHED")

    # Carte déjà jouée dans cette case ?
    already_tried = any(
        g.cell_row == cell_row and g.cell_col == cell_col and g.oracle_id == oracle_id
        for g in existing
    )
    if already_tried:
        raise ValueError("CARD_ALREADY_TRIED")

    is_valid = check_card_for_cell(session, grid, cell_row, cell_col, oracle_id)

    # Position globale dans l'essai (toutes difficultés confondues)
    total_guesses = session.exec(
        select(func.count()).select_from(MtgDokuAttemptGuess)
        .where(MtgDokuAttemptGuess.attempt_id == attempt.id)
    ).one()

    guess = MtgDokuAttemptGuess(
        attempt_id=attempt.id,
        position=total_guesses,
        difficulty=difficulty,
        cell_row=cell_row,
        cell_col=cell_col,
        oracle_id=oracle_id,
        is_valid=is_valid,
    )
    session.add(guess)
    session.flush()

    # Mettre à jour les flags de victoire
    all_guesses = existing + [guess]
    won = _won_flags(all_guesses)
    attempt.won_easy = won["easy"]
    attempt.won_medium = won["medium"]
    attempt.won_hard = won["hard"]

    if all(won.values()):
        attempt.finished_at = utcnow_naive()

    session.add(attempt)
    session.commit()
    session.refresh(guess)

    return guess, is_valid
