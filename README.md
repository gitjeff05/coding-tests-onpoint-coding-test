# SKU Hierarchy Coding Test

Solution to the Full Stack Software Engineer (React + Python) coding test
(see `FullStackWebDeveloper-CodingTest.pdf`).

Models the Location > Department > Category > SubCategory SKU hierarchy,
exposes it through a REST API, and provides a React UI for CRUD operations.

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React (Vite)
- **Tests:** pytest (backend), Vitest + React Testing Library (frontend)
- **Infra:** Docker Compose (postgres + backend + frontend)

## Schema

The hierarchy (Location > Department > Category > SubCategory) is modeled as
a single self-referencing `hierarchy_nodes` table (`id, parent_id, level,
name`) rather than four separate tables. It's a strict 4-level tree, so an
adjacency list keeps every level on the same CRUD surface instead of
duplicating it four times.

## Running the database

```
docker compose up -d db
docker compose build backend
docker compose run --rm backend python -m app.seed
```

This starts Postgres, builds the backend image, and loads
`backend/data/sku_hierarchy.csv` into `hierarchy_nodes`.

## Status

This is being built incrementally, exercise by exercise. See commit history
for progress; full setup/run instructions will land in this README as each
piece is completed.
