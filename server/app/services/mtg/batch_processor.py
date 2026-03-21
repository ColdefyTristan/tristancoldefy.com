from dataclasses import dataclass, field

from sqlmodel import Session, select

from app.models.mtg.mtg_deck import Deck, DeckEntry, DeckBatchResult
from app.models.mtg.mtg_tag import TagDefinition, TagValueOption, DeckEntryTag
from app.models.mtg.batch_schemas import (
    ApplyDeckOperationsRequest,
    ApplyDeckOperationsResponse,
    DeckOperation,
    EntityRef,
    LocalToServerMapping,
    LocalToServerMappings,
    AddCardOperation,
    RemoveCardOperation,
    MoveCardToZoneOperation,
    SetCardQuantityOperation,
    RenameDeckOperation,
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
)
from app.services.mtg import deck as deck_svc
from app.services.mtg import deck_entry as entry_svc
from app.services.mtg import tag_def as tag_svc
from app.services.mtg import card_tag as card_tag_svc
from app.services.mtg.exceptions import DeckServiceError, DeckNotFound, DeckAccessForbidden
from app.utils.time import utcnow_naive


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BatchConflictVersionError(Exception):
    pass


class BatchOperationError(Exception):
    def __init__(self, operation_id: str, code: str, message: str):
        self.operation_id = operation_id
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Internal context (local_id → server_id maps)
# ---------------------------------------------------------------------------


@dataclass
class _BatchContext:
    deck: Deck
    card_map: dict[str, int] = field(default_factory=dict)
    tag_def_map: dict[str, int] = field(default_factory=dict)
    tag_value_map: dict[str, int] = field(default_factory=dict)
    card_tag_map: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Entity resolution helpers
# ---------------------------------------------------------------------------


def _resolve_server_id(ref: EntityRef, local_map: dict[str, int], label: str) -> int:
    if ref.server_id is not None:
        return ref.server_id
    resolved = local_map.get(ref.local_id)  # type: ignore[arg-type]
    if resolved is None:
        raise DeckServiceError("unresolved_local_id", f"local_id '{ref.local_id}' not resolved for {label}")
    return resolved


def _resolve_deck_entry(session: Session, deck: Deck, ref: EntityRef, ctx: _BatchContext) -> DeckEntry:
    server_id = _resolve_server_id(ref, ctx.card_map, "card_ref")
    entry = session.get(DeckEntry, server_id)
    if entry is None or entry.deck_id != deck.id:
        raise DeckServiceError("unknown_card_ref", "Card entry not found in this deck")
    return entry


def _resolve_tag_def(session: Session, deck: Deck, ref: EntityRef, ctx: _BatchContext) -> TagDefinition:
    server_id = _resolve_server_id(ref, ctx.tag_def_map, "tag_def_ref")
    tag_def = session.get(TagDefinition, server_id)
    if tag_def is None or (tag_def.deck_id is not None and tag_def.deck_id != deck.id):
        raise DeckServiceError("unknown_tag_def_ref", "Tag definition not found for this deck")
    return tag_def


def _resolve_tag_value(session: Session, ref: EntityRef, ctx: _BatchContext) -> TagValueOption:
    server_id = _resolve_server_id(ref, ctx.tag_value_map, "tag_value_def_ref")
    option = session.get(TagValueOption, server_id)
    if option is None:
        raise DeckServiceError("unknown_tag_value_def_ref", "Tag value definition not found")
    return option


def _resolve_card_tag(session: Session, deck: Deck, ref: EntityRef, ctx: _BatchContext) -> DeckEntryTag:
    server_id = _resolve_server_id(ref, ctx.card_tag_map, "card_tag_ref")
    card_tag = session.get(DeckEntryTag, server_id)
    if card_tag is None:
        raise DeckServiceError("unknown_card_tag_ref", "Card tag not found")
    # Verify ownership via the parent deck entry
    entry = session.get(DeckEntry, card_tag.deck_entry_id)
    if entry is None or entry.deck_id != deck.id:
        raise DeckServiceError("unknown_card_tag_ref", "Card tag does not belong to this deck")
    return card_tag


# ---------------------------------------------------------------------------
# Operation dispatch
# ---------------------------------------------------------------------------


