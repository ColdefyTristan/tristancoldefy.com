from sqlmodel import SQLModel, Field
from datetime import datetime


class MtgBulkSyncState(SQLModel, table=True):
    __tablename__ = "mtg_bulk_sync_state"

    id: int | None = Field(default=None, primary_key=True)

    bulk_type: str
    remote_bulk_id: str | None = None
    remote_updated_at: datetime | None = None
    remote_download_uri: str | None = None
    remote_size: int | None = None

    last_downloaded_at: datetime | None = None
    last_downloaded_file_path: str | None = None

    last_imported_bulk_id: str | None = None
    last_imported_at: datetime | None = None

    last_status: str
    last_error: str | None = None
