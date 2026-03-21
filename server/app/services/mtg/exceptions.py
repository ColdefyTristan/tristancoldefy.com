class DeckServiceError(Exception):
    """Base class for deck service errors."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class DeckNotFound(DeckServiceError):
    def __init__(self):
        super().__init__("not_found", "Deck not found.")


class DeckAccessForbidden(DeckServiceError):
    def __init__(self):
        super().__init__("forbidden_deck_access", "Access to this deck is forbidden.")


class EntityNotFound(DeckServiceError):
    def __init__(self, ref_type: str):
        super().__init__(f"unknown_{ref_type}_ref", f"Referenced {ref_type} not found.")


class ImmutableTagDef(DeckServiceError):
    def __init__(self):
        super().__init__("immutable_tag_def", "Global tag definitions cannot be modified.")


class TagDefHasDependencies(DeckServiceError):
    def __init__(self):
        super().__init__(
            "tag_def_has_dependencies",
            "Cannot remove a tag definition that has value options or card tags.",
        )


class TagValueDefHasDependencies(DeckServiceError):
    def __init__(self):
        super().__init__(
            "tag_value_def_has_dependencies",
            "Cannot remove a tag value definition that is assigned to cards.",
        )


class DuplicateTagValue(DeckServiceError):
    def __init__(self):
        super().__init__("duplicate_tag_value", "A tag value with this name already exists.")
