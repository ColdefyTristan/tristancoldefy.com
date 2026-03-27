"""
show_doku_grids.py

Affiche et pioche des grilles MTGDoku depuis doku_grids.json.

Usage :
  # Afficher une grille aléatoire
  python -m scripts.show_doku_grids

  # Piocher par difficulté
  python -m scripts.show_doku_grids --pick hard:3 medium:2

  # Afficher une grille précise (index)
  python -m scripts.show_doku_grids --index 42

  # Filtrer l'affichage
  python -m scripts.show_doku_grids --pick easy:1 --min-score 10
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

DEFAULT_GRIDS_PATH = Path(__file__).parent / "doku_grids.json"

def load_grids(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _center(text: str, width: int) -> str:
    """Centre le texte dans width (sans compter les codes ANSI)."""
    pad = max(0, width - len(text))
    return " " * (pad // 2) + text + " " * (pad - pad // 2)


def display_grid(grid: dict) -> None:
    diff  = grid["difficulty"]
    score = grid["score"]
    cells = grid["cells"]

    col_labels = [" + ".join(c["label"] for c in g["conditions"]) for g in grid["cols"]]
    row_labels = [" + ".join(c["label"] for c in g["conditions"]) for g in grid["rows"]]

    # Contenu de chaque cellule : deux lignes
    #   ligne 1 : known  ligne 2 : / total
    cell_lines = [
        [f"{c['known']} known", f"/ {c['total']} total"]
        for row in cells for c in row
    ]

    CELL_W = max(20, max(len(l) for cl in cell_lines for l in cl) + 6)
    ROW_W  = max(20, max(len(l) for l in row_labels) + 6)
    CELL_W = max(CELL_W, max(len(l) for l in col_labels) + 6)

    sep       = "+" + ("-" * ROW_W) + ("+" + "-" * CELL_W) * 3 + "+"
    header_sep = "+" + ("=" * ROW_W) + ("+" + "=" * CELL_W) * 3 + "+"

    print()
    print(f"  Score : {score:.2f}   Difficulté : {diff['label'].upper()} (score {diff['score']:.0f})")
    print()

    # En-tête colonnes
    print(sep)
    print(f"|{'':>{ROW_W}}", end="")
    for label in col_labels:
        print(f"|{_center(label, CELL_W)}", end="")
    print("|")
    print(header_sep)

    # Lignes de données
    for r, row_label in enumerate(row_labels):
        # Ligne vide au-dessus
        print(f"|{'':>{ROW_W}}" + (f"|{'':>{CELL_W}}") * 3 + "|")

        # Ligne 1 : label de ligne + known de chaque cellule
        print(f"|{_center(row_label, ROW_W)}", end="")
        for c in range(3):
            cell = cells[r][c]
            text = f"{cell['known']} known"
            print(f"|{_center(text, CELL_W)}", end="")
        print("|")

        # Ligne vide
        print(f"|{'':>{ROW_W}}" + (f"|{'':>{CELL_W}}") * 3 + "|")

        print(sep)
    print()


def pick_grids(
    grids: list[dict],
    criteria: list[str],
    min_score: float,
    by_score: bool = False,
) -> list[dict]:
    """
    criteria : liste de "label:n", ex ["hard:3", "medium:2"]
    by_score  : si True, prend les N meilleures par score au lieu d'un tirage aléatoire
    """
    by_diff: dict[str, list[dict]] = {"easy": [], "medium": [], "hard": []}
    for g in grids:
        if g["score"] >= min_score:
            label = g["difficulty"]["label"]
            by_diff[label].append(g)

    if by_score:
        for label in by_diff:
            by_diff[label].sort(key=lambda g: g["score"], reverse=True)

    picked: list[dict] = []
    for criterion in criteria:
        label, n_str = criterion.split(":")
        n = int(n_str)
        pool = by_diff.get(label, [])
        if len(pool) < n:
            print(f"Attention : seulement {len(pool)} grilles '{label}' disponibles (demandé {n}).")
        if by_score:
            picked.extend(pool[:n])
        else:
            picked.extend(random.sample(pool, min(n, len(pool))))

    return picked


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiche des grilles MTGDoku.")
    parser.add_argument("--grids", type=Path, default=DEFAULT_GRIDS_PATH)
    parser.add_argument("--pick", nargs="+", metavar="LABEL:N",
                        help="Piocher N grilles par difficulté, ex: hard:3 medium:2")
    parser.add_argument("--index", type=int, default=None,
                        help="Afficher la grille à cet index")
    parser.add_argument("--min-score", type=float, default=float("-inf"),
                        help="Score minimum pour le filtrage")
    parser.add_argument("--by-score", action="store_true",
                        help="Trier par score plutôt que tirer aléatoirement")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    grids = load_grids(args.grids)
    print(f"{len(grids)} grilles chargées.")

    if args.index is not None:
        display_grid(grids[args.index])
        return

    if args.pick:
        selected = pick_grids(grids, args.pick, args.min_score, by_score=args.by_score)
        for g in selected:
            display_grid(g)
        print(f"\n{len(selected)} grille(s) affichée(s).")
        return

    # Par défaut : une grille aléatoire
    display_grid(random.choice(grids))


if __name__ == "__main__":
    main()
