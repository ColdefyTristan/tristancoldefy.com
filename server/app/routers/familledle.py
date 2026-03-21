from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from app.models.familledle.champ_data import ChampData
from app.models.familledle.daily_game import FamilledleDailyGame
from app.models.familledle.familledle_attempt import (
    FamilledleAttemptGuess,
    FamilledleAttempt,
)
from app.models.familledle.schemas import (
    ClueIn,
    GuessIn,
    FamilledleAttemptTodayWrapperOut,
)
from app.db import get_session
from app.utils.time import utcnow_naive, today_paris_date
from app.deps import get_current_auth_optional, AuthContext, get_current_auth
from sqlalchemy import func, select as sa_select
from app.services.familledle.attempts import (
    get_attempt_for_user_by_day,
    attempt_to_day_out,
)

_CHAMP_DATA_FIELDS = (
    "skin_number",
    "family_mastery",
    "mobility",
    "randomness",
    "cc_quantity",
    "intension",
    "vote",
    "regime",
    "pilosite",
    "genre",
    "ressource",
    "portee",
    "annee_sortie",
    "role",
    "espece",
    "region",
    "icon_url",
    "mean_hex",
    "mean_hue",
)


def _compute_ranks(session: Session, champ: ChampData) -> dict:
    """Calcule le rang du champion parmi tous les champions pour chaque stat buckettée."""
    total: int = session.execute(
        sa_select(func.count()).select_from(ChampData)
    ).scalar_one()

    def rank_of(col, value: int) -> int:
        count: int = session.execute(
            sa_select(func.count()).select_from(ChampData).where(col < value)
        ).scalar_one()
        return count + 1

    return {
        "mobility_rank": rank_of(ChampData.mobility, champ.mobility),
        "randomness_rank": rank_of(ChampData.randomness, champ.randomness),
        "cc_quantity_rank": rank_of(ChampData.cc_quantity, champ.cc_quantity),
        "intension_rank": rank_of(ChampData.intension, champ.intension),
        "total_champions": total,
    }


router = APIRouter(prefix="/familledle", tags=["familledle"])


@router.get("/champ_data/{champion_name}")
def get_champ_data(
    champion_name: str,
    session: Session = Depends(get_session),
):
    stmt = select(ChampData).where(
        func.lower(ChampData.name) == func.lower(champion_name)
    )
    champ_data = session.exec(stmt).first()

    if champ_data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "INVALID_CHAMPION_NAME",
                "message": "Invalid champion name.",
                "fields": {},
            },
        )

    ranks = _compute_ranks(session, champ_data)
    return {
        "name": champ_data.name,
        "data": {
            **{k: getattr(champ_data, k) for k in _CHAMP_DATA_FIELDS},
            **ranks,
        },
    }


@router.get("/daily_game")
def get_daily_game(
    session: Session = Depends(get_session),
):
    day = today_paris_date()
    daily_game = session.exec(
        select(FamilledleDailyGame).where(FamilledleDailyGame.day == day)
    ).first()

    if daily_game is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_DAILY_GAME",
                "message": "No daily game found for today.",
                "fields": {},
            },
        )

    return {
        "day": daily_game.day,
        "champ_name": daily_game.champ_name,
        "row_columns": daily_game.row_columns,
        "winner_count": daily_game.winner_count,
    }


@router.post("/attempts/guess")
def post_attempt_guess(
    payload: GuessIn,
    session: Session = Depends(get_session),
    current_auth: AuthContext | None = Depends(get_current_auth_optional),
):
    day = today_paris_date()

    # Valide le champion proposé
    guessed = session.exec(
        select(ChampData).where(
            func.lower(ChampData.name) == func.lower(payload.champion_name)
        )
    ).first()
    if guessed is None:
        raise HTTPException(status_code=404, detail={
            "code": "INVALID_CHAMPION_NAME",
            "message": "Invalid champion name.",
            "fields": {},
        })

    canonical_name = guessed.name

    # Récup la partie du jour
    daily_game = session.exec(
        select(FamilledleDailyGame).where(FamilledleDailyGame.day == day)
    ).first()
    if daily_game is None:
        raise HTTPException(status_code=404, detail={
            "code": "NO_DAILY_GAME",
            "message": "No daily game found for today.",
            "fields": {},
        })

    is_correct = canonical_name.lower() == daily_game.champ_name.lower()

    # --- ANON : pas de DB write ---
    if current_auth is None or current_auth.user is None:
        return {
            "attempt": None,
            "guess": {
                "position": None,
                "champion_name": canonical_name,
                "is_correct": is_correct,
            },
        }

    # --- CONNECTÉ ---
    attempt = session.exec(
        select(FamilledleAttempt).where(
            FamilledleAttempt.user_id == current_auth.user.id,
            FamilledleAttempt.day == day,
        )
    ).first()
    if attempt is None:
        attempt = FamilledleAttempt(user_id=current_auth.user.id, day=day)
        session.add(attempt)
        session.flush()

    if attempt.finished_at is not None:
        raise HTTPException(status_code=409, detail={
            "code": "ATTEMPT_ALREADY_FINISHED",
            "message": "Attempt already finished.",
            "fields": {},
        })

    guess = FamilledleAttemptGuess(
        attempt_id=attempt.id,
        position=attempt.try_count,
        champion_name=canonical_name,
    )
    session.add(guess)

    attempt.try_count += 1
    attempt.clue_points = min(attempt.clue_points + 1, 3)
    if is_correct:
        attempt.finished_at = utcnow_naive()
        daily_game.winner_count += 1
        session.add(daily_game)

    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return {
        "attempt": {
            "id": attempt.id,
            "day": attempt.day,
            "try_count": attempt.try_count,
            "finished_at": attempt.finished_at,
            "clue_points": attempt.clue_points,
        },
        "guess": {
            "position": guess.position,
            "champion_name": guess.champion_name,
            "is_correct": is_correct,
        },
    }


@router.post("/attempts/clue")
def post_attempt_clue(
    payload: ClueIn,
    session: Session = Depends(get_session),
    auth_context: AuthContext = Depends(get_current_auth),
):
    day = today_paris_date()

    attempt = session.exec(
        select(FamilledleAttempt).where(
            FamilledleAttempt.user_id == auth_context.user.id,
            FamilledleAttempt.day == day,
        )
    ).first()
    if attempt is None:
        attempt = FamilledleAttempt(user_id=auth_context.user.id, day=day)
        session.add(attempt)
        session.flush()

    if attempt.clue_points < 3:
        raise HTTPException(status_code=409, detail={
            "code": "INSUFFICIENT_CLUE_POINTS",
            "message": "Not enough clue points.",
            "fields": {},
        })

    if payload.clue not in attempt.clues:
        attempt.clues = [*attempt.clues, payload.clue]
        attempt.clue_points -= 3
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

    return {"clues": attempt.clues, "clue_points": attempt.clue_points}


@router.get("/attempts/today", response_model=FamilledleAttemptTodayWrapperOut)
def get_today_attempt(
    session: Session = Depends(get_session),
    auth_context: AuthContext = Depends(get_current_auth),
):
    day = today_paris_date()
    attempt = get_attempt_for_user_by_day(
        session, user_id=auth_context.user.id, day=day
    )
    if not attempt:
        return FamilledleAttemptTodayWrapperOut(exists=False, attempt=None)
    return FamilledleAttemptTodayWrapperOut(
        exists=True, attempt=attempt_to_day_out(attempt)
    )
