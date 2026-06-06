#!/usr/bin/env bash
# Create the otg-basic-auth Secret consumed by the Traefik BasicAuth middleware.
# Keeps the credentials out of Git.
#
# Usage:
#   ./create-basic-auth.sh <username> [password]
#   (password omitted -> generated and printed once)
set -euo pipefail

NAMESPACE="${NAMESPACE:-openthreatgrid}"
USER="${1:?usage: create-basic-auth.sh <username> [password]}"
PASS="${2:-$(openssl rand -base64 12)}"

# Traefik BasicAuth expects an htpasswd-style entry under the "users" key.
if command -v htpasswd >/dev/null 2>&1; then
  ENTRY="$(htpasswd -nbB "${USER}" "${PASS}")"
else
  # Fallback: bcrypt via openssl is not available; use apr1 via openssl passwd.
  ENTRY="${USER}:$(openssl passwd -apr1 "${PASS}")"
fi

kubectl create secret generic otg-basic-auth \
  --namespace "${NAMESPACE}" \
  --from-literal=users="${ENTRY}" \
  --dry-run=client -o yaml | kubectl apply -f -

cat <<EOF

Secret 'otg-basic-auth' applied to namespace '${NAMESPACE}'.
  Dashboard/API login:  ${USER} / ${PASS}

Save this password — it is not stored anywhere else.
EOF
