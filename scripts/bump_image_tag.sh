#!/usr/bin/env bash
# Pin the deploy image tag in fleet.yaml so Fleet rolls out a specific build.
#
# Mutable tags (:main) don't change the Deployment spec on rebuild, so Fleet
# never rolls the pods. Pinning an immutable per-commit tag (sha-<short>, pushed
# by docker-build.yml) makes every push produce a new spec → automatic rollout.
#
#   ./scripts/bump_image_tag.sh sha-1a2b3c4     # pin to a build
#   ./scripts/bump_image_tag.sh main            # back to the mutable tag
set -euo pipefail

TAG="${1:?usage: bump_image_tag.sh <image-tag>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="${FLEET_FILE:-$ROOT/fleet.yaml}"

# fleet.yaml carries a single image.tag key; refuse to guess if that changes.
count="$(grep -cE '^[[:space:]]*tag:[[:space:]]' "$FILE" || true)"
if [ "$count" -ne 1 ]; then
  echo "Expected exactly one 'tag:' key in $FILE, found $count" >&2
  exit 1
fi

# -i.bak keeps this portable across GNU and BSD/macOS sed.
sed -i.bak -E "s|^([[:space:]]*)tag:[[:space:]].*|\1tag: ${TAG}|" "$FILE"
rm -f "$FILE.bak"
echo "Pinned image.tag to '${TAG}' in $(basename "$FILE")"
