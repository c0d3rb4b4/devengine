#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

required_files=(".env" "config/repos.json" "config/app.toml")
for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing required file: $file"
    exit 1
  fi
done

mkdir -p workspace logs postgres/data secrets

echo "Validating docker availability..."
docker --version >/dev/null
docker compose version >/dev/null

profiles=()
if grep -q '^ENABLE_REDIS=true' .env; then
  profiles+=(--profile cache)
fi
if grep -q '^ENABLE_NGROK=true' .env; then
  profiles+=(--profile tunnel)
fi

echo "Building and starting services..."
docker compose "${profiles[@]}" up -d --build

echo "Waiting briefly for API..."
sleep 5

set +e
curl -fsS "http://localhost:${API_PORT:-8000}/health"
health_status=$?
set -e

echo
if [[ $health_status -eq 0 ]]; then
  echo "devengine is up."
else
  echo "API health check did not pass yet. Check logs: docker compose logs -f api"
fi

echo "Useful commands:"
echo "  docker compose ps"
echo "  docker compose logs -f api"
echo "  docker compose logs -f agent"
echo "  ./scripts/check_health.sh"
