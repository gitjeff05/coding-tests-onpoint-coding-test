#!/usr/bin/env bash
# Build and deploy the full stack (db + backend + frontend) from a clean
# checkout. Only requires Docker + Docker Compose.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Building images"
docker compose build

echo "==> Starting Postgres"
docker compose up -d db

echo "==> Waiting for Postgres to be healthy"
until [ "$(docker compose ps db --format '{{.Health}}')" = "healthy" ]; do
  sleep 1
done

echo "==> Seeding database"
docker compose run --rm backend python -m app.seed

echo "==> Starting backend + frontend"
docker compose up -d backend frontend

cat <<EOF

Stack is up:
  Frontend: http://localhost:3000
  API:      http://localhost:8000
  API docs: http://localhost:8000/docs

Tear down with: docker compose down
EOF
