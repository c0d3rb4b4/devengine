#!/usr/bin/env bash
set -euo pipefail

API_PORT="${API_PORT:-8000}"

curl -fsS "http://localhost:${API_PORT}/health" | jq .
echo

echo "Compose services:"
docker compose ps
