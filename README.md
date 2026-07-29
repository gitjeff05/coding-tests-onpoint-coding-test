# SKU Hierarchy Coding Test

Solution to the Full Stack Software Engineer (React + Python) coding test.

Models the Location > Department > Category > SubCategory SKU hierarchy,
exposes it through a REST API, and provides a React UI for CRUD operations.

## Quick start (build + deploy)

The whole stack (Postgres, backend, frontend, Prometheus, Grafana) builds
and deploys from a clean checkout with one script — only Docker is
required:

```
./scripts/setup.sh
```

This builds the images, starts Postgres, seeds it, and brings up
everything else. When it's done:

| Service    | URL                            | Notes                                    |
|------------|---------------------------------|-------------------------------------------|
| Frontend   | http://localhost:3000          | log in with `admin` / `admin123`          |
| API        | http://localhost:8000          | docs at `/docs`                           |
| Health     | http://localhost:8000/health   | no auth required                          |
| Prometheus | http://localhost:9090          | scrapes the backend, evaluates alert rules |
| Grafana    | http://localhost:3001          | dashboard viewable with no login; `admin`/`admin` to edit |

Run the full test suite (also Docker-only, no local Python/Node needed):

```
./scripts/test.sh
```

Tear everything down with `docker compose down` (add `-v` to also wipe the
Postgres volume).

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** React (Vite) + Tailwind CSS
- **Tests:** pytest (backend), Vitest + React Testing Library (frontend)
- **Infra:** Docker Compose (postgres + backend + frontend + Prometheus + Grafana)

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

Every route above requires authentication — see "Authentication" below.
`/auth/login` and `/docs` do not.

## Running the frontend

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Log in with `admin` / `admin123` (see
"Authentication" below) — the UI then renders the full hierarchy tree
from `GET /api/tree` and lets you add a child at any level, rename a
node, or delete a node (and its descendants), all through the REST API
above. Set `VITE_API_BASE` if the backend isn't at
`http://localhost:8000`.

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

## Authentication

All `/api/*` routes require authentication. Two schemes are accepted on
the same `Authorization` header, checked by one dependency
(`backend/app/auth.py:require_auth`):

- **HTTP Basic** — for direct/script access (curl, Postman, etc). Demo
  credentials default to `admin` / `admin123`, overridable via the
  `AUTH_USERNAME` / `AUTH_PASSWORD` env vars (also set in
  `docker-compose.yml`).
- **Bearer JWT** — what the frontend actually uses. `POST /auth/login`
  with `{"username", "password"}` checks the same demo credentials and
  returns a self-issued, HS256-signed JWT (`{"sub": username, "exp": ...}`,
  30-minute expiry, signed with the `JWT_SECRET` env var). The UI sends
  that token back as `Authorization: Bearer <token>` on every subsequent
  call.

```
curl -u admin:admin123 http://localhost:8000/api/tree

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# => {"access_token": "...", "token_type": "bearer"}
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/tree
```

The UI (`frontend/src/LoginForm.tsx`) is a plain username/password form —
not the browser's native Basic Auth popup. On success it stores the JWT
in `sessionStorage` (survives a page refresh, cleared when the tab
closes — a reasonable middle ground given the token already expires in
30 minutes; a production app would prefer an httpOnly cookie to avoid
exposing the token to XSS at all) and attaches it to every API call;
"Log out" clears it. If a call comes back `401` (token expired or
invalid) while loading/reloading the tree, the app clears the token and
drops back to the login screen automatically. A `401` returned from an
in-place edit/delete on a single node (open just long enough for the
token to expire mid-session) is a known exception — that surfaces as an
inline error on the node instead of a global redirect; logging out and
back in resolves it.

