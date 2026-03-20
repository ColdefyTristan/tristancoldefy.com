from __future__ import annotations

import gzip
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import ijson
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import Session

# Adapte ces imports à ton projet
from app.db import engine
from app.models.mtg.mtg_card import MtgCard

from scripts.scryfall_bulk_utilities import get_or_create_sync_state


UPSERT_BATCH_SIZE = 1000


def open_json_file_maybe_gzipped(file_path: Path) -> BinaryIO:
    with file_path.open("rb") as raw_file:
        magic_header = raw_file.read(2)

    if magic_header == b"\x1f\x8b":
        return gzip.open(file_path, "rb")

    return file_path.open("rb")


def extract_image_urls(card_data: dict) -> tuple[str | None, str | None]:
    image_uris = card_data.get("image_uris") or {}
    if image_uris:
        return image_uris.get("small"), image_uris.get("normal")

    for card_face in card_data.get("card_faces") or []:
        face_image_uris = card_face.get("image_uris") or {}
        if face_image_uris:
            return face_image_uris.get("small"), face_image_uris.get("normal")

    return None, None


def build_mtg_card_row(card_data: dict) -> dict:
    image_url_small, image_url_medium = extract_image_urls(card_data)

    return {
        "oracle_id": card_data["oracle_id"],
        "name": card_data["name"],
        "image_url_small": image_url_small,
        "image_url_medium": image_url_medium,
        "color_identity": card_data.get("color_identity") or [],
        "converted_mana_cost": int(card_data.get("cmc") or 0),
    }


def upsert_mtg_cards(session: Session, mtg_card_rows: list[dict]) -> None:
    if not mtg_card_rows:
        return

    mtg_card_table = MtgCard.__table__

    insert_statement = pg_insert(mtg_card_table).values(mtg_card_rows)

    upsert_statement = insert_statement.on_conflict_do_update(
        index_elements=[mtg_card_table.c.oracle_id],
        set_={
            "name": insert_statement.excluded.name,
            "image_url_small": insert_statement.excluded.image_url_small,
            "image_url_medium": insert_statement.excluded.image_url_medium,
            "color_identity": insert_statement.excluded.color_identity,
            "converted_mana_cost": insert_statement.excluded.converted_mana_cost,
        },
    )

    session.exec(upsert_statement)


def main() -> None:
    with Session(engine) as session:
        sync_state = get_or_create_sync_state(session)

        if sync_state.last_status != "downloaded":
            raise RuntimeError(
                "Aucun bulk prêt à être importé. Lancez d'abord le script de téléchargement."
            )

        if not sync_state.last_downloaded_file_path:
            raise RuntimeError("last_downloaded_file_path est vide.")

        bulk_file_path = Path(sync_state.last_downloaded_file_path)

        if not bulk_file_path.exists():
            raise FileNotFoundError(f"Fichier bulk introuvable : {bulk_file_path}")

        sync_state.last_status = "importing"
        sync_state.last_error = None
        session.add(sync_state)
        session.commit()

        imported_cards_count = 0
        mtg_card_rows_batch: list[dict] = []

        try:
            with open_json_file_maybe_gzipped(bulk_file_path) as bulk_file:
                for card_data in ijson.items(bulk_file, "item"):
                    mtg_card_rows_batch.append(build_mtg_card_row(card_data))

                    if len(mtg_card_rows_batch) >= UPSERT_BATCH_SIZE:
                        upsert_mtg_cards(session, mtg_card_rows_batch)
                        session.commit()
                        imported_cards_count += len(mtg_card_rows_batch)
                        mtg_card_rows_batch.clear()

            if mtg_card_rows_batch:
                upsert_mtg_cards(session, mtg_card_rows_batch)
                session.commit()
                imported_cards_count += len(mtg_card_rows_batch)
                mtg_card_rows_batch.clear()

        except Exception as error:
            session.rollback()
            sync_state.last_status = "failed"
            sync_state.last_error = f"import_failed: {error}"
            session.add(sync_state)
            session.commit()
            raise

        sync_state.last_imported_bulk_id = sync_state.remote_bulk_id
        sync_state.last_imported_at = datetime.now(timezone.utc)
        sync_state.last_status = "imported"
        sync_state.last_error = None
        session.add(sync_state)
        session.commit()

    print(f"Import terminé : {imported_cards_count} cartes traitées.")


if __name__ == "__main__":
    main()
