"""
compute_doku_combos.py

Pré-calcule toutes les combinaisons valides de catégories MTGDoku (taille 2, 3, 4).

Pour chaque combinaison compatible et dans la plage de difficulté souhaitée :
  - total : nombre de cartes correspondantes
  - known : nombre de cartes avec edhrec_rank IS NOT NULL AND edhrec_rank > EDHREC_THRESHOLD
             (élimine les cartes inconnues des joueurs)

L'index inversé est construit en mémoire : chaque catégorie mappe vers un frozenset
d'oracle_ids. Compter une intersection de k catégories = len(set1 & set2 & ... & setk).

Usage :
  DATABASE_URL=postgresql://user:pass@host/db python tools/compute_doku_combos.py

Sortie : tools/doku_combos.json
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

EDHREC_THRESHOLD = 1000   # edhrec_rank > seuil = carte suffisamment connue
COMBO_SIZES = [2, 3, 4]
MIN_TOTAL = 10             # trop peu de réponses → cellule injouable
MAX_TOTAL = 5000           # trop de réponses → trop facile
MIN_KNOWN = 10             # au moins N cartes "connues" dans l'intersection

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "mtgdoku" / "doku_combos.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _try_int(s: str | None) -> int | None:
    try:
        return int(s) if s is not None else None
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Définition des conditions
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    id: str
    label: str
    category_name: str
    incompatibilities: list[str]   # noms de category_name incompatibles
    weight: float
    predicate: Callable[[dict], bool]

    def __repr__(self) -> str:
        return self.id


_COLOR_MAP   = {"w": "W", "u": "U", "b": "B", "r": "R", "g": "G"}
_COLOR_LABEL = {"w": "White", "u": "Blue", "b": "Black", "r": "Red", "g": "Green", "c": "Colorless"}


def _build_conditions() -> list[Condition]:
    conds: list[Condition] = []

    monocolor = ["w", "u", "b", "r", "g", "c"]
    bicolor_pairs = list(combinations(["w", "u", "b", "r", "g"], 2))

    # -- Couleur exacte monocolor ----------------------------------------
    for c in monocolor:
        if c == "c":
            pred = lambda card: len(card["colors"]) == 0
        else:
            col = _COLOR_MAP[c]
            pred = lambda card, col=col: len(card["colors"]) == 1 and col in card["colors"]
        conds.append(Condition(
            id=f"c={c}",
            label=f"{_COLOR_LABEL[c]} only",
            category_name="monocolor",
            incompatibilities=["bicolor", "at_least_monocolor"],
            weight=1.0,
            predicate=pred,
        ))

    # -- Couleur exacte bicolor ------------------------------------------
    for c1, c2 in bicolor_pairs:
        col1, col2 = _COLOR_MAP[c1], _COLOR_MAP[c2]
        pred = lambda card, col1=col1, col2=col2: (
            len(card["colors"]) == 2 and col1 in card["colors"] and col2 in card["colors"]
        )
        conds.append(Condition(
            id=f"c={c1}{c2}",
            label=f"{_COLOR_LABEL[c1]}/{_COLOR_LABEL[c2]}",
            category_name="bicolor",
            incompatibilities=["monocolor", "bicolor", "at_least_monocolor"],
            weight=0.7,
            predicate=pred,
        ))

    # -- Au moins cette couleur ------------------------------------------
    for c in ["w", "u", "b", "r", "g"]:
        col = _COLOR_MAP[c]
        pred = lambda card, col=col: col in card["color_identity"]
        conds.append(Condition(
            id=f"c>{c}",
            label=f"Uses {_COLOR_LABEL[c]}",
            category_name="at_least_monocolor",
            incompatibilities=["monocolor", "bicolor", "at_least_monocolor"],
            weight=0.8,
            predicate=pred,
        ))

    # -- CMC exact -------------------------------------------------------
    for i in range(1, 6):
        conds.append(Condition(
            id=f"cmc={i}",
            label=f"CMC {i}",
            category_name="cmc",
            incompatibilities=["cmc", "cmc_range"],
            weight=1.0,
            predicate=lambda card, i=i: card["converted_mana_cost"] == i,
        ))

    # -- CMC range -------------------------------------------------------
    for n in [3, 4]:
        conds.append(Condition(
            id=f"cmc<{n}",
            label=f"CMC < {n}",
            category_name="cmc_range",
            incompatibilities=["cmc", "cmc_range"],
            weight=1.0,
            predicate=lambda card, n=n: card["converted_mana_cost"] < n,
        ))
    for n in [2, 3, 4]:
        conds.append(Condition(
            id=f"cmc>{n}",
            label=f"CMC > {n}",
            category_name="cmc_range",
            incompatibilities=["cmc", "cmc_range"],
            weight=0.9,
            predicate=lambda card, n=n: card["converted_mana_cost"] > n,
        ))

    # -- Types permanents ------------------------------------------------
    for t in ["Creature", "Enchantment", "Artifact", "Land"]:
        conds.append(Condition(
            id=f"type={t.lower()}",
            label=t,
            category_name="card_type_permanent",
            incompatibilities=["card_type_non_permanent"],
            weight=0.8,
            predicate=lambda card, t=t: bool(card["type_line"]) and t in card["type_line"],
        ))

    # -- Types non-permanents / supertype --------------------------------
    for t in ["Instant", "Sorcery", "Legendary"]:
        conds.append(Condition(
            id=f"type={t.lower()}",
            label=t,
            category_name="card_type_non_permanent",
            incompatibilities=["card_type_permanent", "power", "toughness"],
            weight=0.8,
            predicate=lambda card, t=t: bool(card["type_line"]) and t in card["type_line"],
        ))

    # -- Keywords (oracle text) ------------------------------------------
    for k in ["flying", "reach", "indestructible", "trample", "haste", "deathtouch", "lifelink"]:
        conds.append(Condition(
            id=f'o:"{k}"',
            label=k.capitalize(),
            category_name="keyword",
            incompatibilities=[],
            weight=0.5,
            predicate=lambda card, k=k: bool(card["oracle_text"]) and k in card["oracle_text"].lower(),
        ))

    # -- Mentions (oracle text) ------------------------------------------
    for m in ["exile", "graveyard", "discard", "hand", "library", "scry",
              "+1/+1", "-1/-1", "token", "sacrifice"]:
        conds.append(Condition(
            id=f'o:"{m}"',
            label=m.capitalize(),
            category_name="mention",
            incompatibilities=[],
            weight=0.5,
            predicate=lambda card, m=m: bool(card["oracle_text"]) and m in card["oracle_text"].lower(),
        ))

    # -- Power exact -----------------------------------------------------
    for i in range(6):
        conds.append(Condition(
            id=f"pow={i}",
            label=f"Power {i}",
            category_name="power",
            incompatibilities=["card_type_non_permanent", "power", "power_range"],
            weight=0.3,
            predicate=lambda card, i=i: card["power"] == str(i),
        ))

    # -- Power range -----------------------------------------------------
    for n in [3, 4]:
        conds.append(Condition(
            id=f"pow<{n}",
            label=f"Power < {n}",
            category_name="power_range",
            incompatibilities=["card_type_non_permanent", "power", "power_range"],
            weight=0.4,
            predicate=lambda card, n=n: _try_int(card["power"]) is not None and _try_int(card["power"]) < n,
        ))
    for n in [2, 3, 4]:
        conds.append(Condition(
            id=f"pow>{n}",
            label=f"Power > {n}",
            category_name="power_range",
            incompatibilities=["card_type_non_permanent", "power", "power_range"],
            weight=0.4,
            predicate=lambda card, n=n: _try_int(card["power"]) is not None and _try_int(card["power"]) > n,
        ))

    # -- Toughness exact -------------------------------------------------
    for i in range(6):
        conds.append(Condition(
            id=f"tou={i}",
            label=f"Toughness {i}",
            category_name="toughness",
            incompatibilities=["card_type_non_permanent", "toughness", "toughness_range"],
            weight=0.3,
            predicate=lambda card, i=i: card["toughness"] == str(i),
        ))

    # -- Toughness range -------------------------------------------------
    for n in [3, 4]:
        conds.append(Condition(
            id=f"tou<{n}",
            label=f"Toughness < {n}",
            category_name="toughness_range",
            incompatibilities=["card_type_non_permanent", "toughness", "toughness_range"],
            weight=0.4,
            predicate=lambda card, n=n: _try_int(card["toughness"]) is not None and _try_int(card["toughness"]) < n,
        ))
    for n in [2, 3, 4]:
        conds.append(Condition(
            id=f"tou>{n}",
            label=f"Toughness > {n}",
            category_name="toughness_range",
            incompatibilities=["card_type_non_permanent", "toughness", "toughness_range"],
            weight=0.4,
            predicate=lambda card, n=n: _try_int(card["toughness"]) is not None and _try_int(card["toughness"]) > n,
        ))

    return conds


ALL_CONDITIONS = _build_conditions()


# ---------------------------------------------------------------------------
# Compatibilité
# ---------------------------------------------------------------------------

def _are_compatible(a: Condition, b: Condition) -> bool:
    return (
        a.category_name not in b.incompatibilities
        and b.category_name not in a.incompatibilities
    )


# Pré-calcul de la matrice de compatibilité pour éviter les répétitions
_COMPAT: dict[tuple[int, int], bool] = {}

def _precompute_compat(conds: list[Condition]) -> None:
    for i, a in enumerate(conds):
        for j, b in enumerate(conds):
            if i < j:
                _COMPAT[(i, j)] = _are_compatible(a, b)

def _combo_is_valid(indices: tuple[int, ...]) -> bool:
    return all(_COMPAT[(i, j)] for i, j in combinations(indices, 2))


# ---------------------------------------------------------------------------
# Chargement DB
# ---------------------------------------------------------------------------

def _psycopg_url(url: str) -> str:
    """Convertit l'URL SQLAlchemy (postgresql+psycopg://) en URL psycopg standard."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def load_cards(db_url: str) -> list[dict]:
    import psycopg  # type: ignore
    with psycopg.connect(_psycopg_url(db_url)) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT oracle_id, colors, color_identity, converted_mana_cost,
                       type_line, oracle_text, power, toughness, edhrec_rank
                FROM mtg_card
            """)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Index inversé
# ---------------------------------------------------------------------------

def build_index(
    cards: list[dict],
    conds: list[Condition],
) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    """
    Retourne :
      index      : condition_id → frozenset d'oracle_ids correspondants
      known_ids  : frozenset des oracle_ids avec edhrec_rank > EDHREC_THRESHOLD
    """
    known_ids: frozenset[str] = frozenset(
        card["oracle_id"]
        for card in cards
        if card["edhrec_rank"] is not None and card["edhrec_rank"] > EDHREC_THRESHOLD
    )

    index: dict[str, frozenset[str]] = {}
    for cond in conds:
        index[cond.id] = frozenset(
            card["oracle_id"] for card in cards if cond.predicate(card)
        )

    return index, known_ids


# ---------------------------------------------------------------------------
# Barre de progression
# ---------------------------------------------------------------------------

def _print_progress(step: int, total: int, n_valid: int, done: bool = False) -> None:
    BAR_WIDTH = 40
    pct = step / total
    filled = int(BAR_WIDTH * pct)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    end = "\n" if done else "\r"
    print(f"  [{bar}] {pct:5.1%}  {step:>7}/{total}  valides: {n_valid}", end=end, flush=True)


# ---------------------------------------------------------------------------
# Calcul des combinaisons
# ---------------------------------------------------------------------------

def compute_combos(
    conds: list[Condition],
    index: dict[str, frozenset[str]],
    known_ids: frozenset[str],
) -> list[dict]:
    results: list[dict] = []

    for k in COMBO_SIZES:
        all_indices = list(combinations(range(len(conds)), k))
        total_iter = len(all_indices)
        print(f"\nCombinaisons de taille {k}  (C({len(conds)},{k}) = {total_iter} à vérifier)...")
        n_checked = n_valid = 0

        for step, indices in enumerate(all_indices, 1):
            _print_progress(step, total_iter, n_valid)

            if not _combo_is_valid(indices):
                continue

            n_checked += 1
            combo = [conds[i] for i in indices]

            # Intersection incrémentale avec early exit
            matching = index[combo[0].id]
            for cond in combo[1:]:
                matching = matching & index[cond.id]
                if len(matching) < MIN_TOTAL:
                    matching = frozenset()
                    break

            total = len(matching)
            if total < MIN_TOTAL or total > MAX_TOTAL:
                continue

            known = len(matching & known_ids)
            if known < MIN_KNOWN:
                continue

            n_valid += 1
            results.append({
                "conditions": [c.id for c in combo],
                "total": total,
                "known": known,
                "weight": round(math.prod(c.weight for c in combo), 4),
            })

        _print_progress(total_iter, total_iter, n_valid, done=True)
        print(f"\n  Vérifiées (compatibles) : {n_checked}")
        print(f"  Valides                 : {n_valid}")

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not DATABASE_URL:
        raise SystemExit("Erreur : la variable d'environnement DATABASE_URL est requise.")

    print("Chargement des cartes depuis la DB...")
    cards = load_cards(DATABASE_URL)
    print(f"  {len(cards)} cartes chargées.")

    print(f"\nConstruction de l'index inversé ({len(ALL_CONDITIONS)} conditions)...")
    index, known_ids = build_index(cards, ALL_CONDITIONS)
    print(f"  {len(known_ids)} cartes avec edhrec_rank > {EDHREC_THRESHOLD}.")

    conditions_meta = []
    for cond in ALL_CONDITIONS:
        ids = index[cond.id]
        conditions_meta.append({
            "id": cond.id,
            "label": cond.label,
            "category_name": cond.category_name,
            "incompatibilities": cond.incompatibilities,
            "weight": cond.weight,
            "total": len(ids),
            "known": len(ids & known_ids),
        })
        print(f"  [{cond.id:25s}] {len(ids):5d} cartes")

    print(f"\nPré-calcul de la matrice de compatibilité...")
    _precompute_compat(ALL_CONDITIONS)

    combos = compute_combos(ALL_CONDITIONS, index, known_ids)

    output = {
        "conditions_meta": conditions_meta,
        "combos": combos,
    }

    print(f"\nTotal combinaisons valides : {len(combos)}")
    print(f"Sauvegarde dans {OUTPUT_PATH}...")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Terminé.")


if __name__ == "__main__":
    main()
