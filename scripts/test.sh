#!/usr/bin/env bash
# Run the full test suite (backend + frontend) without requiring anything
# installed locally besides Docker.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Backend tests"
docker compose build backend
docker compose run --rm backend python -m pytest -v

echo "==> Frontend tests"
docker run --rm -v "$(pwd)/frontend:/app" -w /app node:22-alpine sh -c "npm ci && npm test"
