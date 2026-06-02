#!/usr/bin/env bash
# Verify the source-IP preservation chain:
#   attacker -> HAProxy (send-proxy-v2) -> Traefik (proxyProtocol) -> Cowrie
#
# It connects through the edge proxy and then checks that Cowrie logged the
# *real* client IP (not the Tailscale/SNAT address). Run from a host whose
# public IP you know.
set -euo pipefail

EDGE_HOST="${EDGE_HOST:-}"          # DO VPS public IP / hostname
SSH_PORT="${SSH_PORT:-2222}"
KUBE_NAMESPACE="${KUBE_NAMESPACE:-openthreatgrid}"
COWRIE_LABEL="${COWRIE_LABEL:-app=cowrie}"

if [[ -z "${EDGE_HOST}" ]]; then
  echo "Set EDGE_HOST to the DO VPS public IP/hostname." >&2
  exit 2
fi

# Determine our own public IP so we can assert Cowrie saw it.
MY_IP="$(curl -fsS https://api.ipify.org || echo "unknown")"
echo "==> This host's public IP: ${MY_IP}"

echo "==> Opening a probe SSH connection to ${EDGE_HOST}:${SSH_PORT} ..."
# We expect auth to fail (it's a honeypot); we only care that it connects and
# is logged. Timeout quickly.
ssh -o StrictHostKeyChecking=no \
    -o ConnectTimeout=10 \
    -o BatchMode=yes \
    -p "${SSH_PORT}" \
    "otg-probe-${RANDOM}@${EDGE_HOST}" true 2>/dev/null || true

echo "==> Giving the pipeline a moment to log the connection..."
sleep 3

echo "==> Checking Cowrie logs for the real source IP ..."
if command -v kubectl >/dev/null 2>&1; then
  POD="$(kubectl -n "${KUBE_NAMESPACE}" get pod -l "${COWRIE_LABEL}" \
        -o jsonpath='{.items[0].metadata.name}')"
  if kubectl -n "${KUBE_NAMESPACE}" logs "${POD}" --tail=200 \
        | grep -q "${MY_IP}"; then
    echo "PASS: Cowrie observed the real source IP ${MY_IP}."
    exit 0
  fi
  echo "FAIL: ${MY_IP} not found in Cowrie logs. Proxy Protocol chain is broken." >&2
  echo "      (Check HAProxy send-proxy-v2 and Traefik proxyProtocol.trustedIPs.)" >&2
  exit 1
else
  echo "kubectl not available; inspect Cowrie logs manually for ${MY_IP}." >&2
  exit 0
fi
