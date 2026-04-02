from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func

from app.db import get_session
from app.deps import get_current_auth, get_current_auth_optional, AuthContext
from app.models.mtg.mtg_card import MtgCard
from app.models.mtg.mtgdoku_attempt import MtgDokuAttempt, MtgDokuAttemptGuess
from app.models.mtg.mtgdoku_grid import MtgDokuDailyGame, MtgDokuGrid
from app.models.tables import User
from app.services.mtg.doku_categories import ALL_CATEGORIES, CATEGORIES_BY_ID
from app.services.mtg.doku_game import (
    check_card_for_cell,
    get_or_create_attempt,
    play_guess,
)
from app.utils.time import today_paris_date

router = APIRouter(prefix="/mtgdoku", tags=["mtgdoku"])


# ---------------------------------------------------------------------------
# Schémas de réponse
# ---------------------------------------------------------------------------

class ConditionOut(BaseModel):
    id: str
    label: str
    weight: float
    total: int
    known: int


class GroupOut(BaseModel):
    conditions: list[ConditionOut]
    total: int
    known: int


class CellOut(BaseModel):
    total: int
    known: int


class CardTriedOut(BaseModel):
    oracle_id: str
    name: str
    is_valid: bool


class CellWithAttemptOut(BaseModel):
    total: int
    known: int
    cards_tried: list[CardTriedOut]


class GridOut(BaseModel):
    id: int
    difficulty: str
    score: float
    difficulty_score: float
    rows: list[GroupOut]
    cols: list[GroupOut]
    cells: list[list[CellOut]]


class GridWithAttemptOut(BaseModel):
    id: int
    difficulty: str
    score: float
    difficulty_score: float
    rows: list[GroupOut]
    cols: list[GroupOut]
    cells: list[list[CellWithAttemptOut]]


class DailyGameOut(BaseModel):
    id: int
    day: date
    easy: GridOut | None
    medium: GridOut | None
    hard: GridOut | None


class GuessOut(BaseModel):
    id: int
    position: int
    difficulty: str
    cell_row: int
    cell_col: int
    oracle_id: str
    card_name: str
    is_valid: bool


class AttemptOut(BaseModel):
    id: int
    day: date
    won_easy: bool
    won_medium: bool
    won_hard: bool
    finished_at: datetime | None
    guesses: list[GuessOut]


class GuessIn(BaseModel):
    difficulty: str
    cell_row: int
    cell_col: int
    oracle_id: str


class GuessResultOut(BaseModel):
    is_valid: bool
    oracle_id: str
    card_name: str | None
    attempt: AttemptOut | None  # None si anonyme


class CheckOut(BaseModel):
    is_valid: bool
    oracle_id: str
    card_name: str | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _grid_to_out(grid: MtgDokuGrid) -> GridOut:
    data = grid.grid_data
    return GridOut(
        id=grid.id,
        difficulty=grid.difficulty,
        score=grid.score,
        difficulty_score=grid.difficulty_score,
        rows=data["rows"],
        cols=data["cols"],
        cells=data["cells"],
    )


def _grid_with_attempt(grid: MtgDokuGrid, attempt: MtgDokuAttempt, session: Session) -> GridWithAttemptOut:
    data = grid.grid_data
    difficulty = grid.difficulty

    # Guesses pour cette grille
    guesses = session.exec(
        select(MtgDokuAttemptGuess, MtgCard.name)
        .join(MtgCard, MtgDokuAttemptGuess.oracle_id == MtgCard.oracle_id)
        .where(
            MtgDokuAttemptGuess.attempt_id == attempt.id,
            MtgDokuAttemptGuess.difficulty == difficulty,
        )
        .order_by(MtgDokuAttemptGuess.position)
    ).all()

    # Regrouper par (cell_row, cell_col)
    cells_tried: dict[tuple[int, int], list[CardTriedOut]] = {}
    for guess, card_name in guesses:
        key = (guess.cell_row, guess.cell_col)
        cells_tried.setdefault(key, []).append(
            CardTriedOut(oracle_id=guess.oracle_id, name=card_name, is_valid=guess.is_valid)
        )

    cells: list[list[CellWithAttemptOut]] = []
    for r, row in enumerate(data["cells"]):
        cells.append([
            CellWithAttemptOut(
                total=cell["total"],
                known=cell["known"],
                cards_tried=cells_tried.get((r, c), []),
            )
            for c, cell in enumerate(row)
        ])

    return GridWithAttemptOut(
        id=grid.id,
        difficulty=difficulty,
        score=grid.score,
        difficulty_score=grid.difficulty_score,
        rows=data["rows"],
        cols=data["cols"],
        cells=cells,
    )


