"""Unit tests for the DokuCategory definitions (no DB required)."""
from itertools import combinations

from app.services.mtg.doku_categories import ALL_CATEGORIES, CATEGORIES_BY_ID


def _cats_by_group(group: str):
    return [c for c in ALL_CATEGORIES if c.group == group]


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_all_ids_are_unique():
    ids = [cat.id for cat in ALL_CATEGORIES]
    assert len(ids) == len(set(ids)), "Duplicate category IDs found"


def test_all_categories_have_label_and_group():
    for cat in ALL_CATEGORIES:
        assert cat.id, f"Category has no id: {cat}"
        assert cat.label, f"Category has no label: {cat.id}"
        assert cat.group, f"Category has no group: {cat.id}"


def test_categories_by_id_matches_all_categories():
    assert set(CATEGORIES_BY_ID.keys()) == {cat.id for cat in ALL_CATEGORIES}


# ---------------------------------------------------------------------------
# Color exact (monocolor)
# ---------------------------------------------------------------------------


def test_exact_monocolor_count():
    assert len(_cats_by_group("color_exact")) == 6  # w u b r g c


def test_exact_monocolor_ids_present():
    for color in ["w", "u", "b", "r", "g", "c"]:
        assert f"c={color}" in CATEGORIES_BY_ID


def test_colorless_category_label():
    assert CATEGORIES_BY_ID["c=c"].label == "Colorless only"


# ---------------------------------------------------------------------------
# Color exact (bicolor)
# ---------------------------------------------------------------------------


def test_exact_bicolor_count():
    expected = len(list(combinations(["w", "u", "b", "r", "g"], 2)))
    assert len(_cats_by_group("color_bicolor")) == expected  # 10


def test_exact_bicolor_wu_present():
    assert "c=wu" in CATEGORIES_BY_ID


def test_exact_bicolor_rg_present():
    assert "c=rg" in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# Color at-least
# ---------------------------------------------------------------------------


def test_atleast_count():
    assert len(_cats_by_group("color_atleast")) == 5  # no colorless


def test_atleast_ids_present():
    for color in ["w", "u", "b", "r", "g"]:
        assert f"c>{color}" in CATEGORIES_BY_ID


def test_atleast_no_colorless():
    assert "c>c" not in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# CMC
# ---------------------------------------------------------------------------


def test_cmc_count():
    assert len(_cats_by_group("cmc")) == 5


def test_cmc_ids_present():
    for i in range(1, 6):
        assert f"cmc={i}" in CATEGORIES_BY_ID


def test_cmc_zero_not_present():
    assert "cmc=0" not in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# Card types
# ---------------------------------------------------------------------------


def test_type_count():
    assert len(_cats_by_group("type")) == 7


def test_permanent_types_present():
    for t in ["creature", "enchantment", "artifact", "land"]:
        assert f"type={t}" in CATEGORIES_BY_ID


def test_non_permanent_types_present():
    for t in ["instant", "sorcery", "legendary"]:
        assert f"type={t}" in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# Power / Toughness
# ---------------------------------------------------------------------------


def test_power_count():
    assert len(_cats_by_group("power")) == 6  # 0 to 5


def test_toughness_count():
    assert len(_cats_by_group("toughness")) == 6


def test_power_ids_present():
    for i in range(6):
        assert f"pow={i}" in CATEGORIES_BY_ID


def test_toughness_ids_present():
    for i in range(6):
        assert f"tou={i}" in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------


def test_keyword_count():
    assert len(_cats_by_group("keyword")) == 7


def test_keywords_present():
    for k in ["flying", "reach", "indestructible", "trample", "haste", "deathtouch", "lifelink"]:
        assert f'o:"{k}"' in CATEGORIES_BY_ID


# ---------------------------------------------------------------------------
# Mentions
# ---------------------------------------------------------------------------


def test_mention_count():
    assert len(_cats_by_group("mention")) == 10


def test_mentions_present():
    for m in ["exile", "graveyard", "discard", "hand", "library", "scry",
              "+1/+1", "-1/-1", "token", "sacrifice"]:
        assert f'o:"{m}"' in CATEGORIES_BY_ID
