# API Specification

## Overview
This API provides:
- User accounts with authentication
- Password-based login and password reset
- A protected Task resource (CRUD)
- A RESTful, JSON-based interface

Authentication is handled via **Bearer tokens**.  

---

## Authentication

### Register
`POST /auth/register`

**Body**
```json
{
  "email": "string",
  "password": "string",
  "username": "string"
} 
```

**Response — 201**
```json
{
  "accessToken": "string",
  "user": UserDTO
}
```

---

### Login

`POST /auth/login`

**Body**

```json
{
  "email": "string",
  "password": "string"
}
```
**Response — 200**

```json
{
  "accessToken": "string",
  "user": UserDTO
}
```
---
### Request password reset
`POST /auth/reset-password/request`

**Body**

```json
{
  "email": "string"
}
``` 

**Response — 204**
---
### Confirm password reset
`POST /auth/reset-password/confirm`

**Body**

```json
{
  "token": "string",
  "newPassword": "string"
}
```
**Response — 204**
---
### Authentication rules
- Protected routes require:

```makefile
Authorization: Bearer <accessToken>
```

- Missing or invalid token → `401 Unauthorized`

---
### Users
**Get current user**
`GET /users/me`

**Response — 200**

```json
{
  "id": 1,
  "email": "string",
  "username": "string",
  "createdAt": "ISO-8601"
}
```
---
### Update current user
`PATCH /users/me`

**Body**

```json
{
  "username": "string"
}
```
**Response — 200**

```json
UserDTO
```
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
---
### List tasks
`GET /tasks`

**Query parameters**

- ``page`` (number, ≥1)

- ``limit`` (number)

- ``done`` (``true | false``)

- ``tag`` (string)

- ``sort`` (``createdAt``)

- ``order`` (``asc | desc``)

**Response — 200**

```json
{
  "data": [TaskDTO]
}
```
---
### Get task by id
`GET /tasks/{id}`

**Response — 200**

```json
TaskDTO
```

---
### Create task
`POST /tasks`

**Body**

```json
{
  "title": "string",
  "tags": ["string"]
}
```
**Response — 201**

```json
TaskDTO
```

---
### Update task
`PATCH /tasks/{id}`


**Body**

```json
{
  "title": "string",
  "done": true,
  "tags": ["string"]
}
```
**Response — 200**

```json
TaskDTO
```

---
### Delete task
DELETE /tasks/{id}
```

**Response — 204**

Ownership rules
A task belongs to exactly one user

Accessing or modifying another user’s task → 403 Forbidden

Error format
All errors follow the same structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```
Common error codes
``VALIDATION_ERROR`` → 400

``INVALID_CREDENTIALS`` → 401

``UNAUTHORIZED`` → 401

``FORBIDDEN`` → 403

``NOT_FOUND`` → 404

``EMAIL_TAKEN`` → 409

``RESET_TOKEN_INVALID`` → 400

``INTERNAL_ERROR`` → 500

## Notes
- IDs are integers (SQLite auto-increment)
- Passwords are never returned
- No logout endpoint (stateless tokens)
- OpenAPI specification is provided separately