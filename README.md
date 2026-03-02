# tristancoldefy.com

**tristancoldefy.com** est mon **site personnel** (portfolio) avec un **backend applicatif** (comptes, auth, emails/sessions) et des **pages/projets interactifs** (ex: *Familledle*).

## Structure

* **Frontend** : application **Next.js** (TypeScript) pour le site vitrine + UI.
* **Backend** : API **FastAPI** + base de données (comptes, auth, gestion d’emails, sessions/cookies, etc.).

## Fonctionnalités principales

* Création de compte / connexion
* Hash de mot de passe (**Argon2** via `passlib`/`argon2-cffi`)
* Gestion d’emails (primary/pending, validation, etc.)
* Auth par **session cookies**
* API structurée (service layer) + migrations DB (Alembic)

## Technologies

### Backend

* **FastAPI**, **Uvicorn**
* **SQLModel / SQLAlchemy**, **Alembic**
* **PostgreSQL** (prod) + **psycopg**
* **SQLite** (dev/tests selon besoin)
* **pydantic-settings**
* **pytest** (tests, en cours de remise à jour)

### Frontend

* **Next.js** (App Router), **React**, **TypeScript**
* **Radix UI**
* **CSS Modules**

### Infra / déploiement

* **Docker / Docker Compose**
* **Caddy** (reverse proxy / TLS)

## Statut

Projet en cours : le contenu, le design et les fonctionnalités évoluent régulièrement.
