"""
Sélection pondérée des colonnes pour la partie du jour.

Algorithme :
  1. On part de toutes les colonnes.
  2. À chaque itération on tente de retirer la "pire" colonne
     (tirage inversement proportionnel aux poids).
  3. La probabilité de retrait diminue avec le nombre de colonnes :
       > 7  → 100 %   (obligatoire)
       == 7 → 80 %
       == 6 → 30 %
       <= 5 → on s'arrête
  4. Les règles dures bloquent certains retraits (voir _is_removable).
"""

import random
from collections.abc import Callable

from app.models.riftdle.champ_data import ChampData
from app.models.riftdle.daily_game import ALL_ROW_COLUMNS, RowColumn

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

MAX_COLUMNS = 8
MIN_COLUMNS = 6

# Probabilité de retrait selon le nombre de colonnes actives
REMOVAL_PROB: dict[int, float] = {8: 0.8,7:0.3}

# Groupes pour les règles dures
_STAT_COLS = frozenset({RowColumn.mobility, RowColumn.randomness, RowColumn.cc_quantity})
_PERSONALITY_COLS = frozenset({RowColumn.intension, RowColumn.vote, RowColumn.regime, RowColumn.pilosite})

# ---------------------------------------------------------------------------
# Poids par défaut
# ---------------------------------------------------------------------------

DEFAULT_BASE_WEIGHTS: dict[RowColumn, float] = {
    RowColumn.skin_number:    1.0,
    RowColumn.colorwheel:     1.0,
    RowColumn.family_mastery: 1.0,
    RowColumn.mobility:       1.0,
    RowColumn.randomness:     1.0,
    RowColumn.cc_quantity:    1.0,
    RowColumn.intension:      0.9,  # légèrement abaissé pour équilibrer
    RowColumn.vote:           1.0,
    RowColumn.regime:         1.0,
    RowColumn.pilosite:       1.0,
}

# Modificateurs : ChampData → multiplicateur (appliqué sur le poids de base)
WeightModifiers = dict[RowColumn, Callable[[ChampData], float]]

DEFAULT_WEIGHT_MODIFIERS: WeightModifiers = {
    # Nombre de skins : valeur intermédiaire commune = un peu pénalisée
    RowColumn.skin_number: lambda c: 0.7 if 7 <= c.skin_number <= 16 else 1.0,
    # Joué par : personne → très pénalisé ; ≥ 3 joueurs → un peu pénalisé
    RowColumn.family_mastery: lambda c: (
        0.3 if not c.family_mastery else
        0.7 if len(c.family_mastery) >= 3 else
        1.0
    ),
    # Stats : bucket central = moins informatif
    RowColumn.mobility:    lambda c: 0.7 if 48  <= c.mobility    <= 109 else 1.0,
    RowColumn.randomness:  lambda c: 0.7 if 38  <= c.randomness  <= 134 else 1.0,
    RowColumn.cc_quantity: lambda c: 0.7 if 44  <= c.cc_quantity <= 127 else 1.0,
    # Vote : "idk" = très pénalisé
    RowColumn.vote: lambda c: 0.2 if any(v.lower() == "idk" for v in c.vote) else 1.0,
    # Régime : valeurs communes = un peu pénalisées
    RowColumn.regime: lambda c: (
        0.7 if any(v in c.regime for v in ("Haute gastronomie", "Cuisine soi même")) else 1.0
    ),
    # Pilosité : "normale" = un peu pénalisée
    RowColumn.pilosite: lambda c: 0.7 if "Pilositée normale" in c.pilosite else 1.0,
}

# ---------------------------------------------------------------------------
# Règles dures : détermine si une colonne peut être retirée
# ---------------------------------------------------------------------------

def _is_removable(col: RowColumn, columns: list[RowColumn], forced: frozenset[RowColumn]) -> bool:
    if col in forced:
        return False
    if col == RowColumn.colorwheel:
        return False

    remaining = [c for c in columns if c != col]

    if col in _STAT_COLS and sum(1 for c in remaining if c in _STAT_COLS) < 2:
        return False

    if col in _PERSONALITY_COLS and sum(1 for c in remaining if c in _PERSONALITY_COLS) < 1:
        return False

    return True

# ---------------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------------