def _attempt_to_out(attempt: MtgDokuAttempt, session: Session) -> AttemptOut:
    rows = session.exec(
        select(MtgDokuAttemptGuess, MtgCard.name)
        .join(MtgCard, MtgDokuAttemptGuess.oracle_id == MtgCard.oracle_id)
        .where(MtgDokuAttemptGuess.attempt_id == attempt.id)
        .order_by(MtgDokuAttemptGuess.position)
    ).all()
    guesses = [
        GuessOut(
            id=g.id,
            position=g.position,
            difficulty=g.difficulty,
            cell_row=g.cell_row,
            cell_col=g.cell_col,
            oracle_id=g.oracle_id,
            card_name=name,
            is_valid=g.is_valid,
        )
        for g, name in rows
    ]
    return AttemptOut(
        id=attempt.id,
        day=attempt.day,
        won_easy=attempt.won_easy,
        won_medium=attempt.won_medium,
        won_hard=attempt.won_hard,
        finished_at=attempt.finished_at,
        guesses=guesses,
    )


def _load_daily_game(game: MtgDokuDailyGame, session: Session) -> DailyGameOut:
    def load(grid_id: int | None) -> GridOut | None:
        if grid_id is None:
            return None
        grid = session.get(MtgDokuGrid, grid_id)
        return _grid_to_out(grid) if grid else None

    return DailyGameOut(
        id=game.id,
        day=game.day,
        easy=load(game.easy_grid_id),
        medium=load(game.medium_grid_id),
        hard=load(game.hard_grid_id),
    )


# ---------------------------------------------------------------------------
# Grilles
# ---------------------------------------------------------------------------

