from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from app.models import ChampData, FamilledleAttemptGuess, FamilledleAttempt, GuessIn
from app.db import get_session
from app.utils.time import utcnow_naive, today_paris_date
from app.deps import get_current_auth_optional, AuthContext
from sqlalchemy import func

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

    return {
        "name": champion_name,
        "data": {
            k: getattr(champ_data, k)
            for k in (
                "skin_number",
                "family_mastery",
                "mobility",
                "randomness",
                "cc_quantity",
                "icon_url",
                "mean_hex",
                "mean_hue",
                "is_champ_of_the_day",
            )
        },
    }


@router.get("/champ_of_the_day")
def get_champ_of_the_day(
    session: Session = Depends(get_session),
):
    stmt = select(ChampData).where(ChampData.is_champ_of_the_day)
    champ_data = session.exec(stmt).first()

    if champ_data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_CHAMPION_OF_THE_DAY",
                "message": "Champion of the day not found",
                "fields": {},
            },
        )

    return {
        "name": champ_data.name,
        "data": {
            k: getattr(champ_data, k)
            for k in (
                "skin_number",
                "family_mastery",
                "mobility",
                "randomness",
                "cc_quantity",
                "icon_url",
                "mean_hex",
                "mean_hue",
                "is_champ_of_the_day",
            )
        },
    }


@router.post("/attempts/guess")
def post_attempt_guess(
    payload: GuessIn,
    session: Session = Depends(get_session),
    current_auth: AuthContext | None = Depends(get_current_auth_optional),
):
    day = today_paris_date()

    # 3) valide le champion proposé (comme avant)
    guessed = session.exec(
        select(ChampData).where(
            func.lower(ChampData.name) == func.lower(payload.champion_name)
        )
    ).first()
    if guessed is None:
        raise HTTPException(status_code=404, detail={...})

    canonical_name = guessed.name

    # 6) récup champ of the day (comme avant)
    champ_of_day = session.exec(
        select(ChampData).where(ChampData.is_champ_of_the_day)
    ).first()
    if champ_of_day is None:
        raise HTTPException(status_code=404, detail={...})

    is_correct = guessed.name.lower() == champ_of_day.name.lower()

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

    # --- CONNECTÉ : ton flux actuel, mais stocke canonical_name ---
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
        raise HTTPException(status_code=409, detail={...})

    guess = FamilledleAttemptGuess(
        attempt_id=attempt.id,
        position=attempt.try_count,
        champion_name=canonical_name,  # <<< IMPORTANT
    )
    session.add(guess)

    attempt.try_count += 1
    if is_correct:
        attempt.finished_at = utcnow_naive()

    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return {
        "attempt": {
            "id": attempt.id,
            "day": attempt.day,
            "try_count": attempt.try_count,
            "finished_at": attempt.finished_at,
        },
        "guess": {
            "position": guess.position,
            "champion_name": guess.champion_name,
            "is_correct": is_correct,
        },
    }
