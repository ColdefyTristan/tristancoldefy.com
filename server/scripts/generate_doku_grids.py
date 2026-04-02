"""
generate_doku_grids.py

Génère des grilles MTGDoku 3×3 valides à partir du JSON pré-calculé (doku_combos.json).

Structure d'une grille :
  - 3 groupes-lignes et 3 groupes-colonnes, chacun composé de 1 ou 2 conditions
  - 9 cellules = intersection (conditions ligne ∪ conditions colonne)
  - Toutes les cellules doivent être dans le JSON (valides et dans la plage de difficulté)

Algorithme :
  Pour chaque triplet de lignes (R0, R1, R2) :
    valid_cols = voisins[R0] ∩ voisins[R1] ∩ voisins[R2]   ← pruning
    Pour chaque triplet de colonnes dans valid_cols :
      → grille valide garantie

Usage :
  python scripts/generate_doku_grids.py \\
      [--combos scripts/doku_combos.json] \\
      [--output scripts/doku_grids.json] \\
      [--top 5000]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
from dataclasses import dataclass

from pathlib import Path

DEFAULT_COMBOS_PATH = Path(__file__).parent.parent / "data" / "mtgdoku" / "doku_combos.json"
DEFAULT_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "mtgdoku" / "doku_grids.json"
DEFAULT_TOP_N = 5000
DEFAULT_MAX_PAIRS = 300    # meilleures paires conservées pour l'énumération
MIN_PAIR_GROUP_TOTAL = 20  # cartes minimum pour qu'une paire soit un label valide
PROGRESS_EVERY = 25_000


# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CondMeta:
    id: str
    label: str
    category_name: str
    incompatibilities: tuple[str, ...]
    weight: float
    total: int    # cartes matchant cette condition seule
    known: int    # dont edhrec_rank > seuil


@dataclass(frozen=True)
class Group:
    """Un groupe = label d'une ligne ou colonne (1 ou 2 conditions)."""
    conds: tuple[str, ...]
    total: int    # cartes matchant toutes les conditions du groupe
    known: int
    weight: float

    @property
    def cond_set(self) -> frozenset[str]:
        return frozenset(self.conds)


# ---------------------------------------------------------------------------
# Chargement du JSON
# ---------------------------------------------------------------------------

