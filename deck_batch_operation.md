
# Deck Operations Batch Specification

## Overview

This document specifies the **Deck Operations Batch** API used to apply multiple deck edits in a single request.

The main goals are:

- reduce network chatter between client and server,
- apply deck edits atomically inside a single transaction,
- support offline-like local editing on the client,
- support temporary client-only entities through `local_id`,
- avoid double application through `batch_id`,
- detect edit conflicts through `base_version`.

This specification is designed for a deck editor where the client accumulates user actions locally, then sends them as a single batch to the server.

---

## Endpoint

`POST /decks/{deck_id}/apply-operations`

---

## Design Principles

### Atomic application

A batch is applied inside a single database transaction.

Either:

- all operations succeed, or
- the whole batch fails.

No partial application is allowed.

### Idempotency

Each batch must include a `batch_id`.

If the same batch is submitted multiple times for the same deck and user, the server must not apply it more than once.

### Conflict detection

Each batch must include a `base_version`.

The server compares `base_version` with the current deck version in storage.

If they do not match, the batch must be rejected as a conflict.

### Local-first client flow

The client may create and edit entities locally before they exist on the server.

Such entities are referenced using `local_id`.

The server resolves these `local_id` values during batch processing and returns a `local_to_server_mappings` table so the client can replace temporary references with persistent ones.

---

## Terminology

### Deck version

A monotonically increasing integer representing the current persisted version of the deck.

### `base_version`

The deck version the client believes it is editing.

### `new_version`

The deck version returned by the server after a successful batch application.

### `local_id`

A client-generated temporary identifier used before an entity has a server-side persistent identifier.

Example values:

- `local_card_1`
- `local_tag_def_3`
- `local_tag_value_def_2`
- `local_card_tag_5`

### `server_id`

A persistent integer identifier assigned by the server and stored in the database.

### `EntityRef`

A reference object used to identify an entity in an operation.

An `EntityRef` may contain:

- `server_id`
- `local_id`
- or both

However, because `local_id` is **not persisted in the database**, the server can only resolve a `local_id` if it was introduced earlier in the same batch or if the request context explicitly provides a mapping during processing.

In practice:

- after a successful sync, the client should primarily use `server_id` in future batches,
- `local_id` is mainly useful for newly created entities and intra-batch references.

---

## JSON Conventions

### Naming

All operation types use `snake_case`.

### IDs

- `server_id` is an integer
- `local_id` is a free-form string, with a recommended naming convention such as `local_card_1`

### Weights

All weights are integers from `0` to `10`, inclusive.

---

## Request Envelope

## Type: `ApplyDeckOperationsRequest`

