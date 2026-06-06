#!/usr/bin/env bash
# Build and push the OpenThreatGrid custom images to a container registry.
#
# These are the images that were ErrImagePull (they don't exist until built):
#   otg-api, otg-worker, otg-reports, cowrie
#
# Usage:
#   echo "$GHCR_PAT" | docker login ghcr.io -u wahyurendra --password-stdin
#   ./scripts/build_push_images.sh
#
# Env overrides:
#   REGISTRY  (default ghcr.io/openthreatgrid)
#   TAG       (default latest)
#   PLATFORM  (default linux/amd64 — match your cluster nodes)
set -euo pipefail

cd "$(dirname "$0")/.."

REGISTRY="${REGISTRY:-ghcr.io/openthreatgrid}"
TAG="${TAG:-main}"
PLATFORM="${PLATFORM:-linux/amd64}"

# image-name : build-context
images=(
  "otg-api:backend/otg-api"
  "otg-worker:workers/otg-worker"
  "otg-reports:reports"
  "cowrie:sensors/cowrie"
)

for entry in "${images[@]}"; do
  name="${entry%%:*}"
  context="${entry#*:}"
  ref="${REGISTRY}/${name}:${TAG}"
  echo "==> Building ${ref} (context: ${context})"
  docker build --platform "${PLATFORM}" -t "${ref}" "${context}"
  echo "==> Pushing ${ref}"
  docker push "${ref}"
done

cat <<EOF

All images pushed to ${REGISTRY} (tag ${TAG}).

If these GHCR packages are PRIVATE, either:
  1. Make them public:  GitHub → your profile → Packages → <pkg> → Settings →
     Change visibility → Public, OR
  2. Create an imagePullSecret in the cluster (see scripts notes / README).

Then restart the stuck pods:
  kubectl -n openthreatgrid rollout restart deploy/otg-api deploy/otg-worker deploy/cowrie
EOF
