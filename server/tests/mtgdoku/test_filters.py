"""Tests d'intégration pour les filtres de catégorie MTGDoku et check_card_for_cell.

Deux cartes de référence :
  - Thalia, Guardian of Thraben  (9b7f1d05-707c-4ed3-9f0e-8ced1232c2ee)
    mono-blanc, Legendary Creature, 2/1, CMC 2
  - Find // Finality             (212af747-2ac1-4d33-9456-8b3cc8988f5d)
    B/G Sorcery, CMC 8, mentionne graveyard et +1/+1
"""
import hashlib
import json
import uuid

import pytest
from sqlmodel import Session, func, select

from app.models.mtg.mtg_card import MtgCard
from app.models.mtg.mtgdoku_grid import MtgDokuGrid
from app.services.mtg.doku_categories import CATEGORIES_BY_ID
from app.services.mtg.doku_game import check_card_for_cell

THALIA_ID = "9b7f1d05-707c-4ed3-9f0e-8ced1232c2ee"
FIND_FINALITY_ID = "212af747-2ac1-4d33-9456-8b3cc8988f5d"


# ---------------------------------------------------------------------------
# Fixtures — cartes
# ---------------------------------------------------------------------------


@pytest.fixture
def thalia(session):
    """Thalia, Guardian of Thraben — mono-blanc, Legendary Creature 2/1, CMC 2."""
    card = MtgCard(
        oracle_id=THALIA_ID,
        name="Thalia, Guardian of Thraben",
        colors=["W"],
        color_identity=["W"],
        converted_mana_cost=2,
        type_line="Legendary Creature — Human Soldier",
        oracle_text=(
            "First strike. Nontoken spells cost {1} more to cast "
            "for each player who doesn't control Thalia, Guardian of Thraben."
        ),
        power="2",
        toughness="1",
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@pytest.fixture
def find_finality(session):
    """Find // Finality — B/G Sorcery, CMC 8, graveyard + +1/+1."""
    card = MtgCard(
        oracle_id=FIND_FINALITY_ID,
        name="Find // Finality",
        colors=["B", "G"],
        color_identity=["B", "G"],
        converted_mana_cost=8,
        type_line="Sorcery",
        oracle_text=(
            "Find — Return up to two target creature cards from your graveyard to your hand.\n"
            "Finality — Put a +1/+1 counter on each creature you control, then destroy all "
            "creatures with power less than or equal to your greatest creature's power."
        ),
        power=None,
        toughness=None,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count(session: Session, oracle_id: str, *filter_ids: str) -> int:
    """Applique les filtres de catégorie sur une carte et retourne 0 ou 1."""
    filters = [CATEGORIES_BY_ID[fid].filter_expr() for fid in filter_ids]
    return session.exec(
        select(func.count())
        .select_from(MtgCard)
        .where(MtgCard.oracle_id == oracle_id, *filters)
    ).one()


def _make_grid(
    session: Session,
    row_conditions: list[list[str]],
    col_conditions: list[list[str]],
) -> MtgDokuGrid:
    """Construit un MtgDokuGrid 3×3 minimal avec les IDs de conditions donnés."""

    def _cond_objs(ids: list[str]) -> list[dict]:
        return [{"id": cid, "label": cid, "weight": 1.0, "total": 100, "known": 50} for cid in ids]

    def _slots(conds_per_slot: list[list[str]]) -> list[dict]:
        slots = []
        for i in range(3):
            ids = conds_per_slot[i] if i < len(conds_per_slot) else []
            slots.append({"conditions": _cond_objs(ids), "total": 100, "known": 50})
        return slots

    grid_data = {
        "score": 1.0,
        "difficulty": {"label": "medium", "score": 400},
        "min_known": 1,
        "min_total": 1,
        "rows": _slots(row_conditions),
        "cols": _slots(col_conditions),
        "cells": [[{"total": 1, "known": 1}] * 3 for _ in range(3)],
    }
    payload = json.dumps(
        {"rows": grid_data["rows"], "cols": grid_data["cols"], "cells": grid_data["cells"]},
        sort_keys=True,
    )
    content_hash = hashlib.md5(payload.encode()).hexdigest()[:24] + uuid.uuid4().hex[:8]

    grid = MtgDokuGrid(
        difficulty="medium",
        score=1.0,
        difficulty_score=400.0,
        content_hash=content_hash,
        grid_data=grid_data,
    )
    session.add(grid)
    session.commit()
    session.refresh(grid)
    return grid


# ===========================================================================
# PARTIE 1 — Filtres solo
# ===========================================================================


class TestThaliaFiltersMatch:
    """Thalia doit matcher tous ses filtres caractéristiques."""

    def test_mono_white(self, session, thalia):
        assert _count(session, THALIA_ID, "c=w") == 1

    def test_legendary(self, session, thalia):
        assert _count(session, THALIA_ID, "type=legendary") == 1

    def test_creature(self, session, thalia):
        assert _count(session, THALIA_ID, "type=creature") == 1

    def test_power_2(self, session, thalia):
        assert _count(session, THALIA_ID, "pow=2") == 1

    def test_toughness_1(self, session, thalia):
        assert _count(session, THALIA_ID, "tou=1") == 1

    def test_cmc_2(self, session, thalia):
        assert _count(session, THALIA_ID, "cmc=2") == 1

    def test_atleast_white(self, session, thalia):
        assert _count(session, THALIA_ID, "c>w") == 1


class TestThaliaFiltersNoMatch:
    """Thalia ne doit pas matcher des filtres qui ne lui correspondent pas."""

    def test_not_blue(self, session, thalia):
        assert _count(session, THALIA_ID, "c=u") == 0

    def test_not_black(self, session, thalia):
        assert _count(session, THALIA_ID, "c=b") == 0

    def test_not_red(self, session, thalia):
        assert _count(session, THALIA_ID, "c=r") == 0

    def test_not_green(self, session, thalia):
        assert _count(session, THALIA_ID, "c=g") == 0

    def test_not_atleast_green(self, session, thalia):
        assert _count(session, THALIA_ID, "c>g") == 0

    def test_not_bicolor_wb(self, session, thalia):
        assert _count(session, THALIA_ID, "c=wb") == 0

    def test_not_sorcery(self, session, thalia):
        assert _count(session, THALIA_ID, "type=sorcery") == 0

    def test_not_instant(self, session, thalia):
        assert _count(session, THALIA_ID, "type=instant") == 0

    # pow>1 : les bornes inférieures ne matchent pas
    def test_not_power_0(self, session, thalia):
        assert _count(session, THALIA_ID, "pow=0") == 0

    def test_not_power_1(self, session, thalia):
        assert _count(session, THALIA_ID, "pow=1") == 0

    # pow<3 : les bornes supérieures ne matchent pas
    def test_not_power_3(self, session, thalia):
        assert _count(session, THALIA_ID, "pow=3") == 0

    def test_not_toughness_0(self, session, thalia):
        assert _count(session, THALIA_ID, "tou=0") == 0

    def test_not_toughness_2(self, session, thalia):
        assert _count(session, THALIA_ID, "tou=2") == 0

    def test_not_cmc_3(self, session, thalia):
        assert _count(session, THALIA_ID, "cmc=3") == 0



class TestFindFinalityFiltersMatch:
    """Find // Finality doit matcher ses filtres caractéristiques."""

    def test_atleast_green(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c>g") == 1

    def test_atleast_black(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c>b") == 1

    def test_exact_bicolor_bg(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c=bg") == 1

    def test_sorcery(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "type=sorcery") == 1

    def test_oracle_graveyard(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, 'o:"graveyard"') == 1

    def test_oracle_plus1_counter(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, 'o:"+1/+1"') == 1


class TestFindFinalityFiltersNoMatch:
    """Find // Finality ne doit pas matcher des filtres inadaptés."""

    def test_not_mono_white(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c=w") == 0

    def test_not_atleast_white(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c>w") == 0

    def test_not_bicolor_wg(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "c=wg") == 0

    def test_not_creature(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "type=creature") == 0

    def test_not_legendary(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "type=legendary") == 0

    def test_not_cmc_2(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "cmc=2") == 0

    # pow<2 : Find // Finality n'a pas de power (sorcery) — aucun pow ne doit matcher
    def test_no_power_0(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "pow=0") == 0

    def test_no_power_1(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "pow=1") == 0

    def test_no_power_2(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "pow=2") == 0

    # tou<2 : même chose pour la toughness
    def test_no_toughness_0(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "tou=0") == 0

    def test_no_toughness_1(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, "tou=1") == 0

    def test_no_oracle_flying(self, session, find_finality):
        assert _count(session, FIND_FINALITY_ID, 'o:"flying"') == 0


# ===========================================================================
# PARTIE 2 — Groupes de filtres (check_card_for_cell)
# ===========================================================================


class TestCheckCardForCellThalia:
    """Thalia doit valider les cases combinant ses attributs."""

    def test_white_plus_legendary(self, session, thalia):
        grid = _make_grid(session, [["c=w"]], [["type=legendary"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_white_plus_creature(self, session, thalia):
        grid = _make_grid(session, [["c=w"]], [["type=creature"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_legendary_plus_power_2(self, session, thalia):
        grid = _make_grid(session, [["type=legendary"]], [["pow=2"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_creature_plus_toughness_1(self, session, thalia):
        grid = _make_grid(session, [["type=creature"]], [["tou=1"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_five_conditions_all_match(self, session, thalia):
        """Case avec 5 conditions combinées : c=w + type=legendary (row) + type=creature + pow=2 + tou=1 (col)."""
        grid = _make_grid(
            session,
            [["c=w", "type=legendary"]],
            [["type=creature", "pow=2", "tou=1"]],
        )
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_cmc_2_plus_creature(self, session, thalia):
        grid = _make_grid(session, [["cmc=2"]], [["type=creature"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_wrong_card_fails_white_condition(self, session, thalia, find_finality):
        """Find // Finality ne passe pas une case mono-blanc."""
        grid = _make_grid(session, [["c=w"]], [["type=legendary"]])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is False

    def test_thalia_fails_sorcery_condition(self, session, thalia):
        grid = _make_grid(session, [["c=w"]], [["type=sorcery"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False

    def test_thalia_fails_wrong_power(self, session, thalia):
        grid = _make_grid(session, [["c=w"]], [["pow=3"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False

    def test_cell_uses_correct_row_and_col(self, session, thalia):
        """Vérifie que cell (1, 2) lit bien row[1] et col[2] et non row[0]/col[0]."""
        # row[0]=sorcery (ne convient pas), row[1]=creature (convient)
        # col[0]=sorcery (ne convient pas), col[2]=legendary (convient)
        grid = _make_grid(
            session,
            [["type=sorcery"], ["type=creature"]],
            [["type=sorcery"], [], ["type=legendary"]],
        )
        assert check_card_for_cell(session, grid, 1, 2, THALIA_ID) is True
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False


class TestCheckCardForCellFindFinality:
    """Find // Finality doit valider les cases combinant ses attributs."""

    def test_atleast_green_plus_sorcery(self, session, find_finality):
        grid = _make_grid(session, [["c>g"]], [["type=sorcery"]])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is True

    def test_oracle_graveyard_plus_oracle_plus1(self, session, find_finality):
        grid = _make_grid(session, [['o:"graveyard"']], [['o:"+1/+1"']])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is True

    def test_four_conditions_all_match(self, session, find_finality):
        """c>g + o:graveyard (row) · o:+1/+1 + type=sorcery (col)."""
        grid = _make_grid(
            session,
            [["c>g", 'o:"graveyard"']],
            [['o:"+1/+1"', "type=sorcery"]],
        )
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is True

    def test_exact_bg_plus_sorcery(self, session, find_finality):
        grid = _make_grid(session, [["c=bg"]], [["type=sorcery"]])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is True

    def test_wrong_card_fails_green_condition(self, session, thalia, find_finality):
        """Thalia ne passe pas une case qui exige la couleur verte."""
        grid = _make_grid(session, [["c>g"]], [["type=sorcery"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False

    def test_find_finality_fails_creature_condition(self, session, find_finality):
        grid = _make_grid(session, [["c>g"]], [["type=creature"]])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is False

    def test_find_finality_fails_mono_white(self, session, find_finality):
        grid = _make_grid(session, [["c=w"]], [["type=sorcery"]])
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is False


class TestCheckCardForCellEdgeCases:
    """Cas limites et comportements de robustesse."""

    def test_unknown_condition_id_returns_false(self, session, thalia):
        """Une condition inconnue doit retourner False (carte inconnue du registre)."""
        grid = _make_grid(session, [["c=w"]], [["UNKNOWN_CONDITION_XYZ"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False

    def test_empty_conditions_matches_any_card(self, session, thalia):
        """Aucune condition → toute carte est valide."""
        grid = _make_grid(session, [[]], [[]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is True

    def test_unknown_oracle_id_returns_false(self, session, thalia):
        grid = _make_grid(session, [["c=w"]], [["type=creature"]])
        assert check_card_for_cell(session, grid, 0, 0, "00000000-0000-0000-0000-000000000000") is False

    def test_contradictory_conditions_return_false(self, session, thalia, find_finality):
        """c=w ET c>g sont incompatibles : aucune carte ne peut valider."""
        grid = _make_grid(session, [["c=w"]], [["c>g"]])
        assert check_card_for_cell(session, grid, 0, 0, THALIA_ID) is False
        assert check_card_for_cell(session, grid, 0, 0, FIND_FINALITY_ID) is False
