from itertools import combinations

from sqlalchemy import Integer, and_, cast, func

from app.models.mtg.mtg_card import MtgCard

# Regexp PostgreSQL pour ne cibler que les puissances/endurances numériques (exclut "*", "X", etc.)
_NUMERIC_RE = r"^\d+$"

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

_COLOR_MAP = {"w": "W", "u": "U", "b": "B", "r": "R", "g": "G"}
_COLOR_LABEL = {"w": "White", "u": "Blue", "b": "Black", "r": "Red", "g": "Green", "c": "Colorless"}


# ---------------------------------------------------------------------------
# Category class
# ---------------------------------------------------------------------------


class DokuCategory:
    def __init__(self, id: str, label: str, group: str, filter_fn):
        self.id = id
        self.label = label
        self.group = group
        self._filter_fn = filter_fn

    def filter_expr(self):
        return self._filter_fn()

    def __repr__(self) -> str:
        return f"DokuCategory(id={self.id!r}, label={self.label!r})"


# ---------------------------------------------------------------------------
# Filter builders
# ---------------------------------------------------------------------------


def _colors_length(n: int):
    """PostgreSQL array_length is NULL for empty arrays, coalesce to 0."""
    return func.coalesce(func.array_length(MtgCard.colors, 1), 0) == n


def _exact_mono(color: str):
    if color == "c":
        return _colors_length(0)
    col = _COLOR_MAP[color]
    return and_(_colors_length(1), MtgCard.colors.contains([col]))


def _exact_bi(c1: str, c2: str):
    col1, col2 = _COLOR_MAP[c1], _COLOR_MAP[c2]
    return and_(_colors_length(2), MtgCard.colors.contains([col1, col2]))


def _at_least(color: str):
    col = _COLOR_MAP[color]
    return MtgCard.color_identity.contains([col])


def _cmc(n: int):
    return MtgCard.converted_mana_cost == n


def _type_contains(type_name: str):
    return MtgCard.type_line.ilike(f"%{type_name}%")


def _power_eq(n: int):
    return MtgCard.power == str(n)


def _power_lt(n: int):
    return and_(MtgCard.power.op("~")(_NUMERIC_RE), cast(MtgCard.power, Integer) < n)


def _power_gt(n: int):
    return and_(MtgCard.power.op("~")(_NUMERIC_RE), cast(MtgCard.power, Integer) > n)


def _toughness_eq(n: int):
    return MtgCard.toughness == str(n)


def _toughness_lt(n: int):
    return and_(MtgCard.toughness.op("~")(_NUMERIC_RE), cast(MtgCard.toughness, Integer) < n)


def _toughness_gt(n: int):
    return and_(MtgCard.toughness.op("~")(_NUMERIC_RE), cast(MtgCard.toughness, Integer) > n)


def _cmc_lt(n: int):
    return MtgCard.converted_mana_cost < n


def _cmc_gt(n: int):
    return MtgCard.converted_mana_cost > n


def _oracle_contains(text: str):
    return MtgCard.oracle_text.ilike(f"%{text}%")


# ---------------------------------------------------------------------------
# Build all categories
# ---------------------------------------------------------------------------