`/auth/login`, `/docs`, `/openapi.json`, `/health`, and `/metrics` do not
require auth (unauthenticated health/metrics endpoints are the norm — a
monitoring tool polling the app shouldn't need credentials). See "Health
& Monitoring" below.

**What this is, and isn't.** This demonstrates the *mechanics* of
JWT/OAuth2-style bearer tokens — issuing, signing, verifying, expiring —
without standing up a real identity provider. It is **not** how you'd
actually do authentication in production. A real deployment would
delegate identity entirely to a managed IdP — **AWS Cognito, Auth0,
Okta, or an enterprise SSO/OIDC provider** — via the **OAuth2
Authorization Code flow** (with **PKCE** for a browser SPA like this
one), with **OpenID Connect** supplying the identity layer (`id_token`,
`/userinfo`) on top of OAuth2's authorization framework. The app would
never see or store a password: it would redirect to the IdP's hosted
login page, receive a code back, exchange it for tokens, and verify
incoming JWTs by fetching the provider's **JWKS** (public signing keys,
rotated by the provider) and checking signature/issuer/audience/expiry —
rather than trusting a single static HMAC secret shared between issuer
and verifier the way this demo does. That approach also gets you
password resets, MFA, social login, and centralized user management for
free, none of which are in scope here.

## Health & Monitoring

The point of this section is being **proactive rather than reactive**:
knowing something is wrong (or trending toward wrong) before a user files
a support ticket, instead of only finding out when someone complains.

**`GET /health`** — checks the app can actually reach Postgres (`SELECT
1`), not just that the process is running. Returns `200 {"status": "ok",
"db": true}` when healthy, `503 {"status": "unhealthy", "db": false}`
when the DB is unreachable. No auth required, so any monitoring tool can
poll it directly.

**Docker Compose healthchecks** — `backend` and `frontend` both have a
`healthcheck:` block (`db` already had one). Docker polls these every 10s
independently of any human watching; a container that fails repeatedly
shows as `unhealthy` in `docker compose ps` and can be wired to
auto-restart or fail a deploy, without anyone having to notice a slow
page load first.

**Prometheus** (`http://localhost:9090`) — scrapes `GET /metrics` on the
backend (`prometheus-fastapi-instrumentator`) every 15s: request rate,
latency histograms, and status-code breakdown, labeled by route. Config
lives in `monitoring/prometheus.yml`. Three alert rules
(`monitoring/alerts.yml`) are loaded and continuously evaluated —
visible at http://localhost:9090/alerts:

- `BackendDown` — the scrape target has been unreachable for 30s
- `HighErrorRate` — more than 5% of requests are 5xx over 5 minutes
- `SlowResponses` — p95 latency has been above 1s for 5 minutes

This is the "proactive" part: these conditions fire on their own, on a
schedule, whether or not anyone is looking at a dashboard at the time.

**Grafana** (`http://localhost:3001`, dashboard viewable with no login,
`admin`/`admin` to edit) — a pre-provisioned "SKU Hierarchy API Overview"
dashboard (`monitoring/grafana/dashboards/api-overview.json`, loaded
automatically on container start, no manual click-through setup)
showing backend up/down, 5xx error rate, p95 latency, request rate by
route, and p50/p95/p99 latency over time — the trend-watching
complement to point-in-time alerts.

**What's out of scope / what production would add:** Prometheus
evaluates alert rules but nothing is currently wired to *notify* anyone
— that's normally **Alertmanager**, routing firing alerts to Slack,
PagerDuty, email, etc. (visible in Prometheus's own UI here, but silent
otherwise). A real deployment would also add: an external uptime check
(Pingdom/UptimeRobot/Route 53 health check) hitting `/health` from
outside the cluster so you catch total outages the monitoring stack
itself can't see; log-based alerting on the `WARNING`/error lines from
"Logging" above (e.g. shipped to CloudWatch/Datadog/ELK); and dashboard
alert thresholds tuned against real traffic rather than the seed-data
guesses used here.

## Status

All three exercises from the coding test are complete:

- **Exercise 1 (BUILD):** schema + seed script, REST API, React CRUD UI —
  see "Schema", "Running the API", "Running the frontend".
- **Exercise 2 (SHIP):** backend + frontend test suites, one-command
  build/deploy, CI — see "Running tests", "Quick start", "CI".
- **Exercise 3 (RUN):** logging, authentication, proactive health
  monitoring — see "Logging", "Authentication", "Health & Monitoring".

It was built incrementally, one verified step at a time — see the commit
history for that progression.
