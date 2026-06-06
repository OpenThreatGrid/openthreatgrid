#!/usr/bin/env bash
# Install the OpenThreatGrid index template and import the Dashboards saved
# objects. Safe to re-run. Override endpoints/credentials via env vars.
#
#   OPENSEARCH_URL   (default http://localhost:9200)
#   DASHBOARDS_URL   (default http://localhost:5601)
#   OS_USER / OS_PASS  optional basic-auth credentials
set -euo pipefail

OPENSEARCH_URL="${OPENSEARCH_URL:-http://localhost:9200}"
DASHBOARDS_URL="${DASHBOARDS_URL:-http://localhost:5601}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

auth=()
if [[ -n "${OS_USER:-}" ]]; then
  auth=(-u "${OS_USER}:${OS_PASS:-}")
fi

echo "==> Installing index template otg-events"
curl -sk "${auth[@]}" -X PUT \
  "${OPENSEARCH_URL}/_index_template/otg-events" \
  -H 'Content-Type: application/json' \
  --data-binary "@${ROOT}/opensearch/index-templates/otg-events.json"
echo

echo "==> Importing Dashboards saved objects"
curl -sk "${auth[@]}" -X POST \
  "${DASHBOARDS_URL}/api/saved_objects/_import?overwrite=true" \
  -H 'osd-xsrf: true' \
  --form "file=@${ROOT}/opensearch/dashboards/otg-dashboards.ndjson"
echo

echo "==> Done. Open ${DASHBOARDS_URL} → Dashboards → 'OpenThreatGrid — Threat Overview'"