def _build_all_categories() -> list[DokuCategory]:
    cats: list[DokuCategory] = []

    monocolor = ["w", "u", "b", "r", "g", "c"]
    bicolor = list(combinations(["w", "u", "b", "r", "g"], 2))

    # Exact monocolor (c=w, c=u, ..., c=c)
    for c in monocolor:
        c_fixed = c
        cats.append(DokuCategory(
            id=f"c={c_fixed}",
            label=f"{_COLOR_LABEL[c_fixed]} only",
            group="color_exact",
            filter_fn=lambda c=c_fixed: _exact_mono(c),
        ))

    # Exact bicolor (c=wu, c=wb, ...)
    for c1, c2 in bicolor:
        c1_fixed, c2_fixed = c1, c2
        label = f"{_COLOR_LABEL[c1_fixed]}/{_COLOR_LABEL[c2_fixed]}"
        cats.append(DokuCategory(
            id=f"c={c1_fixed}{c2_fixed}",
            label=label,
            group="color_bicolor",
            filter_fn=lambda c1=c1_fixed, c2=c2_fixed: _exact_bi(c1, c2),
        ))

    # At least color (c>w, c>u, ...) — no colorless
    for c in ["w", "u", "b", "r", "g"]:
        c_fixed = c
        cats.append(DokuCategory(
            id=f"c>{c_fixed}",
            label=f"Uses {_COLOR_LABEL[c_fixed]}",
            group="color_atleast",
            filter_fn=lambda c=c_fixed: _at_least(c),
        ))

    # CMC exact (cmc=1 to cmc=5)
    for i in range(1, 6):
        i_fixed = i
        cats.append(DokuCategory(
            id=f"cmc={i_fixed}",
            label=f"CMC {i_fixed}",
            group="cmc",
            filter_fn=lambda i=i_fixed: _cmc(i),
        ))

    # CMC < n  (cmc<2 … cmc<6)
    for n in range(2, 7):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"cmc<{n_fixed}",
            label=f"CMC < {n_fixed}",
            group="cmc",
            filter_fn=lambda n=n_fixed: _cmc_lt(n),
        ))

    # CMC > n  (cmc>0 … cmc>4)
    for n in range(0, 5):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"cmc>{n_fixed}",
            label=f"CMC > {n_fixed}",
            group="cmc",
            filter_fn=lambda n=n_fixed: _cmc_gt(n),
        ))

    # Card types — permanent
    for t in ["Creature", "Enchantment", "Artifact", "Land"]:
        t_fixed = t
        cats.append(DokuCategory(
            id=f"type={t_fixed.lower()}",
            label=t_fixed,
            group="type",
            filter_fn=lambda t=t_fixed: _type_contains(t),
        ))

    # Card types — non-permanent / supertype
    for t in ["Instant", "Sorcery", "Legendary"]:
        t_fixed = t
        cats.append(DokuCategory(
            id=f"type={t_fixed.lower()}",
            label=t_fixed,
            group="type",
            filter_fn=lambda t=t_fixed: _type_contains(t),
        ))

    # Power exact (pow=0 to pow=5)
    for i in range(6):
        i_fixed = i
        cats.append(DokuCategory(
            id=f"pow={i_fixed}",
            label=f"Power {i_fixed}",
            group="power",
            filter_fn=lambda i=i_fixed: _power_eq(i),
        ))

    # Power < n  (pow<2 … pow<5)
    for n in range(2, 6):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"pow<{n_fixed}",
            label=f"Power < {n_fixed}",
            group="power",
            filter_fn=lambda n=n_fixed: _power_lt(n),
        ))

    # Power > n  (pow>0 … pow>4)
    for n in range(0, 5):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"pow>{n_fixed}",
            label=f"Power > {n_fixed}",
            group="power",
            filter_fn=lambda n=n_fixed: _power_gt(n),
        ))

    # Toughness exact (tou=0 to tou=5)
    for i in range(6):
        i_fixed = i
        cats.append(DokuCategory(
            id=f"tou={i_fixed}",
            label=f"Toughness {i_fixed}",
            group="toughness",
            filter_fn=lambda i=i_fixed: _toughness_eq(i),
        ))

    # Toughness < n  (tou<2 … tou<5)
    for n in range(2, 6):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"tou<{n_fixed}",
            label=f"Toughness < {n_fixed}",
            group="toughness",
            filter_fn=lambda n=n_fixed: _toughness_lt(n),
        ))

    # Toughness > n  (tou>0 … tou>4)
    for n in range(0, 5):
        n_fixed = n
        cats.append(DokuCategory(
            id=f"tou>{n_fixed}",
            label=f"Toughness > {n_fixed}",
            group="toughness",
            filter_fn=lambda n=n_fixed: _toughness_gt(n),
        ))

    # Keywords (oracle text)
    keywords = ["flying", "reach", "indestructible", "trample", "haste", "deathtouch", "lifelink"]
    for k in keywords:
        k_fixed = k
        cats.append(DokuCategory(
            id=f'o:"{k_fixed}"',
            label=k_fixed.capitalize(),
            group="keyword",
            filter_fn=lambda k=k_fixed: _oracle_contains(k),
        ))

    # Mentions (oracle text)
    mentions = ["exile", "graveyard", "discard", "hand", "library", "scry", "+1/+1", "-1/-1", "token", "sacrifice"]
    mention_labels = {
        "+1/+1": "+1/+1 counter",
        "-1/-1": "-1/-1 counter",
    }
    for m in mentions:
        m_fixed = m
        label = mention_labels.get(m_fixed, m_fixed).capitalize()
        cats.append(DokuCategory(
            id=f'o:"{m_fixed}"',
            label=label,
            group="mention",
            filter_fn=lambda m=m_fixed: _oracle_contains(m),
        ))

    return cats


ALL_CATEGORIES: list[DokuCategory] = _build_all_categories()
CATEGORIES_BY_ID: dict[str, DokuCategory] = {cat.id: cat for cat in ALL_CATEGORIES}
