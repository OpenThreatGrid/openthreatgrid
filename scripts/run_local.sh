#!/usr/bin/env bash
# Bring up the full OpenThreatGrid pipeline locally with Docker Compose,
# wait for the API, seed sample data, and print the useful URLs.
set -euo pipefail

cd "$(dirname "$0")/.."

API_URL="${API_URL:-http://localhost:8000}"

echo "==> Building and starting the stack..."
docker compose up -d --build

echo "==> Waiting for the API to become ready..."
for _ in $(seq 1 60); do
  if curl -fsS "${API_URL}/health" >/dev/null 2>&1; then
    echo "    API is up."
    break
  fi
  sleep 2
done

echo "==> Installing OpenSearch index template + dashboards..."
./scripts/bootstrap_opensearch.sh || \
  echo "    (bootstrap skipped — OpenSearch/Dashboards may still be starting; re-run later)"

echo "==> Seeding sample data..."
python3 scripts/seed_sample_data.py --api-url "${API_URL}" || \
  echo "    (seed skipped — is python3 available?)"

cat <<EOF

OpenThreatGrid is running:

  API docs    : ${API_URL}/docs
  API health  : ${API_URL}/health
  Stats       : ${API_URL}/api/v1/stats/summary
  Dashboards  : http://localhost:5601  (Threat Overview)
  OpenSearch  : http://localhost:9200

Tail logs with:   docker compose logs -f
Tear down with:   docker compose down -v
EOF
