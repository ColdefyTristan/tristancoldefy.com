from __future__ import annotations


from sqlmodel import Session, select

# Adapte ces imports à ton projet
from app.models.mtg.mtg_bulk_state import MtgBulkSyncState

BULK_TYPE = "oracle_cards"


def get_or_create_sync_state(session: Session) -> MtgBulkSyncState:
    sync_state = session.exec(
        select(MtgBulkSyncState).where(MtgBulkSyncState.bulk_type == BULK_TYPE)
    ).first()

    if sync_state is None:
        sync_state = MtgBulkSyncState(
            bulk_type=BULK_TYPE,
            last_status="idle",
        )
        session.add(sync_state)
        session.commit()
        session.refresh(sync_state)

    return sync_state