```json
{
  "batch_id": "batch_001",
  "base_version": 12,
  "operations": []
}
````

### Fields

#### `batch_id`

* Type: string
* Required: yes

A client-generated unique identifier for the batch.

Used for idempotency.

#### `base_version`

* Type: integer
* Required: yes

The version of the deck the client expects to be editing.

#### `operations`

* Type: array of operation objects
* Required: yes

Ordered list of deck operations.

---

## Response Envelope

## Type: `ApplyDeckOperationsResponse`

```json
{
  "applied_batch_id": "batch_001",
  "new_version": 13,
  "applied_operation_ids": ["op_001", "op_002"],
  "local_to_server_mappings": {
    "cards": [
      { "local_id": "local_card_1", "server_id": 101 }
    ],
    "tag_defs": [
      { "local_id": "local_tag_def_1", "server_id": 12 }
    ],
    "tag_value_defs": [
      { "local_id": "local_tag_value_def_1", "server_id": 55 }
    ],
    "card_tags": [
      { "local_id": "local_card_tag_1", "server_id": 88 }
    ]
  }
}
```

### Fields

#### `applied_batch_id`

* Type: string
* Required: yes

The `batch_id` that was applied.

#### `new_version`

* Type: integer
* Required: yes

The deck version after successful application.

#### `applied_operation_ids`

* Type: array of strings
* Required: yes

List of successfully applied operation identifiers.

#### `local_to_server_mappings`

* Type: object
* Required: yes

Maps temporary client-side IDs to persistent server-side IDs for entities created during batch processing.

---

## Shared Types

## Type: `EntityRef`

```json
{
  "local_id": "local_card_1",
  "server_id": 101
}
```

### Rules

At least one of the following must be present:

* `local_id`
* `server_id`

### Resolution rules

1. If `server_id` is provided, it is the primary persistent reference.
2. If `local_id` is provided and refers to an entity created earlier in the same batch, the server resolves it using the in-memory batch mapping.
3. If both are provided and the `local_id` has already been resolved in the same batch, both references must point to the same entity.
4. If both are provided but the `local_id` is not resolvable in the current batch context, the server may treat `server_id` as authoritative.
5. The server must never persist `local_id` in the database.

### Recommendation

After a successful batch response, the client should update local state with the returned `server_id` values and prefer `server_id` in future batches.

---

## Zones

Allowed values for card zones:

* `mainboard`
* `sideboard`
* `maybeboard`

---

## Operation Structure

Every operation object must contain:

* `type`
* `operation_id`

Example:

```json
{
  "type": "set_card_quantity",
  "operation_id": "op_004"
}
```

### `operation_id`

* Type: string
* Required: yes

A client-generated unique identifier for this operation inside the batch.

Used for:

* debugging,
* logging,
* precise error reporting.

---

## Operation Catalog

## Cards

### `add_card`

Creates a new deck card entry.

```json
{
  "type": "add_card",
  "operation_id": "op_001",
  "card_local_id": "local_card_1",
  "oracle_card_id": "d9d11f41-3f8f-4d62-bb76-4c5c7b0b1f51",
  "zone": "mainboard",
  "quantity": 1
}
```

#### Fields

* `card_local_id`: string, required
  Temporary local identifier for the new card entry.
* `oracle_card_id`: string, required
  Identifier of the card concept being added.
* `zone`: enum, required
  One of `mainboard`, `sideboard`, `maybeboard`.
* `quantity`: integer, required
  Must be greater than or equal to `1`.

#### Notes

This specification assumes the deck refers to cards by `oracle_card_id`, not by a specific printing identifier.

---

### `remove_card`

Removes an existing deck card entry.

```json
{
  "type": "remove_card",
  "operation_id": "op_002",
  "card_ref": {
    "server_id": 101
  }
}
```

#### Fields

* `card_ref`: `EntityRef`, required

---

### `move_card_to_zone`

Moves a card entry from one zone to another.

```json
{
  "type": "move_card_to_zone",
  "operation_id": "op_003",
  "card_ref": {
    "server_id": 101
  },
  "zone": "sideboard"
}
```

#### Fields

* `card_ref`: `EntityRef`, required
* `zone`: enum, required

---

### `set_card_quantity`

Sets the quantity of a card entry.

```json
{
  "type": "set_card_quantity",
  "operation_id": "op_004",
  "card_ref": {
    "server_id": 101
  },
  "quantity": 3
}
```

#### Fields

* `card_ref`: `EntityRef`, required
* `quantity`: integer, required

#### Rules

* `quantity` must be greater than or equal to `1`
* `quantity = 0` is invalid
* card removal must be expressed using `remove_card`

---

## Tag Definitions

### `create_tag_def`

Creates a new tag definition.

```json
{
  "type": "create_tag_def",
  "operation_id": "op_005",
  "tag_def_local_id": "local_tag_def_1",
  "name": "Archetype"
}
```

#### Fields

* `tag_def_local_id`: string, required
* `name`: string, required

---

### `remove_tag_def`

Removes a tag definition.

```json
{
  "type": "remove_tag_def",
  "operation_id": "op_006",
  "tag_def_ref": {
    "server_id": 12
  }
}
```

#### Fields

* `tag_def_ref`: `EntityRef`, required

#### Note

Dependency handling is implementation-specific and must be defined by the backend. Typical strategies include:

* reject removal if dependent values or card tags exist,
* cascade delete dependent values and card tags,
* soft-delete the tag definition.

The backend must choose and document one policy.

---

### `rename_tag_def`

Renames an existing tag definition.

```json
{
  "type": "rename_tag_def",
  "operation_id": "op_007",
  "tag_def_ref": {
    "server_id": 12
  },
  "name": "Role"
}
```

#### Fields

* `tag_def_ref`: `EntityRef`, required
* `name`: string, required

---

## Tag Value Definitions

### `add_tag_value_def`

Creates a new value definition under a tag definition.

```json
{
  "type": "add_tag_value_def",
  "operation_id": "op_008",
  "tag_def_ref": {
    "local_id": "local_tag_def_1"
  },
  "tag_value_def_local_id": "local_tag_value_def_1",
  "value": "Aggro",
  "weight": 7
}
```

#### Fields

* `tag_def_ref`: `EntityRef`, required
* `tag_value_def_local_id`: string, required
* `value`: string, required
* `weight`: integer, required

#### Rules

* `weight` must be between `0` and `10`, inclusive

---

### `remove_tag_value_def`

Removes a tag value definition.

```json
{
  "type": "remove_tag_value_def",
  "operation_id": "op_009",
  "tag_value_def_ref": {
    "server_id": 55
  }
}
```

#### Fields

* `tag_value_def_ref`: `EntityRef`, required

---

### `rename_tag_value_def`

Renames a tag value definition.

```json
{
  "type": "rename_tag_value_def",
  "operation_id": "op_010",
  "tag_value_def_ref": {
    "server_id": 55
  },
  "value": "Midrange"
}
```

#### Fields

* `tag_value_def_ref`: `EntityRef`, required
* `value`: string, required

---

### `set_tag_value_def_weight`

Sets the weight of a tag value definition.

```json
{
  "type": "set_tag_value_def_weight",
  "operation_id": "op_011",
  "tag_value_def_ref": {
    "server_id": 55
  },
  "weight": 9
}
```

#### Fields

* `tag_value_def_ref`: `EntityRef`, required
* `weight`: integer, required

#### Rules

* `weight` must be between `0` and `10`, inclusive

---

## Card Tags

### `add_card_tag`

Assigns a tag value definition to a card.

```json
{
  "type": "add_card_tag",
  "operation_id": "op_012",
  "card_ref": {
    "server_id": 101
  },
  "card_tag_local_id": "local_card_tag_1",
  "tag_def_ref": {
    "server_id": 12
  },
  "tag_value_def_ref": {
    "server_id": 55
  },
  "weight": 8
}
```

#### Fields

* `card_ref`: `EntityRef`, required
* `card_tag_local_id`: string, required
* `tag_def_ref`: `EntityRef`, required
* `tag_value_def_ref`: `EntityRef`, required
* `weight`: integer, required

#### Rules

* `weight` must be between `0` and `10`, inclusive
* `tag_def_ref` and `tag_value_def_ref` must be consistent
* the referenced tag value definition must belong to the referenced tag definition

---

### `remove_card_tag`

Removes an existing card tag assignment.

```json
{
  "type": "remove_card_tag",
  "operation_id": "op_013",
  "card_tag_ref": {
    "server_id": 88
  }
}
```

#### Fields

* `card_tag_ref`: `EntityRef`, required

---

### `set_card_tag_value`

Changes the tag value definition assigned to a card tag.

```json
{
  "type": "set_card_tag_value",
  "operation_id": "op_014",
  "card_tag_ref": {
    "server_id": 88
  },
  "tag_def_ref": {
    "server_id": 12
  },
  "tag_value_def_ref": {
    "server_id": 56
  }
}
```

#### Fields

* `card_tag_ref`: `EntityRef`, required
* `tag_def_ref`: `EntityRef`, required
* `tag_value_def_ref`: `EntityRef`, required

#### Rules

* `tag_def_ref` and `tag_value_def_ref` must be consistent
* the new value definition must belong to the given tag definition

---

### `set_card_tag_weight`

Sets the weight of a card tag assignment.

```json
{
  "type": "set_card_tag_weight",
  "operation_id": "op_015",
  "card_tag_ref": {
    "server_id": 88
  },
  "weight": 5
}
```

#### Fields

* `card_tag_ref`: `EntityRef`, required
* `weight`: integer, required

#### Rules

* `weight` must be between `0` and `10`, inclusive

---

## Validation Rules

The server must validate the full batch before commit.

At minimum, the following checks should exist.

### Request-level validation

* `batch_id` must be present
* `base_version` must be present
* `operations` must be present
* `operations` must not contain duplicate `operation_id` values
* `base_version` must match the current persisted deck version
* the authenticated user must own the target deck

### Entity reference validation

For every `EntityRef`:

* at least one of `local_id` or `server_id` must be present
* if `server_id` is provided, it must refer to an entity owned by or belonging to the current deck context
* if `local_id` is used, it must be resolvable in the current batch context when required

### Operation-specific validation

Examples:

* card quantity must be `>= 1`
* weight must be between `0` and `10`
* zones must be valid
* referenced card entries must exist
* referenced tag definitions must exist
* referenced tag value definitions must exist
* referenced card tag assignments must exist
* a tag value definition must belong to the given tag definition
* a card tag must belong to the given card

### Consistency validation

The server should reject inconsistent batches, for example:

* removing a card and then modifying that same card later in the same batch,
* assigning a tag value definition from the wrong tag definition,
* referencing a `local_id` that has not been introduced,
* duplicate semantic creations that would violate uniqueness constraints.

---

## Execution Semantics

### Ordered logical processing

Operations are logically processed in the order they appear in the request.

This allows intra-batch references such as:

1. create a tag definition,
2. create a tag value definition under it using its `local_id`,
3. assign that tag to a card using the newly created value definition.

### Internal optimization

The server may internally optimize SQL execution, regroup operations, or collapse redundant changes, as long as the final result is identical to ordered logical processing.

### Local ID resolution

The server may maintain temporary in-memory mappings during batch processing, for example:

* `local_tag_def_1 -> server_id 12`
* `local_tag_value_def_1 -> server_id 55`
* `local_card_1 -> server_id 101`
* `local_card_tag_1 -> server_id 88`

These mappings must exist only for the duration of the request and must not be persisted in database storage.

### Idempotent replay

If a previously applied batch is received again with the same `batch_id`, the server must not reapply it.

The exact implementation is backend-specific, but the result must be idempotent from the client perspective.

---

## Error Format

The server may return global errors or operation-targeted errors.

Example:

```json
{
  "error": "invalid_batch",
  "message": "One or more operations are invalid.",
  "operation_errors": [
    {
      "operation_id": "op_014",
      "code": "tag_value_def_mismatch",
      "message": "The referenced tag value definition does not belong to the provided tag definition."
    }
  ]
}
```

### Fields

#### `error`

* Type: string
* Required: yes

Global error code.

#### `message`

* Type: string
* Required: yes

Human-readable summary.

#### `operation_errors`

* Type: array
* Required: no

List of operation-specific validation errors.

### Recommended error codes

Request-level:

* `conflict_version`
* `duplicate_batch_id`
* `invalid_batch`
* `forbidden_deck_access`

Operation-level:

* `unknown_card_ref`
* `unknown_tag_def_ref`
* `unknown_tag_value_def_ref`
* `unknown_card_tag_ref`
* `invalid_zone`
* `invalid_quantity`
* `invalid_weight`
* `unresolved_local_id`
* `tag_value_def_mismatch`
* `operation_dependency_error`

---

## Full Example

### Request

```json
{
  "batch_id": "batch_2026_03_19_001",
  "base_version": 12,
  "operations": [
    {
      "type": "add_card",
      "operation_id": "op_001",
      "card_local_id": "local_card_1",
      "oracle_card_id": "d9d11f41-3f8f-4d62-bb76-4c5c7b0b1f51",
      "zone": "mainboard",
      "quantity": 2
    },
    {
      "type": "create_tag_def",
      "operation_id": "op_002",
      "tag_def_local_id": "local_tag_def_1",
      "name": "Archetype"
    },
    {
      "type": "add_tag_value_def",
      "operation_id": "op_003",
      "tag_def_ref": {
        "local_id": "local_tag_def_1"
      },
      "tag_value_def_local_id": "local_tag_value_def_1",
      "value": "Aggro",
      "weight": 7
    },
    {
      "type": "add_card_tag",
      "operation_id": "op_004",
      "card_ref": {
        "local_id": "local_card_1"
      },
      "card_tag_local_id": "local_card_tag_1",
      "tag_def_ref": {
        "local_id": "local_tag_def_1"
      },
      "tag_value_def_ref": {
        "local_id": "local_tag_value_def_1"
      },
      "weight": 8
    }
  ]
}
```

### Response

```json
{
  "applied_batch_id": "batch_2026_03_19_001",
  "new_version": 13,
  "applied_operation_ids": ["op_001", "op_002", "op_003", "op_004"],
  "local_to_server_mappings": {
    "cards": [
      { "local_id": "local_card_1", "server_id": 101 }
    ],
    "tag_defs": [
      { "local_id": "local_tag_def_1", "server_id": 12 }
    ],
    "tag_value_defs": [
      { "local_id": "local_tag_value_def_1", "server_id": 55 }
    ],
    "card_tags": [
      { "local_id": "local_card_tag_1", "server_id": 88 }
    ]
  }
}
```

---

## Client-Side Recommendations

### Persist local draft state

The client should persist unsaved editor state locally.

Recommended options:

* `localStorage` for simple drafts,
* `IndexedDB` for larger or more structured drafts.

Cookies are not recommended for storing the operation list.

### Keep `local_id` stable client-side

Each local entity should keep a stable `local_id` in client memory and storage.

After synchronization, the client should attach the returned `server_id` to the same local object rather than replacing the entire local identity model.

### Prefer server IDs after synchronization

Once the server returns `server_id` values, future batches should primarily reference entities using `server_id`.

### Compress noisy local changes before submission

The client may generate many intermediate edits, for example:

* quantity changed from `1` to `2`
* then `2` to `3`
* then `3` to `4`

Before submission, the client should collapse these into a single final operation when possible:

* `set_card_quantity` to `4`

This reduces payload size and simplifies server-side processing.

---

## Card Autocomplete Strategy

A deck editor typically needs card name autocomplete.

Loading full card data for roughly 30,000 cards is too heavy for every user session, but sending a server request on every keystroke can also be unnecessarily slow.

Recommended strategy:

### Lightweight local search index

Load a compact client-side search index only when the editor is opened.

This index should contain only the minimum fields needed for autocomplete, for example:

* `oracle_card_id`
* `name`
* `normalized_name`

Do not include rich card metadata in this index.

### Cache the index

The search index should be cached by the browser so subsequent editor sessions are fast.

### Separate search data from detail data

Use two levels of card data:

#### Level 1: autocomplete index

* `oracle_card_id`
* `name`
* `normalized_name`

#### Level 2: optional detail payload

Loaded only when needed, such as:

* image
* mana cost
* type line
* colors
* other presentation details

This gives fast local autocomplete without forcing the client to preload all card details.

---

## Open Design Points

The following points are intentionally left for final backend policy decisions:

### `remove_tag_def` dependency behavior

The backend must define whether removing a tag definition:

* is rejected when dependencies exist,
* cascades to dependent tag value definitions and card tags,
* is implemented as a soft-delete.

### `oracle_card_id` versus printing-level identifier

This specification currently assumes the deck uses `oracle_card_id`.

If the product later needs edition-specific deck entries, the identifier model may need to evolve.

---

## Summary

This specification defines a batch-based deck editing API with:

* atomic server-side application,
* idempotent request handling through `batch_id`,
* optimistic conflict detection through `base_version`,
* support for temporary client-side entities through `local_id`,
* explicit operation typing,
* targeted validation and error reporting,
* a scalable card autocomplete strategy.

It is intended to serve as the detailed reference for implementation and higher-level API documentation.
