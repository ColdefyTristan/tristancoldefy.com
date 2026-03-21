from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

from app.models.mtg.enums import DeckEntryZone


class EntityRef(BaseModel):
    server_id: int | None = None
    local_id: str | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> "EntityRef":
        if self.server_id is None and self.local_id is None:
            raise ValueError("EntityRef must have at least one of server_id or local_id")
        return self


# --- Base ---


class _BaseOperation(BaseModel):
    operation_id: str


# --- Deck ---


class RenameDeckOperation(_BaseOperation):
    type: Literal["rename_deck"]
    name: str = Field(min_length=1, max_length=120)


# --- Cards ---


class AddCardOperation(_BaseOperation):
    type: Literal["add_card"]
    card_local_id: str
    oracle_card_id: str
    zone: DeckEntryZone
    quantity: int = Field(ge=1)


class RemoveCardOperation(_BaseOperation):
    type: Literal["remove_card"]
    card_ref: EntityRef


class MoveCardToZoneOperation(_BaseOperation):
    type: Literal["move_card_to_zone"]
    card_ref: EntityRef
    zone: DeckEntryZone


class SetCardQuantityOperation(_BaseOperation):
    type: Literal["set_card_quantity"]
    card_ref: EntityRef
    quantity: int = Field(ge=1)


# --- Tag definitions ---


class CreateTagDefOperation(_BaseOperation):
    type: Literal["create_tag_def"]
    tag_def_local_id: str
    name: str = Field(min_length=1, max_length=120)


class RemoveTagDefOperation(_BaseOperation):
    type: Literal["remove_tag_def"]
    tag_def_ref: EntityRef


class RenameTagDefOperation(_BaseOperation):
    type: Literal["rename_tag_def"]
    tag_def_ref: EntityRef
    name: str = Field(min_length=1, max_length=120)


# --- Tag value definitions ---


class AddTagValueDefOperation(_BaseOperation):
    type: Literal["add_tag_value_def"]
    tag_def_ref: EntityRef
    tag_value_def_local_id: str
    value: str = Field(min_length=1, max_length=120)
    weight: int = Field(ge=0, le=10)


class RemoveTagValueDefOperation(_BaseOperation):
    type: Literal["remove_tag_value_def"]
    tag_value_def_ref: EntityRef


class RenameTagValueDefOperation(_BaseOperation):
    type: Literal["rename_tag_value_def"]
    tag_value_def_ref: EntityRef
    value: str = Field(min_length=1, max_length=120)


class SetTagValueDefWeightOperation(_BaseOperation):
    type: Literal["set_tag_value_def_weight"]
    tag_value_def_ref: EntityRef
    weight: int = Field(ge=0, le=10)


# --- Card tags ---


class AddCardTagOperation(_BaseOperation):
    type: Literal["add_card_tag"]
    card_ref: EntityRef
    card_tag_local_id: str
    tag_def_ref: EntityRef
    tag_value_def_ref: EntityRef
    weight: int = Field(ge=0, le=10)


class RemoveCardTagOperation(_BaseOperation):
    type: Literal["remove_card_tag"]
    card_tag_ref: EntityRef


class SetCardTagValueOperation(_BaseOperation):
    type: Literal["set_card_tag_value"]
    card_tag_ref: EntityRef
    tag_value_def_ref: EntityRef


class SetCardTagWeightOperation(_BaseOperation):
    type: Literal["set_card_tag_weight"]
    card_tag_ref: EntityRef
    weight: int = Field(ge=0, le=10)


# --- Discriminated union ---

DeckOperation = Annotated[
    Union[
        RenameDeckOperation,
        AddCardOperation,
        RemoveCardOperation,
        MoveCardToZoneOperation,
        SetCardQuantityOperation,
        CreateTagDefOperation,
        RemoveTagDefOperation,
        RenameTagDefOperation,
        AddTagValueDefOperation,
        RemoveTagValueDefOperation,
        RenameTagValueDefOperation,
        SetTagValueDefWeightOperation,
        AddCardTagOperation,
        RemoveCardTagOperation,
        SetCardTagValueOperation,
        SetCardTagWeightOperation,
    ],
    Field(discriminator="type"),
]


# --- Request ---


class ApplyDeckOperationsRequest(BaseModel):
    batch_id: str = Field(min_length=1, max_length=255)
    base_version: int = Field(ge=0)
    operations: list[DeckOperation] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def no_duplicate_operation_ids(self) -> "ApplyDeckOperationsRequest":
        ids = [op.operation_id for op in self.operations]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate operation_id values in batch")
        return self


# --- Response ---


class LocalToServerMapping(BaseModel):
    local_id: str
    server_id: int


class LocalToServerMappings(BaseModel):
    cards: list[LocalToServerMapping] = []
    tag_defs: list[LocalToServerMapping] = []
    tag_value_defs: list[LocalToServerMapping] = []
    card_tags: list[LocalToServerMapping] = []


class ApplyDeckOperationsResponse(BaseModel):
    applied_batch_id: str
    new_version: int
    applied_operation_ids: list[str]
    local_to_server_mappings: LocalToServerMappings
