"""
assign_daily_doku.py

Sélectionne et assigne les 3 grilles MTGDoku du jour (easy, medium, hard).
Les grilles récemment utilisées sont exclues. La sélection est pondérée par score.

Usage :
  python -m scripts.assign_daily_doku
  python -m scripts.assign_daily_doku --date 2026-04-01
  python -m scripts.assign_daily_doku --cooldown 30 --weight-power 2.0
  python -m scripts.assign_daily_doku --verbose
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from app.utils.time import utcnow_naive, today_paris_date
from pathlib import Path

from sqlmodel import Session, select

from app.db import engine
from app.models.mtg.mtgdoku_grid import MtgDokuDailyGame, MtgDokuGrid

# ---------------------------------------------------------------------------
# Paramètres par défaut
# ---------------------------------------------------------------------------

# Nombre de jours pendant lesquels une grille ne peut pas être réutilisée
COOLDOWN_DAYS: int = 60

# Exposant appliqué au score normalisé pour amplifier la préférence aux meilleures grilles.
# 1.0 = linéaire, 2.0 = quadratique (favorise encore plus les meilleurs scores)
WEIGHT_POWER: float = 1.0

DIFFICULTIES = ("easy", "medium", "hard")


# ---------------------------------------------------------------------------
# Logique de sélection
# ---------------------------------------------------------------------------

def _recent_grid_ids(session: Session, cutoff: date) -> set[int]:
    """Retourne les IDs de toutes les grilles utilisées depuis cutoff."""
    rows = session.exec(
        select(
            MtgDokuDailyGame.easy_grid_id,
            MtgDokuDailyGame.medium_grid_id,
            MtgDokuDailyGame.hard_grid_id,
        ).where(MtgDokuDailyGame.day >= cutoff)
    ).all()

    ids: set[int] = set()
    for easy_id, medium_id, hard_id in rows:
        for gid in (easy_id, medium_id, hard_id):
            if gid is not None:
                ids.add(gid)
    return ids


def _pick_grid(
    session: Session,
    difficulty: str,
    excluded_ids: set[int],
    weight_power: float,
    verbose: bool,
) -> MtgDokuGrid:
    query = select(MtgDokuGrid).where(MtgDokuGrid.difficulty == difficulty)
    if excluded_ids:
        query = query.where(MtgDokuGrid.id.not_in(excluded_ids))

    candidates = session.exec(query).all()

    if not candidates:
        raise RuntimeError(
            f"Aucune grille '{difficulty}' disponible "
            f"(toutes dans le cooldown ou absentes)."
        )

    min_score = min(g.score for g in candidates)
    weights = [(g.score - min_score + 1) ** weight_power for g in candidates]

    chosen = random.choices(candidates, weights=weights, k=1)[0]

    if verbose:
        print(
            f"  [{difficulty}] {len(candidates)} candidates → "
            f"grille #{chosen.id} score={chosen.score:.2f}"
        )

    return chosen


def assign_daily(
    target_date: date,
    cooldown_days: int,
    weight_power: float,
    verbose: bool,
) -> None:
    started_at = utcnow_naive()
    print(f"[{started_at.isoformat()}] assign_daily_doku : démarrage")
    print(f"  Date cible : {target_date}  cooldown={cooldown_days}j  weight_power={weight_power}")

    with Session(engine) as session:
        existing = session.exec(
            select(MtgDokuDailyGame).where(MtgDokuDailyGame.day == target_date)
        ).first()
        if existing:
            print(f"  Partie déjà assignée pour {target_date} (id={existing.id}). Rien à faire.")
            return

        cutoff = target_date - timedelta(days=cooldown_days)
        excluded = _recent_grid_ids(session, cutoff)
        if verbose:
            print(f"  {len(excluded)} grilles exclues (utilisées depuis {cutoff})")

        grids: dict[str, MtgDokuGrid] = {}
        for difficulty in DIFFICULTIES:
            grids[difficulty] = _pick_grid(session, difficulty, excluded, weight_power, verbose)
            # Exclure immédiatement pour éviter de tirer la même grille sur deux difficultés
            excluded.add(grids[difficulty].id)

        game = MtgDokuDailyGame(
            day=target_date,
            easy_grid_id=grids["easy"].id,
            medium_grid_id=grids["medium"].id,
            hard_grid_id=grids["hard"].id,
        )
        session.add(game)
        session.commit()
        session.refresh(game)

        easy_id = grids["easy"].id
        medium_id = grids["medium"].id
        hard_id = grids["hard"].id

    finished_at = utcnow_naive()
    duration = (finished_at - started_at).total_seconds()
    print(
        f"[{finished_at.isoformat()}] assign_daily_doku : terminé en {duration:.1f}s"
        f" | day={target_date}"
        f" easy={easy_id} medium={medium_id} hard={hard_id}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Assigne les grilles MTGDoku du jour.")
    parser.add_argument("--date", type=date.fromisoformat, default=today_paris_date(),
                        help="Date cible (défaut : aujourd'hui, format YYYY-MM-DD)")
    parser.add_argument("--cooldown", type=int, default=COOLDOWN_DAYS,
                        help=f"Jours de cooldown avant réutilisation d'une grille (défaut : {COOLDOWN_DAYS})")
    parser.add_argument("--weight-power", type=float, default=WEIGHT_POWER,
                        help=f"Exposant de pondération par score (1.0=linéaire, 2.0=quadratique, défaut : {WEIGHT_POWER})")
    parser.add_argument("--seed", type=int, default=None,
                        help="Graine aléatoire pour la reproductibilité")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    try:
        assign_daily(args.date, args.cooldown, args.weight_power, args.verbose)
    except RuntimeError as e:
        print(f"[ERREUR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
