from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import requests
from sqlmodel import Session

# Adapte ces imports à ton projet
from app.db import engine

from scripts.scryfall_bulk_utilities import BULK_TYPE, get_or_create_sync_state

BULK_METADATA_URL = f"https://api.scryfall.com/bulk-data/{BULK_TYPE}"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIRECTORY = PROJECT_ROOT / "data" / "scryfall"
DOWNLOAD_CHUNK_SIZE_BYTES = 1024 * 1024


def fetch_remote_bulk_metadata() -> dict:
    response = requests.get(BULK_METADATA_URL, timeout=30)
    response.raise_for_status()

    bulk_metadata = response.json()

    if bulk_metadata.get("type") != BULK_TYPE:
        raise RuntimeError(
            f"Le bulk récupéré n'est pas de type {BULK_TYPE}: {bulk_metadata.get('type')}"
        )

    return bulk_metadata


def parse_scryfall_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_download_path(remote_bulk_id: str) -> Path:
    DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return DOWNLOAD_DIRECTORY / f"{BULK_TYPE}_{remote_bulk_id}.json"


def download_bulk_file(download_url: str, output_path: Path) -> None:
    temporary_output_path = output_path.with_suffix(f"{output_path.suffix}.part")

    if temporary_output_path.exists():
        temporary_output_path.unlink()

    with requests.get(download_url, stream=True, timeout=120) as response:
        response.raise_for_status()

        with temporary_output_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE_BYTES):
                if chunk:
                    output_file.write(chunk)

    temporary_output_path.replace(output_path)


def main() -> None:
    remote_bulk_metadata = fetch_remote_bulk_metadata()
    remote_bulk_id = remote_bulk_metadata["id"]
    remote_updated_at = parse_scryfall_datetime(remote_bulk_metadata["updated_at"])
    remote_download_url = remote_bulk_metadata["download_uri"]
    remote_size = remote_bulk_metadata["size"]

    download_path = build_download_path(remote_bulk_id)

    with Session(engine) as session:
        sync_state = get_or_create_sync_state(session)

        sync_state.remote_bulk_id = remote_bulk_id
        sync_state.remote_updated_at = remote_updated_at
        sync_state.remote_download_uri = remote_download_url
        sync_state.remote_size = remote_size
        sync_state.last_error = None

        if sync_state.last_imported_bulk_id == remote_bulk_id:
            sync_state.last_status = "imported"
            session.add(sync_state)
            session.commit()
            print("Bulk déjà importé, rien à faire.")
            return

        if (
            sync_state.last_status == "downloaded"
            and sync_state.last_downloaded_file_path == str(download_path)
            and download_path.exists()
        ):
            session.add(sync_state)
            session.commit()
            print(f"Bulk déjà téléchargé : {download_path}")
            return

        sync_state.last_status = "downloading"
        session.add(sync_state)
        session.commit()

        try:
            download_bulk_file(remote_download_url, download_path)
        except Exception as error:
            sync_state.last_status = "failed"
            sync_state.last_error = f"download_failed: {error}"
            session.add(sync_state)
            session.commit()
            raise

        sync_state.last_downloaded_at = datetime.now(timezone.utc)
        sync_state.last_downloaded_file_path = str(download_path)
        sync_state.last_status = "downloaded"
        sync_state.last_error = None

        session.add(sync_state)
        session.commit()

    print(f"Bulk téléchargé : {download_path}")


if __name__ == "__main__":
    main()
