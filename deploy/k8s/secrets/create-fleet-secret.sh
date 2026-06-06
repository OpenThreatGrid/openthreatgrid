#!/usr/bin/env bash
# Create the "otg-fleet-values" Secret that Rancher Fleet merges into the Helm
# chart via helm.valuesFrom (see fleet.yaml). Keeps the Postgres/Grafana
# passwords OUT of Git.
#
# The Secret must exist in the openthreatgrid namespace on the TARGET cluster
# BEFORE Fleet renders the bundle (Fleet reads it at deploy time).
#
# Usage:
#   ./create-fleet-secret.sh                 # generate random passwords + apply
#   POSTGRES_PASSWORD=... GRAFANA_PASSWORD=... ./create-fleet-secret.sh
#   ./create-fleet-secret.sh --dry-run       # print the manifest, don't apply
set -euo pipefail

NAMESPACE="${NAMESPACE:-openthreatgrid}"
SECRET_NAME="${SECRET_NAME:-otg-fleet-values}"

gen() { openssl rand -hex 16; }
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(gen)}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-$(gen)}"

# The Secret's single key "values.yaml" is a Helm values fragment that Fleet
# layers on top of the chart defaults.
VALUES_YAML="$(cat <<EOF
postgres:
  auth:
    password: ${POSTGRES_PASSWORD}
grafana:
  adminPassword: ${GRAFANA_PASSWORD}
EOF
)"

if [[ "${1:-}" == "--dry-run" ]]; then
  kubectl create secret generic "${SECRET_NAME}" \
    --namespace "${NAMESPACE}" \
    --from-literal=values.yaml="${VALUES_YAML}" \
    --dry-run=client -o yaml
  exit 0
fi

# Ensure the namespace exists (Fleet would create it later, but the Secret must
# land here first).
kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || \
  kubectl create namespace "${NAMESPACE}"

# Idempotent create-or-update.
kubectl create secret generic "${SECRET_NAME}" \
  --namespace "${NAMESPACE}" \
  --from-literal=values.yaml="${VALUES_YAML}" \
  --dry-run=client -o yaml | kubectl apply -f -

cat <<EOF

Secret '${SECRET_NAME}' applied to namespace '${NAMESPACE}'.

  Grafana admin password : ${GRAFANA_PASSWORD}
  Postgres password      : ${POSTGRES_PASSWORD}

Save the Grafana password now — it is not stored anywhere else.
Fleet will pick these up on the next bundle sync (helm.valuesFrom in fleet.yaml).
EOF
