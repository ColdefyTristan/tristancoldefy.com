"""
import_doku_grids.py

Importe les grilles MTGDoku depuis data/mtgdoku/doku_grids.json vers la base de données.
Les grilles déjà présentes (même contenu) sont ignorées via un hash md5.

Usage :
  python -m scripts.import_doku_grids
  python -m scripts.import_doku_grids --verbose
  python -m scripts.import_doku_grids --file data/mtgdoku/doku_grids.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.db import engine
from app.models.mtg.mtgdoku_grid import MtgDokuGrid


def _content_hash(grid_data: dict) -> str:
    """Hash md5 du contenu structurel de la grille (rows, cols, cells)."""
    payload = json.dumps(
        {"rows": grid_data["rows"], "cols": grid_data["cols"], "cells": grid_data["cells"]},
        sort_keys=True,
    )
    return hashlib.md5(payload.encode()).hexdigest()

DEFAULT_FILE = Path(__file__).parent.parent / "data" / "mtgdoku" / "doku_grids.json"


def log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg)


def import_grids(file: Path, verbose: bool) -> None:
    started_at = datetime.now(timezone.utc)

    print(f"[{started_at.isoformat()}] import_doku_grids : démarrage")
    print(f"  Fichier : {file}")

    with open(file, encoding="utf-8") as f:
        grids_data: list[dict] = json.load(f)

    total_in_file = len(grids_data)
    print(f"  {total_in_file} grilles dans le fichier")

    inserted = 0
    skipped = 0
    errors = 0

    with Session(engine) as session:
        existing_hashes: set[str] = set(session.exec(select(MtgDokuGrid.content_hash)).all())
        log(f"  {len(existing_hashes)} grilles déjà en base", verbose)

        for i, grid_data in enumerate(grids_data):
            try:
                difficulty: str = grid_data["difficulty"]["label"]
                score: float = grid_data["score"]
                difficulty_score: float = grid_data["difficulty"]["score"]
                content_hash = _content_hash(grid_data)

                if content_hash in existing_hashes:
                    skipped += 1
                    log(f"  [SKIP] {difficulty} score={score:.2f} hash={content_hash[:8]}", verbose)
                    continue

                grid = MtgDokuGrid(
                    difficulty=difficulty,
                    score=score,
                    difficulty_score=difficulty_score,
                    content_hash=content_hash,
                    grid_data=grid_data,
                )
                session.add(grid)
                existing_hashes.add(content_hash)
                inserted += 1
                log(f"  [INSERT] {difficulty} score={score:.2f} hash={content_hash[:8]}", verbose)

            except (KeyError, TypeError) as e:
                errors += 1
                print(f"  [ERROR] grille index {i} : {e}", file=sys.stderr)

        session.commit()

    finished_at = datetime.now(timezone.utc)
    duration = (finished_at - started_at).total_seconds()

    # Résumé minimal toujours affiché (utile pour les logs cron)
    print(
        f"[{finished_at.isoformat()}] import_doku_grids : terminé en {duration:.1f}s"
        f" | fichier={total_in_file} insérées={inserted} ignorées={skipped} erreurs={errors}"
    )

    if errors:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe les grilles MTGDoku en base.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE,
                        help="Chemin vers doku_grids.json")
    parser.add_argument("--verbose", action="store_true",
                        help="Affiche le détail de chaque grille traitée")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Fichier introuvable : {args.file}", file=sys.stderr)
        sys.exit(1)

    import_grids(args.file, args.verbose)


if __name__ == "__main__":
    main()