def _process_op(session: Session, op: DeckOperation, ctx: _BatchContext) -> None:
    deck = ctx.deck

    if isinstance(op, RenameDeckOperation):
        deck_svc.rename_deck(session, deck, op.name)

    elif isinstance(op, AddCardOperation):
        entry = entry_svc.add_card(session, deck, op.oracle_card_id, op.zone, op.quantity)
        ctx.card_map[op.card_local_id] = entry.id  # type: ignore[assignment]

    elif isinstance(op, RemoveCardOperation):
        entry = _resolve_deck_entry(session, deck, op.card_ref, ctx)
        entry_svc.remove_card(session, entry)

    elif isinstance(op, MoveCardToZoneOperation):
        entry = _resolve_deck_entry(session, deck, op.card_ref, ctx)
        entry_svc.move_card_to_zone(session, entry, op.zone)

    elif isinstance(op, SetCardQuantityOperation):
        entry = _resolve_deck_entry(session, deck, op.card_ref, ctx)
        entry_svc.set_card_quantity(session, entry, op.quantity)

    elif isinstance(op, CreateTagDefOperation):
        tag_def = tag_svc.create_tag_def(session, deck, op.name)
        ctx.tag_def_map[op.tag_def_local_id] = tag_def.id  # type: ignore[assignment]

    elif isinstance(op, RemoveTagDefOperation):
        tag_def = _resolve_tag_def(session, deck, op.tag_def_ref, ctx)
        tag_svc.remove_tag_def(session, tag_def)

    elif isinstance(op, RenameTagDefOperation):
        tag_def = _resolve_tag_def(session, deck, op.tag_def_ref, ctx)
        tag_svc.rename_tag_def(session, tag_def, op.name)

    elif isinstance(op, AddTagValueDefOperation):
        tag_def = _resolve_tag_def(session, deck, op.tag_def_ref, ctx)
        option = tag_svc.add_tag_value_def(session, tag_def, op.value, op.weight)
        ctx.tag_value_map[op.tag_value_def_local_id] = option.id  # type: ignore[assignment]

    elif isinstance(op, RemoveTagValueDefOperation):
        option = _resolve_tag_value(session, op.tag_value_def_ref, ctx)
        tag_svc.remove_tag_value_def(session, option)

    elif isinstance(op, RenameTagValueDefOperation):
        option = _resolve_tag_value(session, op.tag_value_def_ref, ctx)
        tag_svc.rename_tag_value_def(session, option, op.value)

    elif isinstance(op, SetTagValueDefWeightOperation):
        option = _resolve_tag_value(session, op.tag_value_def_ref, ctx)
        tag_svc.set_tag_value_def_weight(session, option, op.weight)

    elif isinstance(op, AddCardTagOperation):
        entry = _resolve_deck_entry(session, deck, op.card_ref, ctx)
        tag_def = _resolve_tag_def(session, deck, op.tag_def_ref, ctx)
        option = _resolve_tag_value(session, op.tag_value_def_ref, ctx)
        card_tag = card_tag_svc.add_card_tag(session, entry, tag_def, option, op.weight)
        ctx.card_tag_map[op.card_tag_local_id] = card_tag.id  # type: ignore[assignment]

    elif isinstance(op, RemoveCardTagOperation):
        card_tag = _resolve_card_tag(session, deck, op.card_tag_ref, ctx)
        card_tag_svc.remove_card_tag(session, card_tag)

    elif isinstance(op, SetCardTagValueOperation):
        card_tag = _resolve_card_tag(session, deck, op.card_tag_ref, ctx)
        option = _resolve_tag_value(session, op.tag_value_def_ref, ctx)
        card_tag_svc.set_card_tag_value(session, card_tag, option)

    elif isinstance(op, SetCardTagWeightOperation):
        card_tag = _resolve_card_tag(session, deck, op.card_tag_ref, ctx)
        card_tag_svc.set_card_tag_weight(session, card_tag, op.weight)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def apply_batch(
    session: Session,
    deck_id: int,
    user_id: int,
    request: ApplyDeckOperationsRequest,
) -> ApplyDeckOperationsResponse:
    # 1. Idempotency: return stored result if batch already applied
    existing = session.exec(
        select(DeckBatchResult).where(
            DeckBatchResult.deck_id == deck_id,
            DeckBatchResult.user_id == user_id,
            DeckBatchResult.batch_id == request.batch_id,
        )
    ).first()
    if existing is not None:
        return ApplyDeckOperationsResponse.model_validate(existing.result_json)

    # 2. Fetch deck with exclusive lock (prevents concurrent batch races)
    deck = session.exec(
        select(Deck).where(Deck.id == deck_id).with_for_update()
    ).first()
    if deck is None:
        raise DeckNotFound()
    if deck.user_id != user_id:
        raise DeckAccessForbidden()

    # 3. Version conflict check
    if deck.version != request.base_version:
        raise BatchConflictVersionError()

    # 4. Process operations in order
    ctx = _BatchContext(deck=deck)
    applied_ids: list[str] = []

    for op in request.operations:
        try:
            _process_op(session, op, ctx)
            applied_ids.append(op.operation_id)
        except DeckServiceError as exc:
            raise BatchOperationError(op.operation_id, exc.code, exc.message)

    # 5. Increment deck version
    deck.version += 1
    session.add(deck)
    session.flush()

    # 6. Build response
    response = ApplyDeckOperationsResponse(
        applied_batch_id=request.batch_id,
        new_version=deck.version,
        applied_operation_ids=applied_ids,
        local_to_server_mappings=LocalToServerMappings(
            cards=[LocalToServerMapping(local_id=k, server_id=v) for k, v in ctx.card_map.items()],
            tag_defs=[LocalToServerMapping(local_id=k, server_id=v) for k, v in ctx.tag_def_map.items()],
            tag_value_defs=[LocalToServerMapping(local_id=k, server_id=v) for k, v in ctx.tag_value_map.items()],
            card_tags=[LocalToServerMapping(local_id=k, server_id=v) for k, v in ctx.card_tag_map.items()],
        ),
    )

    # 7. Persist result for idempotent replay
    session.add(DeckBatchResult(
        deck_id=deck_id,
        user_id=user_id,
        batch_id=request.batch_id,
        result_json=response.model_dump(),
        applied_at=utcnow_naive(),
    ))

    return response
