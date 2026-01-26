
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
  }
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

---

## Notes

* IDs are integers (SQLite auto-increment)
* Passwords are never returned
* Auth is cookie-based (`session_id`, HttpOnly). No Bearer tokens.
* In production, the session cookie must be `Secure` (HTTPS).
