from enum import Enum


class DeckEntryZone(str, Enum):
    MAINBOARD = "mainboard"
    SIDEBOARD = "sideboard"
    COMMANDER = "commander"
    MAYBEBOARD = "maybeboard"


class TagKind(str, Enum):
    STRATEGY = "strategy"
    CARD_TYPE = "card_type"
    MANA_VALUE = "mana_value"
    USER_ONLY = "user_only"
    COLOR_IDENTITY = "color_identity"


class TagValueKind(str, Enum):
    NONE = "none"
    OPTION = "option"
    INTEGER = "integer"


class TagSourceKind(str, Enum):
    DERIVED = "derived"
    USER = "user"