@router.get("/grid/{grid_id}", response_model=GridOut)
def get_grid(grid_id: int, session: Session = Depends(get_session)):
    grid = session.get(MtgDokuGrid, grid_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Grille introuvable")
    return _grid_to_out(grid)


@router.get("/grid/{grid_id}/attempt/{attempt_id}", response_model=GridWithAttemptOut)
def get_grid_with_attempt(
    grid_id: int,
    attempt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_auth),
):
    grid = session.get(MtgDokuGrid, grid_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Grille introuvable")

    attempt = session.get(MtgDokuAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Essai introuvable")

    return _grid_with_attempt(grid, attempt, session)


# ---------------------------------------------------------------------------
# Partie quotidienne
# ---------------------------------------------------------------------------

@router.get("/daily", response_model=DailyGameOut)
def get_today_daily_game(session: Session = Depends(get_session)):
    game = session.exec(
        select(MtgDokuDailyGame).where(MtgDokuDailyGame.day == today_paris_date())
    ).first()
    if not game:
        raise HTTPException(status_code=404, detail="Aucune partie pour aujourd'hui")
    return _load_daily_game(game, session)


@router.get("/daily/attempt", response_model=AttemptOut)
def get_today_attempt(
    session: Session = Depends(get_session),
    auth: AuthContext = Depends(get_current_auth),
):
    attempt = session.exec(
        select(MtgDokuAttempt).where(
            MtgDokuAttempt.user_id == auth.user.id,
            MtgDokuAttempt.day == today_paris_date(),
        )
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Aucun essai pour aujourd'hui")
    return _attempt_to_out(attempt, session)


@router.get("/daily/{daily_game_id}", response_model=DailyGameOut)
def get_daily_game_by_id(daily_game_id: int, session: Session = Depends(get_session)):
    game = session.get(MtgDokuDailyGame, daily_game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partie quotidienne introuvable")
    return _load_daily_game(game, session)


@router.post("/daily/guess", response_model=GuessResultOut)
def post_guess(
    body: GuessIn,
    session: Session = Depends(get_session),
    auth: AuthContext | None = Depends(get_current_auth_optional),
):
    # Récupérer la partie du jour
    game = session.exec(
        select(MtgDokuDailyGame).where(MtgDokuDailyGame.day == today_paris_date())
    ).first()
    if not game:
        raise HTTPException(status_code=404, detail="Aucune partie pour aujourd'hui")

    # Récupérer la grille selon la difficulté
    grid_id = {"easy": game.easy_grid_id, "medium": game.medium_grid_id, "hard": game.hard_grid_id}.get(body.difficulty)
    if grid_id is None:
        raise HTTPException(status_code=400, detail="Difficulté invalide")
    grid = session.get(MtgDokuGrid, grid_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Grille introuvable")

    # Vérifier que la carte existe
    card = session.exec(select(MtgCard).where(MtgCard.oracle_id == body.oracle_id)).first()
    if not card:
        raise HTTPException(status_code=404, detail="Carte introuvable")

    # Anonyme : juste vérifier, ne rien stocker
    if auth is None:
        is_valid = check_card_for_cell(session, grid, body.cell_row, body.cell_col, body.oracle_id)
        return GuessResultOut(is_valid=is_valid, oracle_id=body.oracle_id, card_name=card.name, attempt=None)

    # Authentifié : créer/récupérer l'essai et jouer
    attempt = get_or_create_attempt(session, auth.user)

    try:
        guess, is_valid = play_guess(session, attempt, grid, body.cell_row, body.cell_col, body.oracle_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    session.refresh(attempt)
    return GuessResultOut(
        is_valid=is_valid,
        oracle_id=body.oracle_id,
        card_name=card.name,
        attempt=_attempt_to_out(attempt, session),
    )


@router.get("/check", response_model=CheckOut)
def check_card(
    grid_id: int = Query(...),
    cell_row: int = Query(...),
    cell_col: int = Query(...),
    oracle_id: str = Query(...),
    session: Session = Depends(get_session),
):
    grid = session.get(MtgDokuGrid, grid_id)
    if not grid:
        raise HTTPException(status_code=404, detail="Grille introuvable")

    card = session.exec(select(MtgCard).where(MtgCard.oracle_id == oracle_id)).first()

    is_valid = check_card_for_cell(session, grid, cell_row, cell_col, oracle_id)
    return CheckOut(is_valid=is_valid, oracle_id=oracle_id, card_name=card.name if card else None)


# ---------------------------------------------------------------------------
# Cartes — autocomplétion
# ---------------------------------------------------------------------------

class CardEntryOut(BaseModel):
    name: str
    oracle_id: str
    image_url_medium: str | None


class CardNamesOut(BaseModel):
    lang: str
    cards: list[CardEntryOut]


@router.get("/cards/names", response_model=CardNamesOut)
def get_card_names(session: Session = Depends(get_session)):
    """Retourne tous les noms et oracle_ids distincts pour l'autocomplétion côté client."""
    rows = session.exec(
        select(MtgCard.name, MtgCard.oracle_id, MtgCard.image_url_medium).distinct().order_by(MtgCard.name)
    ).all()
    return CardNamesOut(lang="en", cards=[
        CardEntryOut(name=name, oracle_id=oracle_id, image_url_medium=image_url_medium)
        for name, oracle_id, image_url_medium in rows
    ])


# ---------------------------------------------------------------------------
# Catégories (debug/admin)
# ---------------------------------------------------------------------------

@router.get("/categories")
def list_categories():
    return [{"id": cat.id, "label": cat.label, "group": cat.group} for cat in ALL_CATEGORIES]


@router.get("/category-stats")
def category_stats(session: Session = Depends(get_session)):
    result = []
    for cat in ALL_CATEGORIES:
        count = session.exec(
            select(func.count()).select_from(MtgCard).where(cat.filter_expr())
        ).one()
        result.append({"id": cat.id, "label": cat.label, "group": cat.group, "count": count})
    return result


@router.get("/pair-count")
def pair_count(
    cat1: str = Query(...),
    cat2: str = Query(...),
    session: Session = Depends(get_session),
):
    if cat1 not in CATEGORIES_BY_ID:
        return {"error": "unknown_category", "category": cat1}
    if cat2 not in CATEGORIES_BY_ID:
        return {"error": "unknown_category", "category": cat2}

    count = session.exec(
        select(func.count())
        .select_from(MtgCard)
        .where(CATEGORIES_BY_ID[cat1].filter_expr(), CATEGORIES_BY_ID[cat2].filter_expr())
    ).one()

    return {"cat1": cat1, "cat2": cat2, "count": count}
