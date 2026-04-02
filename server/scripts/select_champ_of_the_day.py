import argparse
from datetime import timedelta

from sqlmodel import Session, select
from sqlalchemy import func

from app.db import engine
from app.models.riftdle.champ_data import ChampData
from app.models.riftdle.daily_game import RiftdleDailyGame, RowColumn
from app.services.riftdle.column_selection import select_columns
from app.utils.time import today_paris_date

RECENT_DAYS = 21  # fenêtre d'exclusion des champions récents


def select_champ_of_the_day(
    force: bool = False,
    forced_columns: list[RowColumn] | None = None,
    verbose: bool = False,
) -> None:
    day = today_paris_date()

    with Session(engine) as session:
        # Vérifier l'existence d'une partie aujourd'hui
        existing = session.exec(
            select(RiftdleDailyGame).where(RiftdleDailyGame.day == day)
        ).first()

        if existing is not None:
            if not force:
                print(f"Une partie existe déjà pour le {day} : {existing.champ_name}. Rien à faire.")
                return
            print(f"Écrasement de la partie existante ({existing.champ_name}).")
            session.delete(existing)
            session.flush()

        # Champions déjà utilisés dans les 3 dernières semaines
        cutoff = day - timedelta(days=RECENT_DAYS)
        recent_names: set[str] = {
            row.champ_name
            for row in session.exec(
                select(RiftdleDailyGame).where(RiftdleDailyGame.day > cutoff)
            ).all()
        }

        if verbose and recent_names:
            print(f"Champions exclus (utilisés depuis le {cutoff}) : {sorted(recent_names)}")

        # Tirage aléatoire en excluant les récents
        query = select(ChampData).order_by(func.random()).limit(1)
        if recent_names:
            query = query.where(ChampData.name.notin_(recent_names))

        champ = session.exec(query).one_or_none()

        if champ is None:
            raise RuntimeError(
                "Aucun champion disponible (tous ont été joués dans les 3 dernières semaines ?)."
            )

        if verbose:
            print(f"\nChampion sélectionné : {champ.name}")

        active_columns = select_columns(champ, forced=forced_columns, verbose=verbose)

        daily_game = RiftdleDailyGame(
            day=day,
            champ_name=champ.name,
            row_columns=[col.value for col in active_columns],
        )
        session.add(daily_game)
        session.commit()

        print(f"Partie du {day} créée : champ={champ.name}, colonnes={[c.value for c in active_columns]}")


if __name__ == "__main__":
    valid_columns = [col.value for col in RowColumn]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Écrase la partie existante du jour si elle existe déjà.",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        choices=valid_columns,
        metavar="COL",
        default=None,
        help=(
            f"Colonnes forcées. Valeurs possibles : {', '.join(valid_columns)}. "
            "Par défaut : sélection automatique."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Affiche le détail des poids et de la sélection des colonnes.",
    )
    args = parser.parse_args()

    parsed_columns = [RowColumn(c) for c in args.columns] if args.columns else None
    select_champ_of_the_day(force=args.force, forced_columns=parsed_columns, verbose=args.verbose)
