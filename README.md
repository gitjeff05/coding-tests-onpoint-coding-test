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

## Quick start (build + deploy)

The whole stack (Postgres, backend, frontend) builds and deploys from a
clean checkout with one script — only Docker is required:

```
./scripts/setup.sh
```

This builds the images, starts Postgres, seeds it, and brings up the
backend and frontend. When it's done:

- Frontend: http://localhost:3000
- API: http://localhost:8000 (docs at `/docs`)

Run the full test suite (also Docker-only, no local Python/Node needed):

```
./scripts/test.sh
```

Tear everything down with `docker compose down` (add `-v` to also wipe the
Postgres volume).

## CI

`.github/workflows/ci.yml` runs on every push to `master`: backend tests
via pytest, and frontend type-check + Vitest + production build.

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

## Logging

The backend logs to stdout (`app.logging_config.configure_logging`, format
`timestamp level logger message`):

- `app.main`: one line per request — method, path, status code, duration.
- `app.crud`: one line per mutation (create/update/delete) and a `WARNING`
  for rejected writes (e.g. wrong parent level) or operations on missing
  nodes.

View it with `docker compose logs -f backend`.

## Status

This is being built incrementally, exercise by exercise. See commit history
for progress; full setup/run instructions will land in this README as each
piece is completed.
