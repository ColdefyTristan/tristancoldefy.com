from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_auth, AuthContext
from app.models.mtg.batch_schemas import ApplyDeckOperationsRequest, ApplyDeckOperationsResponse
from app.services.mtg.batch_processor import (
    apply_batch,
    BatchConflictVersionError,
    BatchOperationError,
)
from app.services.mtg.exceptions import DeckNotFound, DeckAccessForbidden

router = APIRouter(prefix="/decks", tags=["mtg"])


@router.post("/{deck_id}/apply-operations", response_model=ApplyDeckOperationsResponse)
def apply_deck_operations(
    deck_id: int,
    payload: ApplyDeckOperationsRequest,
    auth: AuthContext = Depends(get_current_auth),
    session: Session = Depends(get_session),
):
    try:
        return apply_batch(session, deck_id, auth.user.id, payload)

    except DeckNotFound:
        return JSONResponse(status_code=404, content={"error": "not_found", "message": "Deck not found.", "operation_errors": []})

    except DeckAccessForbidden:
        return JSONResponse(status_code=403, content={"error": "forbidden_deck_access", "message": "Access to this deck is forbidden.", "operation_errors": []})

    except BatchConflictVersionError:
        return JSONResponse(status_code=409, content={"error": "conflict_version", "message": "base_version does not match the current deck version.", "operation_errors": []})

    except BatchOperationError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_batch",
                "message": "One or more operations are invalid.",
                "operation_errors": [
                    {"operation_id": exc.operation_id, "code": exc.code, "message": exc.message}
                ],
            },
        )
