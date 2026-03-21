# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal portfolio site with a Next.js frontend and FastAPI backend, featuring user authentication, a Wordle-like game (Familledle), and Magic The Gathering deck management.

## Commands

### Frontend (`web/`)

```bash
cd web
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # ESLint check
npm run lint:fix     # ESLint auto-fix
npm run typecheck    # TypeScript check (no emit)
npm run format       # Prettier check
npm run format:write # Prettier auto-fix
npm run test         # Run Vitest tests
```

### Backend (`server/`)

```bash
cd server
uvicorn app.main:app --reload        # Start dev server (port 8000)
pytest                               # Run all tests
pytest app/tests/test_foo.py         # Run a single test file
pytest -k "test_name"                # Run a specific test
alembic upgrade head                 # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

### Docker

```bash
docker compose up          # Start all services (postgres, backend, web)
docker compose up postgres # Start only the database
```

## Architecture

### Monorepo Structure

- `web/` — Next.js 16 frontend (TypeScript, React 19)
- `server/` — FastAPI backend (Python, SQLModel, PostgreSQL)
- `tools/` — Data processing scripts (e.g., Scryfall MTG data import)

### Frontend Architecture (`web/src/`)

**Routing:** Next.js App Router with two route groups:
- `(protected)/` — requires authentication (dashboard, playground)
- `(public)/` — no auth required (login, register, portfolio pages, familledle)

**Feature modules** (`features/`): Self-contained features with their own `api/`, `domain/`, `hooks/`, `types.ts`, and `ui/` subdirectories. Currently: `familledle/` and `techOverview/`.

**API client** (`lib/api/`): Typed fetch wrapper (`client.ts`) that handles credentials (HttpOnly cookies), timeouts (10s), error mapping to `ApiError`, and dev-mode logging. Endpoint strings are centralized in `endpoints.ts`. Service layers (`services/`) call client functions and return typed data.

**Auth:** `AuthProvider` (React context) wraps the app and exposes `login`, `logout`, `refreshMe`, `setUser`. Protected routes check auth via layout (`(protected)/layout.tsx`).

**Formatting:** Prettier with single quotes, semicolons, 100-char width. ESLint with `simple-import-sort`.

### Backend Architecture (`server/app/`)

**Layered structure:** Routers → Services → Models/DB

- `routers/` — FastAPI route handlers (thin, delegate to services)
- `services/` — Business logic (auth flows, game logic)
- `models/tables.py` — SQLModel ORM tables
- `models/schemas.py` — Pydantic request/response schemas
- `deps.py` — FastAPI dependency injection (`get_current_auth()` for protected routes)
- `security.py` — Argon2 password hashing, session token operations
- `settings.py` — Pydantic settings loaded from environment variables

**Authentication:** Session-based with HttpOnly cookies (`session_id`). The session token is hashed before storage. Sessions have both absolute and idle expiry.

**Error responses:** Standardized format `{ code, message, fields }`. HTTP 422 for validation, 401 for unauthenticated, 409 for conflicts.

**Database models by domain:**
- Core auth: `User`, `UserEmailAddress`, `UserSession`, `PasswordResetToken`, `EmailVerificationToken`
- Game: `FamilledleAttempt`
- MTG: `MTGCard`, `MTGDeck`, `MTGTag`, `MTGBulkState`

### Dev API Proxy

In development, `next.config.ts` rewrites `/api/*` requests to `http://localhost:8000/api/*`, so the frontend always calls relative `/api/` paths.

### Database

PostgreSQL via SQLModel (SQLAlchemy ORM + Pydantic). Migrations managed with Alembic in `server/alembic/versions/`.

**Local dev DB** is started via Docker: `docker compose up postgres`

Environment variables for the DB are in `.env` (root) and `server/.env`.