def load_json(path: Path) -> tuple[dict[str, CondMeta], dict[frozenset[str], dict]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cond_meta: dict[str, CondMeta] = {
        c["id"]: CondMeta(
            id=c["id"],
            label=c["label"],
            category_name=c["category_name"],
            incompatibilities=tuple(c["incompatibilities"]),
            weight=c["weight"],
            total=c["total"],
            known=c["known"],
        )
        for c in data["conditions_meta"]
    }

    combo_lookup: dict[frozenset[str], dict] = {
        frozenset(entry["conditions"]): entry
        for entry in data["combos"]
    }

    return cond_meta, combo_lookup


# ---------------------------------------------------------------------------
# Construction des groupes
# ---------------------------------------------------------------------------

def _are_compatible(a: CondMeta, b: CondMeta) -> bool:
    return (
        a.category_name not in b.incompatibilities
        and b.category_name not in a.incompatibilities
    )


def build_groups(
    cond_meta: dict[str, CondMeta],
    combo_lookup: dict[frozenset[str], dict],
    max_pairs: int = DEFAULT_MAX_PAIRS,
) -> list[Group]:
    groups: list[Group] = []

    # Groupes simples (1 condition)
    for meta in cond_meta.values():
        groups.append(Group(
            conds=(meta.id,),
            total=meta.total,
            known=meta.known,
            weight=meta.weight,
        ))

    # Groupes paires (2 conditions) — tirés des combos à 2 conditions du JSON
    # Triées par score (weight × known) et limitées à max_pairs
    pair_candidates: list[Group] = []
    for key, entry in combo_lookup.items():
        if len(key) != 2:
            continue
        if entry["total"] < MIN_PAIR_GROUP_TOTAL:
            continue
        c1_id, c2_id = tuple(key)
        w = cond_meta[c1_id].weight * cond_meta[c2_id].weight
        pair_candidates.append(Group(
            conds=(c1_id, c2_id),
            total=entry["total"],
            known=entry["known"],
            weight=w,
        ))

    random.shuffle(pair_candidates)
    groups.extend(pair_candidates[:max_pairs])

    return groups


# ---------------------------------------------------------------------------
# Index des voisins
# ---------------------------------------------------------------------------

def build_neighbor_index(
    groups: list[Group],
    combo_lookup: dict[frozenset[str], dict],
) -> list[set[int]]:
    """
    neighbors[i] = ensemble des indices j tels que :
      - groups[i] et groups[j] n'ont aucune condition en commun
      - l'union de leurs conditions est dans combo_lookup (cellule valide)
    """
    n = len(groups)
    neighbors: list[set[int]] = [set() for _ in range(n)]

    for i in range(n):
        G = groups[i]
        for j in range(n):
            if i == j:
                continue
            C = groups[j]
            if G.cond_set & C.cond_set:       # conditions chevauchantes
                continue
            if G.cond_set | C.cond_set in combo_lookup:
                neighbors[i].add(j)

    return neighbors


# ---------------------------------------------------------------------------
# Thèmes
# ---------------------------------------------------------------------------

_THEME: dict[str, str] = {
    "monocolor": "color", "bicolor": "color", "at_least_monocolor": "color",
    "cmc": "stat", "cmc_range": "stat",
    "power": "stat", "power_range": "stat",
    "toughness": "stat", "toughness_range": "stat",
    "card_type_permanent": "type", "card_type_non_permanent": "type",
    "keyword": "text", "mention": "text",
}

SAME_THEME_PENALTY = 2.0  # par paire de labels partageant le même thème
PAIR_BONUS = 3          # bonus par label à double condition


def _group_theme(group: Group, cond_meta: dict[str, CondMeta]) -> str:
    """Thème dominant du groupe (premier thème trouvé parmi ses conditions)."""
    for cid in group.conds:
        theme = _THEME.get(cond_meta[cid].category_name)
        if theme:
            return theme
    return "other"


# ---------------------------------------------------------------------------
# Redondances entre conditions
# ---------------------------------------------------------------------------

_NUM_COND_RE = re.compile(r"^(cmc|pow|tou)([=<>])(\d+)$")
_COLOR_MONO_RE = re.compile(r"^c=([wubrg])$")
_COLOR_BI_RE = re.compile(r"^c=([wubrg]{2})$")
_COLOR_ATLEAST_RE = re.compile(r"^c>([wubrg])$")


def _implies(a: str, b: str) -> bool:
    """Retourne True si la condition a ⊆ b (toute carte satisfaisant a satisfait aussi b)."""
    if a == b:
        return True

    ma = _NUM_COND_RE.match(a)
    mb = _NUM_COND_RE.match(b)
    if ma and mb and ma.group(1) == mb.group(1):
        op_a, val_a = ma.group(2), int(ma.group(3))
        op_b, val_b = mb.group(2), int(mb.group(3))
        if op_a == "=" and op_b == "<":
            return val_a < val_b
        if op_a == "=" and op_b == ">":
            return val_a > val_b
        if op_a == "<" and op_b == "<":
            return val_a <= val_b
        if op_a == ">" and op_b == ">":
            return val_a >= val_b
        return False

    mb_at = _COLOR_ATLEAST_RE.match(b)
    if mb_at:
        color_b = mb_at.group(1)
        m_mono = _COLOR_MONO_RE.match(a)
        if m_mono:
            return m_mono.group(1) == color_b
        m_bi = _COLOR_BI_RE.match(a)
        if m_bi:
            return color_b in set(m_bi.group(1))

    return False


def _has_redundant_conditions(groups: list[Group]) -> bool:
    """Retourne True si deux conditions parmi tous les groupes sont en relation de subsomption."""
    all_conds = [cid for g in groups for cid in g.conds]
    for i, a in enumerate(all_conds):
        for b in all_conds[i + 1:]:
            if _implies(a, b) or _implies(b, a):
                return True
    return False


# ---------------------------------------------------------------------------
# Score et difficulté
# ---------------------------------------------------------------------------

_SWEET_SPOT: dict[str, tuple[int, int]] = {
    "hard":   (10,   200),
    "medium": (200,  1000),
    "easy":   (800, 1200),
}


def score_grid(
    cells: list[dict],
    row_groups: list[Group],
    col_groups: list[Group],
    cond_meta: dict[str, CondMeta],
    difficulty_label: str = "medium",
) -> float:
    knowns = [c["known"] for c in cells]

    lo, hi = _SWEET_SPOT[difficulty_label]
    sweet_spot    = sum(lo <= k <= hi for k in knowns)
    median        = statistics.median(knowns)
    accessibility = sum(g.weight for g in row_groups + col_groups)

    # Balance asymétrique : pénalise fortement les cases trop dures, peu les trop faciles
    if median > 0:
        downside = statistics.mean(max(0, median - k) / median for k in knowns)
        upside   = statistics.mean(max(0, k - median) / median for k in knowns)
        balance  = -(downside * 1.0 + upside * 0.3)
    else:
        balance = 0.0

    # Bonus par label à double condition
    pair_bonus = sum(len(g.conds) == 2 for g in row_groups + col_groups) * PAIR_BONUS

    # Pénalité par paire de labels ayant le même thème
    all_groups = row_groups + col_groups
    themes = [_group_theme(g, cond_meta) for g in all_groups]
    same_theme_pairs = sum(
        1 for i in range(len(themes)) for j in range(i + 1, len(themes))
        if themes[i] == themes[j]
    )
    theme_penalty = (same_theme_pairs * SAME_THEME_PENALTY) ** 2

    return (
        sweet_spot * 5      # bonus par case dans la zone idéale pour cette difficulté
        + balance * 5       # pénalise cases trop dures >> cases trop faciles
        + accessibility     # bonus critères lisibles
        + pair_bonus        # bonus labels doubles
        - theme_penalty     # pénalité répétition de thème
    )


def difficulty_grid(cells: list[dict]) -> dict:
    """Retourne un score de difficulté numérique et un label."""
    knowns = [c["known"] for c in cells]

    # Moyenne harmonique : pénalise les cellules très basses sans qu'une seule soit rédhibitoire
    combined = len(knowns) / sum(1 / k for k in knowns if k > 0)

    if combined > 1000:
        label = "easy"
    elif combined > 200:
        label = "medium"
    else:
        label = "hard"

    return {"score": round(combined, 1), "label": label}


# ---------------------------------------------------------------------------
# Barre de progression
# ---------------------------------------------------------------------------

def _print_sampling_progress(found: int, target: int, attempts: int, done: bool = False) -> None:
    BAR_WIDTH = 40
    pct = found / target if target else 1.0
    filled = int(BAR_WIDTH * pct)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    end = "\n" if done else "\r"
    print(f"  [{bar}] {pct:5.1%}  {found:>6}/{target}  tentatives: {attempts}", end=end, flush=True)


# ---------------------------------------------------------------------------
# Sampling des grilles
# ---------------------------------------------------------------------------

def _try_build_grid(
    r0: int, r1: int, r2: int,
    groups: list[Group],
    neighbors: list[set[int]],
    combo_lookup: dict[frozenset[str], dict],
    cond_meta: dict[str, CondMeta],
    col_pool: list[int] | None = None,
) -> tuple[float, dict] | None:
    """Tente de construire une grille valide à partir de 3 indices de lignes.
    col_pool restreint les colonnes candidates (None = tous les voisins valides).
    Retourne (score, grid) ou None si invalide.
    """
    R0, R1, R2 = groups[r0], groups[r1], groups[r2]

    if R0.cond_set & R1.cond_set or R0.cond_set & R2.cond_set or R1.cond_set & R2.cond_set:
        return None

    valid_cols = neighbors[r0] & neighbors[r1] & neighbors[r2]
    all_row_conds = R0.cond_set | R1.cond_set | R2.cond_set
    valid_cols = {j for j in valid_cols if not (groups[j].cond_set & all_row_conds)}

    if col_pool is not None:
        valid_cols &= set(col_pool)

    if len(valid_cols) < 3:
        return None

    c0, c1, c2 = random.sample(list(valid_cols), 3)
    C0, C1, C2 = groups[c0], groups[c1], groups[c2]

    if C0.cond_set & C1.cond_set or C0.cond_set & C2.cond_set or C1.cond_set & C2.cond_set:
        return None

    if _has_redundant_conditions([R0, R1, R2, C0, C1, C2]):
        return None

    row_groups = [R0, R1, R2]
    col_groups = [C0, C1, C2]

    cells_grid: list[list[dict]] = []
    cells_flat: list[dict] = []
    for R in row_groups:
        row_cells = []
        for C in col_groups:
            entry = combo_lookup[R.cond_set | C.cond_set]
            row_cells.append({"total": entry["total"], "known": entry["known"]})
            cells_flat.append(row_cells[-1])
        cells_grid.append(row_cells)

    diff = difficulty_grid(cells_flat)
    sc = score_grid(cells_flat, row_groups, col_groups, cond_meta, diff["label"])
    return sc, _format_grid(sc, diff, row_groups, col_groups, cells_grid, cond_meta)


def sample_grids(
    groups: list[Group],
    neighbors: list[set[int]],
    combo_lookup: dict[frozenset[str], dict],
    cond_meta: dict[str, CondMeta],
    targets: dict[str, int],   # {"easy": N, "medium": N, "hard": N}
    max_attempts: int,
    pairs_ratio: float = 0.1,  # fraction de grilles avec au moins une paire
    max_attempts_pairs: int = 200_000,
) -> list[dict]:
    single_indices = [i for i, g in enumerate(groups) if len(g.conds) == 1]
    pair_indices   = [i for i, g in enumerate(groups) if len(g.conds) == 2]

    buckets: dict[str, list[tuple[float, dict]]] = {"easy": [], "medium": [], "hard": []}
    total_target = sum(targets.values())
    attempts = 0

    print(f"\n  Cibles : " + "  ".join(f"{k}={v}" for k, v in targets.items()))
    print(f"  Passe simples (max {max_attempts} tentatives)...")

    while any(len(buckets[d]) < targets.get(d, 0) for d in buckets) and attempts < max_attempts:
        attempts += 1
        if attempts % PROGRESS_EVERY == 0:
            found = sum(len(v) for v in buckets.values())
            _print_sampling_progress(found, total_target, attempts)

        r0, r1, r2 = random.sample(single_indices, 3)
        result = _try_build_grid(r0, r1, r2, groups, neighbors, combo_lookup, cond_meta)
        if result:
            sc, grid = result
            label = grid["difficulty"]["label"]
            if len(buckets[label]) < targets.get(label, 0):
                buckets[label].append((sc, grid))

    found = sum(len(v) for v in buckets.values())
    _print_sampling_progress(found, total_target, attempts, done=True)
    rate = found / attempts * 100 if attempts else 0
    print(f"\n  Taux de succès : {rate:.1f}%  "
          + "  ".join(f"{k}: {len(v)}/{targets.get(k,0)}" for k, v in buckets.items()))

    # Passe paires : au moins une paire en ligne
    if pair_indices:
        pairs_targets = {d: max(1, round(targets.get(d, 0) * pairs_ratio)) for d in targets}
        pairs_buckets: dict[str, list[tuple[float, dict]]] = {"easy": [], "medium": [], "hard": []}
        attempts_p = 0
        total_pairs = sum(pairs_targets.values())
        print(f"\n  Passe paires (max {max_attempts_pairs} tentatives)...")

        while any(len(pairs_buckets[d]) < pairs_targets.get(d, 0) for d in pairs_buckets) \
                and attempts_p < max_attempts_pairs:
            attempts_p += 1
            r0 = random.choice(pair_indices)
            r1, r2 = random.sample(single_indices, 2)
            result = _try_build_grid(r0, r1, r2, groups, neighbors, combo_lookup, cond_meta)
            if result:
                sc, grid = result
                label = grid["difficulty"]["label"]
                if len(pairs_buckets[label]) < pairs_targets.get(label, 0):
                    pairs_buckets[label].append((sc, grid))

        found_p = sum(len(v) for v in pairs_buckets.values())
        rate_p = found_p / attempts_p * 100 if attempts_p else 0
        print(f"  Taux de succès : {rate_p:.1f}%  "
              + "  ".join(f"{k}: {len(v)}/{pairs_targets.get(k,0)}" for k, v in pairs_buckets.items()))

        for d in buckets:
            buckets[d].extend(pairs_buckets[d])

    all_results = []
    for d in ("easy", "medium", "hard"):
        all_results.extend(sorted(buckets[d], key=lambda x: x[0], reverse=True))
    return [g for _, g in all_results]


# ---------------------------------------------------------------------------
# Format de sortie
# ---------------------------------------------------------------------------

def _format_conditions(group: Group, cond_meta: dict[str, CondMeta]) -> list[dict]:
    return [
        {
            "id": cid,
            "label": cond_meta[cid].label,
            "weight": cond_meta[cid].weight,
            "total": cond_meta[cid].total,
            "known": cond_meta[cid].known,
        }
        for cid in group.conds
    ]


def _format_grid(
    score: float,
    diff: dict,
    row_groups: list[Group],
    col_groups: list[Group],
    cells_grid: list[list[dict]],
    cond_meta: dict[str, CondMeta],
) -> dict:
    cells_flat = [c for row in cells_grid for c in row]
    knowns = [c["known"] for c in cells_flat]
    return {
        "score": round(score, 2),
        "difficulty": diff,
        "min_known": min(knowns),
        "min_total": min(c["total"] for c in cells_flat),
        "rows": [
            {
                "conditions": _format_conditions(g, cond_meta),
                "total": g.total,
                "known": g.known,
            }
            for g in row_groups
        ],
        "cols": [
            {
                "conditions": _format_conditions(g, cond_meta),
                "total": g.total,
                "known": g.known,
            }
            for g in col_groups
        ],
        "cells": cells_grid,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Génère des grilles MTGDoku 3×3.")
    parser.add_argument("--combos", type=Path, default=DEFAULT_COMBOS_PATH,
                        help="Chemin vers doku_combos.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH,
                        help="Chemin de sortie pour doku_grids.json")
    parser.add_argument("--easy", type=int, default=500,
                        help="Nombre de grilles faciles à générer")
    parser.add_argument("--medium", type=int, default=1000,
                        help="Nombre de grilles moyennes à générer")
    parser.add_argument("--hard", type=int, default=500,
                        help="Nombre de grilles difficiles à générer")
    parser.add_argument("--max-attempts", type=int, default=500_000,
                        help="Nombre maximum de tentatives aléatoires")
    parser.add_argument("--pairs-ratio", type=float, default=0.1,
                        help="Fraction de chaque bucket réservée aux grilles avec paires (0-1)")
    parser.add_argument("--max-attempts-pairs", type=int, default=200_000,
                        help="Nombre maximum de tentatives pour la passe paires")
    parser.add_argument("--max-pairs", type=int, default=DEFAULT_MAX_PAIRS,
                        help="Nombre maximum de groupes-paires à inclure (sélection aléatoire)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Graine aléatoire pour la reproductibilité")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        print(f"Graine aléatoire : {args.seed}")

    print(f"Chargement de {args.combos}...")
    cond_meta, combo_lookup = load_json(args.combos)
    print(f"  {len(cond_meta)} conditions, {len(combo_lookup)} combinaisons valides.")

    print("\nConstruction des groupes...")
    groups = build_groups(cond_meta, combo_lookup, max_pairs=args.max_pairs)
    single = sum(1 for g in groups if len(g.conds) == 1)
    pairs  = sum(1 for g in groups if len(g.conds) == 2)
    print(f"  {single} groupes simples + {pairs} groupes paires (top {args.max_pairs}) = {len(groups)} total")

    print("\nConstruction de l'index des voisins...")
    neighbors = build_neighbor_index(groups, combo_lookup)
    avg_neighbors = sum(len(v) for v in neighbors) / len(neighbors) if neighbors else 0
    print(f"  Moyenne de {avg_neighbors:.0f} voisins par groupe")

    targets = {"easy": args.easy, "medium": args.medium, "hard": args.hard}
    grids = sample_grids(
        groups, neighbors, combo_lookup, cond_meta,
        targets=targets,
        max_attempts=args.max_attempts,
        pairs_ratio=args.pairs_ratio,
        max_attempts_pairs=args.max_attempts_pairs,
    )

    print(f"\n{len(grids)} grilles générées.")
    print(f"Sauvegarde dans {args.output}...")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(grids, f, ensure_ascii=False, indent=2)

    print("Terminé.")


if __name__ == "__main__":
    main()
