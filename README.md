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

The hierarchy (Location > Department > Category > SubCategory) is modeled
as a single self-referencing table, `hierarchy_nodes`, rather than four
separate tables (`locations`, `departments`, `categories`,
`subcategories`):

| Column      | Type                                | Notes                                      |
|-------------|-------------------------------------|---------------------------------------------|
| `id`        | integer, primary key                |                                             |
| `parent_id` | integer, FK to `hierarchy_nodes.id`, nullable | `NULL` only for `location` rows (the roots) |
| `level`     | enum: `location`/`department`/`category`/`subcategory` | which tier of the hierarchy this row represents |
| `name`      | string                              | e.g. "Bakery", "Cheese Sauce"               |

This is the **adjacency list** pattern: every row is a node, and a row
points at its parent via `parent_id` instead of living in a
level-specific table with a level-specific foreign key
(`departments.location_id`, `categories.department_id`, etc.).

**Why this instead of four tables.** The source data is a strict,
fixed-depth 4-level tree — every subcategory always has exactly one
category parent, every category exactly one department parent, and so on.
Four separate tables would model that same tree, but every level would
need its own table, its own set of Pydantic schemas, its own CRUD
functions, and its own REST routes — four near-identical copies of the
same create/read/update/delete logic. Collapsing all four levels into one
table means one model, one schema, one `crud.py`, and one set of
`/api/nodes` routes handle every level; the UI's recursive tree component
follows the same shape. The tradeoff is that the database itself can't
enforce "a department's parent must be a location" the way a real foreign
key to a `locations` table would — that constraint is enforced in
application code instead (see below), not by the schema.

**Enforcing hierarchy order.** Because any node can technically point to
any other node as its parent, `backend/app/crud.py` keeps a small
`LEVEL_PARENT` map (`department -> location`, `category -> department`,
`subcategory -> category`, `location -> None`) and calls
`validate_parent()` on every create/update. It checks that a `location`
has no parent, and that every other level's `parent_id` points at an
existing node whose `level` is exactly the expected one — e.g. you can't
attach a `category` directly under a `location`, or under another
`category`. A violation raises a `ValueError`, which the API layer turns
into a `400` (see the CRUD API table below).

**Cascading delete.** The SQLAlchemy relationship on `HierarchyNode` is
declared with `cascade="all, delete-orphan"`, so deleting a node (say, a
`department`) deletes its entire subtree (`category` and `subcategory`
rows underneath it) in the same operation — you don't have to walk the
tree and delete leaf-first yourself.

**Uniqueness.** A `UniqueConstraint` on `(parent_id, name)` stops two
siblings under the same parent from having the same name (e.g. two
"Cheese" categories under the same "Dairy" department), while still
allowing the same name to reappear elsewhere in the tree as long as the
parent differs. The seed data actually relies on this: under Floral,
there's a category named "Gifts" (child of the "Floral" department) and a
subcategory also named "Gifts" (child of that category) — same string,
different `parent_id`, so both rows are allowed. The same pattern shows up
for "Plants", "Kitchen Accessories", "Stuffing Products", and a few
others.

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