def _print_weights(
    weights: dict[RowColumn, float],
    base_weights: dict[RowColumn, float],
    forced_set: frozenset[RowColumn],
    champ: ChampData,
    wm: WeightModifiers,
) -> None:
    col_w = max(len(c.value) for c in ALL_ROW_COLUMNS) + 2
    print("\n── Poids des colonnes ─────────────────────────────────────")
    print(f"  {'Colonne':<{col_w}} {'Base':>6}  {'×Modif':>7}  {'Final':>6}  Flags")
    print(f"  {'-'*col_w}  {'------':>6}  {'-------':>7}  {'------':>6}")
    for col in ALL_ROW_COLUMNS:
        base = base_weights.get(col, 1.0)
        modifier_fn = wm.get(col)
        mod = modifier_fn(champ) if modifier_fn else 1.0
        final = weights[col]
        flags = []
        if col in forced_set:
            flags.append("FORCÉE")
        if col == RowColumn.colorwheel and col not in forced_set:
            flags.append("toujours présente")
        flag_str = ", ".join(flags)
        print(f"  {col.value:<{col_w}} {base:>6.3f}  ×{mod:>6.3f}  {final:>6.3f}  {flag_str}")
    print()


def _print_result(
    final: list[RowColumn],
    removed: list[RowColumn],
) -> None:
    print("── Sélection finale ────────────────────────────────────────")
    print(f"  {len(final)} colonne(s) retenues :")
    for col in final:
        print(f"    ✓  {col.value}")
    if removed:
        print(f"  {len(removed)} colonne(s) retirée(s) :")
        for col in removed:
            print(f"    ✗  {col.value}")
    print("────────────────────────────────────────────────────────────\n")

# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def select_columns(
    champ: ChampData,
    forced: list[RowColumn] | None = None,
    base_weights: dict[RowColumn, float] | None = None,
    weight_modifiers: WeightModifiers | None = None,
    verbose: bool = False,
) -> list[RowColumn]:
    """
    Sélectionne les colonnes à afficher pour la partie du jour.

    Args:
        champ:            Champion du jour (ses données orientent les poids).
        forced:           Colonnes garanties présentes (jamais retirées).
        base_weights:     Poids de base par colonne (remplace DEFAULT_BASE_WEIGHTS).
        weight_modifiers: Modificateurs par colonne (remplace DEFAULT_WEIGHT_MODIFIERS).
        verbose:          Affiche les poids et la sélection finale.

    Returns:
        Liste de RowColumn entre MIN_COLUMNS et MAX_COLUMNS éléments.

    Raises:
        ValueError: Si trop de colonnes forcées (> MAX_COLUMNS).
    """
    forced_set = frozenset(forced or []) | {RowColumn.colorwheel}

    if len(forced_set) > MAX_COLUMNS:
        raise ValueError(
            f"Trop de colonnes forcées : {len(forced_set)} > MAX_COLUMNS ({MAX_COLUMNS}). "
            f"Colonnes : {[c.value for c in forced_set]}"
        )

    bw = base_weights if base_weights is not None else DEFAULT_BASE_WEIGHTS
    wm = weight_modifiers if weight_modifiers is not None else DEFAULT_WEIGHT_MODIFIERS

    # Calcul des poids finaux
    weights: dict[RowColumn, float] = {}
    for col in ALL_ROW_COLUMNS:
        w = bw.get(col, 1.0)
        modifier = wm.get(col)
        if modifier is not None:
            w *= modifier(champ)
        weights[col] = max(w, 0.01)

    if verbose:
        _print_weights(weights, bw, forced_set, champ, wm)

    columns: list[RowColumn] = list(ALL_ROW_COLUMNS)
    initial = list(columns)

    while len(columns) > MIN_COLUMNS:
        n = len(columns)

        if n > MAX_COLUMNS:
            prob = 1.0
        else:
            prob = REMOVAL_PROB.get(n, 0.0)

        if prob == 0.0:
            break

        if random.random() >= prob:
            break

        removable = [c for c in columns if _is_removable(c, columns, forced_set)]
        if not removable:
            break

        inv_weights = [1.0 / weights[c] for c in removable]
        chosen = random.choices(removable, weights=inv_weights, k=1)[0]
        columns.remove(chosen)

    if verbose:
        removed = [c for c in initial if c not in columns]
        _print_result(columns, removed)

    return columns
