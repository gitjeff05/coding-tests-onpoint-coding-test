# SKU Hierarchy Coding Test

Solution to the Full Stack Software Engineer (React + Python) coding test
(see `FullStackWebDeveloper-CodingTest.pdf`).

Models the Location > Department > Category > SubCategory SKU hierarchy,
exposes it through a REST API, and provides a React UI for CRUD operations.

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React (Vite) + Tailwind CSS
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

## Running the API

```
docker compose up -d db backend
```

API docs (Swagger UI) at http://localhost:8000/docs.

| Method | Path              | Description                                  |
|--------|-------------------|-----------------------------------------------|
| GET    | /api/nodes        | List nodes, optional `level`/`parent_id` filters |
| GET    | /api/tree         | Full nested tree from the root locations down |
| GET    | /api/nodes/{id}   | Get one node                                  |
| POST   | /api/nodes        | Create a node (`level`, `name`, `parent_id`)  |
| PUT    | /api/nodes/{id}   | Update a node's `name`/`parent_id`            |
| DELETE | /api/nodes/{id}   | Delete a node (cascades to descendants)       |

Creates/updates validate that a node's `level` matches its parent's expected
level (e.g. a `department` must have a `location` parent) and return `400`
otherwise.

## Running the frontend

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The UI renders the full hierarchy tree from
`GET /api/tree` and lets you add a child at any level, rename a node, or
delete a node (and its descendants), all through the REST API above. Set
`VITE_API_BASE` if the backend isn't at `http://localhost:8000`.

## Running tests

Backend (pytest, against an isolated in-memory SQLite DB, no Postgres needed):

```
docker compose run --rm backend python -m pytest -v
```

Frontend (Vitest + React Testing Library, API calls mocked):

```
cd frontend
npm test
```

## Status

This is being built incrementally, exercise by exercise. See commit history
for progress; full setup/run instructions will land in this README as each
piece is completed.
