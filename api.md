
# API Specification

## Overview

This API provides:

* User accounts with cookie-based authentication (server-side sessions)
* Email verification (pending → verified)
* A protected Task resource (CRUD)
* A RESTful, JSON-based interface

Authentication is handled via an **HttpOnly cookie** named `session_id` (no Bearer token).

---

## Conventions

### Content type

Requests and responses are JSON unless stated otherwise.

### Error format

All errors use the same JSON structure:

```json
{
  "code": "ERROR_CODE",
  "message": "Human readable message",
  "fields": {}
}
```

* Validation errors return **422**.
* Auth errors typically return **401**.
* Conflicts return **409**.

### Validation error (422) example

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Invalid request.",
  "fields": {
    "password": "invalid",
    "username": "invalid"
  }
}
```

---

## Authentication (cookie sessions)

### Session cookie

On successful **register** and **login**, the API sets:

* Cookie name: `session_id`
* `HttpOnly`: true
* `SameSite`: `lax`
* `Path`: `/`
* `Secure`: **true in production** (HTTPS)

The cookie lifetime depends on `remember_me`.

### Protected routes

Protected routes require a valid `session_id` cookie:

* Missing cookie → 401 `NOT_AUTHENTICATED`
* Invalid/revoked/expired session → 401 `SESSION_INVALID` / `SESSION_REVOKED` / `SESSION_EXPIRED`
* Inactive user → 401 `USER_INACTIVE`

---

## Auth endpoints

### Register

`POST /auth/register` — **201**

Creates a user and (optionally) adds a pending email + sends a verification email.

**Body**

```json
{
  "email": "string | null",
  "username": "string",
  "password": "string",
  "remember_me": false
}
```

**Rules**

* `username`: 3–25 chars, regex `^[a-zA-Z0-9_]+$`, whitespace trimmed
* `password`: 8–128 chars and must include:

  * at least 1 lowercase
  * at least 1 uppercase
  * at least 1 digit
  * at least 1 symbol
* `email`: optional; normalized server-side

**Response (201)**

```json
{
  "id": 1,
  "username": "string"
}
```

**Errors**

* 409 `USERNAME_TAKEN`
* 409 `EMAIL_TAKEN`
* 409 `CONSTRAINT_VIOLATION`
* 422 `VALIDATION_ERROR`

---

### Login

`POST /auth/login` — **200**

Authenticates using `identifier` (username OR verified email) + password.

**Body**

```json
{
  "identifier": "string",
  "password": "string",
  "remember_me": false
}
```

**Response (200)**

```json
{
  "ok": true,
  "user": {
    "id": 1,
    "username": "string"
  }
}
```

**Errors**

* 401 `INVALID_CREDENTIALS`
* 409 `SESSION_CONFLICT`
* 422 `VALIDATION_ERROR`

---

### Logout (protected)

`POST /auth/logout` — **204**

Revokes current session and deletes the `session_id` cookie.

**Errors**

* 401 `NOT_AUTHENTICATED`
* 401 `SESSION_INVALID`
* 401 `SESSION_REVOKED`
* 401 `SESSION_EXPIRED`
* 401 `USER_INACTIVE`

---

### Get current user (protected)

`GET /auth/me` — **200**

Returns user identity + email status.

**Response (200)**

```json
{
  "id": 1,
  "username": "string",
  "email": {
    "primary": "string | null",
    "pending": "string | null",
    "verification_sent_at": "ISO-8601 | null"
  },
  "is_family":"boolean"
}
```

**Errors**

* 401 `NOT_AUTHENTICATED`
* 401 `SESSION_INVALID`
* 401 `SESSION_REVOKED`
* 401 `SESSION_EXPIRED`
* 401 `USER_INACTIVE`

---

## Email verification

### Send verification email (protected)

`POST /auth/email/verification/send` — **200**

Sends a verification email for the current user’s pending email.

**Response (200)**

```json
{
  "ok": true,
  "sent_at": "ISO-8601",
  "expires_at": "ISO-8601"
}
```

**Errors**

* 404 `PENDING_EMAIL_MISSING`
* 409 `PENDING_EMAIL_CONFLICT`
* 429 `EMAIL_VERIFICATION_RATE_LIMITED`
* 401 `NOT_AUTHENTICATED`
* 401 `SESSION_INVALID`
* 401 `SESSION_REVOKED`
* 401 `SESSION_EXPIRED`
* 401 `USER_INACTIVE`

---

### Verify token

`POST /auth/email/verification/verify` — **200**

Consumes a verification token and promotes pending email to verified.

**Body**

```json
{
  "token": "string"
}
```

**Response (200)**

```json
{
  "ok": true
}
```

**Errors**

* 401 `EMAIL_TOKEN_INVALID`
* 422 `VALIDATION_ERROR`

---

## Decks (protected)

> Full batch specification: [`deck_batch_operation.md`](deck_batch_operation.md)

### Get deck

`GET /decks/{deck_id}` — **200**

Returns the current deck state including its version. Used to resolve conflicts after a rejected batch.

**Errors**

* 403 `FORBIDDEN`
* 404 `NOT_FOUND`

---

### Apply batch operations

`POST /decks/{deck_id}/apply-operations` — **200**

Applies a list of deck operations atomically. The batch is idempotent via `batch_id`.

**Body**

```json
{
  "batch_id": "string",
  "base_version": 12,
  "operations": []
}
```

* `operations`: ordered list of typed operations (1–500 items). See [`deck_batch_operation.md`](deck_batch_operation.md) for the full operation catalog.
* `base_version` must match the current deck version, otherwise returns 409 `conflict_version`.
* If `batch_id` was already applied, the server returns the original response without reapplying.

**Response (200)**

```json
{
  "applied_batch_id": "string",
  "new_version": 13,
  "applied_operation_ids": ["op_001"],
  "local_to_server_mappings": {
    "cards": [],
    "tag_defs": [],
    "tag_value_defs": [],
    "card_tags": []
  }
}
```

**Error format** (differs from standard — batch errors include per-operation detail)

```json
{
  "error": "invalid_batch",
  "message": "string",
  "operation_errors": [
    { "operation_id": "op_001", "code": "string", "message": "string" }
  ]
}
```

**HTTP errors**

* 400 `invalid_batch` — empty operations or malformed request
* 400 `batch_too_large` — more than 500 operations
* 403 `forbidden_deck_access`
* 409 `conflict_version` — `base_version` mismatch
* 422 `invalid_batch` — semantic errors (invalid refs, bad quantities, etc.)

---

## Riftdle

### Get champion data

`GET /riftdle/champ_data/{champion_name}` — **200**

Returns stats and ranks for a given champion.

**Response (200)**

```json
{
  "name": "string",
  "data": {
    "skin_number": 0,
    "family_mastery": ["string"],
    "mobility": 0,
    "randomness": 0,
    "cc_quantity": 0,
    "icon_url": "string",
    "mean_hex": "string",
    "mean_hue": 0,
    "mobility_rank": 1,
    "randomness_rank": 1,
    "cc_quantity_rank": 1,
    "total_champions": 100
  }
}
```

**Errors**

* 404 `INVALID_CHAMPION_NAME`

---

### Get daily game

`GET /riftdle/daily_game` — **200**

Returns the configuration for today's game: the champion to guess, which row columns are active, and the current winner count.

**Response (200)**

```json
{
  "day": "2026-03-21",
  "champ_name": "string",
  "row_columns": ["family_mastery", "colorwheel", "mobility", "randomness", "cc_quantity"],
  "winner_count": 0
}
```

`row_columns` is a subset of: `family_mastery`, `colorwheel`, `mobility`, `randomness`, `cc_quantity`.

**Errors**

* 404 `NO_DAILY_GAME`

---

### Submit a guess

`POST /riftdle/attempts/guess` — **200**

Submits a champion guess for today's game. Works for anonymous and authenticated users. Authenticated users have their attempt persisted; `winner_count` is incremented on a correct guess.

**Body**

```json
{
  "champion_name": "string"
}
```

**Response (200)**

```json
{
  "attempt": {
    "id": 1,
    "day": "2026-03-21",
    "try_count": 3,
    "finished_at": "ISO-8601 | null"
  },
  "guess": {
    "position": 2,
    "champion_name": "string",
    "is_correct": false
  }
}
```

For anonymous users, `attempt` is `null` and `position` is `null`.

**Errors**

* 404 `INVALID_CHAMPION_NAME`
* 404 `NO_DAILY_GAME`
* 409 `ATTEMPT_ALREADY_FINISHED`

---

### Get today's attempt (protected)

`GET /riftdle/attempts/today` — **200**

Returns the authenticated user's attempt for today, if any.

**Response (200)**

```json
{
  "exists": false,
  "attempt": null
}
```

```json
{
  "exists": true,
  "attempt": {
    "day": "2026-03-21",
    "is_finished": true,
    "champions": ["string"]
  }
}
```

**Errors**

* 401 `NOT_AUTHENTICATED`

---

## MTGDoku

A daily Magic: The Gathering grid puzzle (Immaculate Grid style). Each daily game has three 3×3 grids (easy / medium / hard). Rows and columns each have a set of conditions (categories), and the player must find a card that satisfies both the row and column conditions for each cell.

### Shared types

**`ConditionOut`**
```json
{ "id": "string", "label": "string", "weight": 1.0, "total": 120, "known": 80 }
```
- `total`: total valid cards for this condition
- `known`: valid cards from the "known" subset

**`GroupOut`** — a row or column
```json
{ "conditions": [ConditionOut], "total": 50, "known": 30 }
```

**`CellOut`** — intersection stats (no attempt context)
```json
{ "total": 10, "known": 7 }
```

**`CellWithAttemptOut`** — intersection stats + player's guesses
```json
{ "total": 10, "known": 7, "cards_tried": [{ "oracle_id": "string", "name": "string", "is_valid": true }] }
```

**`GridOut`**
```json
{
  "id": 1,
  "difficulty": "easy",
  "score": 42.5,
  "difficulty_score": 0.3,
  "rows": [GroupOut, GroupOut, GroupOut],
  "cols": [GroupOut, GroupOut, GroupOut],
  "cells": [[CellOut, CellOut, CellOut], ...]
}
```
`difficulty` is one of `"easy"`, `"medium"`, `"hard"`.

**`GridWithAttemptOut`** — same as `GridOut` but `cells` contains `CellWithAttemptOut`.

**`DailyGameOut`**
```json
{ "id": 1, "day": "2026-03-29", "easy": GridOut | null, "medium": GridOut | null, "hard": GridOut | null }
```

**`AttemptOut`**
```json
{
  "id": 1,
  "day": "2026-03-29",
  "won_easy": false,
  "won_medium": false,
  "won_hard": false,
  "finished_at": "ISO-8601 | null",
  "guesses": [GuessOut]
}
```

**`GuessOut`**
```json
{ "id": 1, "position": 0, "difficulty": "easy", "cell_row": 0, "cell_col": 1, "oracle_id": "string", "card_name": "string", "is_valid": true }
```

**`GuessResultOut`**
```json
{ "is_valid": true, "oracle_id": "string", "card_name": "string | null", "attempt": AttemptOut | null }
```
`attempt` is `null` for anonymous users.

---

### Get grid

`GET /mtgdoku/grid/{grid_id}` — **200**

Returns a grid without attempt context.

**Response (200):** `GridOut`

**Errors**
- 404 grid not found

---

### Get grid with attempt (protected)

`GET /mtgdoku/grid/{grid_id}/attempt/{attempt_id}` — **200**

Returns the grid with the player's card guesses per cell.

**Response (200):** `GridWithAttemptOut`

**Errors**
- 401 `NOT_AUTHENTICATED`
- 404 grid or attempt not found

---

### Get today's daily game

`GET /mtgdoku/daily` — **200**

Returns today's daily game with all three grids.

**Response (200):** `DailyGameOut`

**Errors**
- 404 no daily game for today

---

### Get today's attempt (protected)

`GET /mtgdoku/daily/attempt` — **200**

Returns the authenticated user's attempt for today.

**Response (200):** `AttemptOut`

**Errors**
- 401 `NOT_AUTHENTICATED`
- 404 no attempt found for today

---

### Get daily game by id

`GET /mtgdoku/daily/{daily_game_id}` — **200**

**Response (200):** `DailyGameOut`

**Errors**
- 404 not found

---

### Submit a guess

`POST /mtgdoku/daily/guess` — **200**

Works for both anonymous and authenticated users. Anonymous users get validation only (no persistence). A difficulty is won when all 9 cells are correctly filled.

**Body**
```json
{ "difficulty": "easy", "cell_row": 0, "cell_col": 1, "oracle_id": "string" }
```
- `difficulty`: `"easy"` | `"medium"` | `"hard"`
- `cell_row`, `cell_col`: 0-indexed position in the 3×3 grid
- `oracle_id`: Scryfall oracle ID of the guessed card

**Response (200):** `GuessResultOut`

**Errors**
- 400 invalid difficulty
- 404 no daily game, grid not found, or card not found
- 409 cell already won / duplicate card in cell / max guesses reached

---

### Check card validity

`GET /mtgdoku/check` — **200**

Checks whether a card satisfies both conditions for a given cell, without any game state side effects.

**Query parameters**
- `grid_id` (int)
- `cell_row` (int)
- `cell_col` (int)
- `oracle_id` (string)

**Response (200)**
```json
{ "is_valid": true, "oracle_id": "string", "card_name": "string | null" }
```

---

### List categories

`GET /mtgdoku/categories` — **200**

Returns all available card filter categories (60+).

**Response (200)**
```json
[{ "id": "c=w", "label": "Mono-blanc", "group": "exact_color" }]
```

Category groups: `exact_monocolor`, `exact_bicolor`, `at_least_color`, `cmc`, `type`, `power`, `toughness`, `keyword`, `mention`.

---

### Category stats

`GET /mtgdoku/category-stats` — **200**

Returns card counts per category.

**Response (200)**
```json
[{ "id": "c=w", "label": "Mono-blanc", "group": "exact_color", "count": 320 }]
```

---

### Pair count

`GET /mtgdoku/pair-count` — **200**

Returns the number of cards satisfying two categories simultaneously (cell difficulty estimate).

**Query parameters**
- `cat1` (string) — category id
- `cat2` (string) — category id

**Response (200)**
```json
{ "cat1": "c=w", "cat2": "flying", "count": 45 }
```

**Errors**
- 200 with `{ "error": "unknown_category", "category": "..." }` if a category id is invalid

---

## Tasks (protected)

### Task model (response)

```json
{
  "id": 1,
  "title": "string",
  "done": false,
  "tags": ["string"],
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601"
}
```

### List tasks

`GET /tasks` — **200**

**Query parameters**

* `page` (number, ≥1)
* `limit` (number)
* `done` (`true | false`)
* `tag` (string)
* `sort` (`createdAt`)
* `order` (`asc | desc`)

**Response (200)**

```json
{
  "data": [TaskDTO]
}
```

### Get task by id

`GET /tasks/{id}` — **200**

**Response**

```json
TaskDTO
```

### Create task

`POST /tasks` — **201**

**Body**

```json
{
  "title": "string",
  "tags": ["string"]
}
```

**Response**

```json
TaskDTO
```

### Update task

`PATCH /tasks/{id}` — **200**

**Body**

```json
{
  "title": "string",
  "done": true,
  "tags": ["string"]
}
```

**Response**

```json
TaskDTO
```

### Delete task

`DELETE /tasks/{id}` — **204**

### Ownership rules

A task belongs to exactly one user.

Accessing or modifying another user’s task → 403 `FORBIDDEN`

---

## Common error codes

* `VALIDATION_ERROR` → 422
* `INVALID_CREDENTIALS` → 401
* `NOT_AUTHENTICATED` → 401
* `SESSION_INVALID` → 401
* `SESSION_REVOKED` → 401
* `SESSION_EXPIRED` → 401
* `USER_INACTIVE` → 401
* `USERNAME_TAKEN` → 409
* `EMAIL_TAKEN` → 409
* `CONSTRAINT_VIOLATION` → 409
* `SESSION_CONFLICT` → 409
* `PENDING_EMAIL_MISSING` → 404
* `PENDING_EMAIL_CONFLICT` → 409
* `EMAIL_VERIFICATION_RATE_LIMITED` → 429
* `EMAIL_TOKEN_INVALID` → 401
* `EMAIL_ALREADY_VERIFIED` → 400
* `EMAIL_NOT_OWNED` → 400
* `EMAIL_NOT_VERIFIED` → 400
* `FORBIDDEN` → 403
* `NOT_FOUND` → 404
* `INTERNAL_ERROR` → 500

Deck batch error codes (use `error` key, not `code`):

* `conflict_version` → 409
* `duplicate_batch_id` → 200 (idempotent replay)
* `invalid_batch` → 400 / 422
* `batch_too_large` → 400
* `forbidden_deck_access` → 403
* `immutable_tag_def` → 422

---

## Notes

* IDs are integers (SQLite auto-increment)
* Passwords are never returned
* Auth is cookie-based (`session_id`, HttpOnly). No Bearer tokens.
* In production, the session cookie must be `Secure` (HTTPS).
