#!/usr/bin/env bash
# Bring up the OpenThreatGrid pipeline locally (topology A) with Docker Compose:
# Cowrie → Filebeat → Logstash → OpenSearch → Dashboards. Installs the index
# template, imports dashboards, seeds sample data, and prints the URLs.
set -euo pipefail

cd "$(dirname "$0")/.."

OPENSEARCH_URL="${OPENSEARCH_URL:-http://localhost:9200}"

echo "==> Starting OpenSearch + Dashboards first..."
docker compose up -d opensearch opensearch-dashboards

echo "==> Waiting for OpenSearch to become healthy..."
for _ in $(seq 1 60); do
  if curl -fsS "${OPENSEARCH_URL}/_cluster/health" >/dev/null 2>&1; then
    echo "    OpenSearch is up."
    break
  fi
  sleep 2
done

echo "==> Installing index template + dashboards (must precede first events)..."
./scripts/bootstrap_opensearch.sh || \
  echo "    (bootstrap partial — Dashboards may still be starting; re-run later)"

echo "==> Seeding sample data into OpenSearch..."
python3 scripts/seed_sample_data.py --opensearch-url "${OPENSEARCH_URL}" || \
  echo "    (seed skipped — is python3 available?)"

echo "==> Building and starting the ingestion stack (Logstash, Cowrie, Filebeat)..."
docker compose up -d --build

cat <<EOF

OpenThreatGrid is running (topology A):

  Dashboards  : http://localhost:5601  (Threat Overview)
  OpenSearch  : ${OPENSEARCH_URL}
  Honeypot    : ssh -p 2222 root@localhost

Tail logs with:   docker compose logs -f
Tear down with:   docker compose down -v
EOF
