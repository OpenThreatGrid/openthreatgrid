#!/usr/bin/env bash
# Sync the canonical Logstash pipeline into the places that mount it as a
# ConfigMap, so pipeline fixes ship via git + rollout (NO image rebuild):
#   - Helm chart files/  (consumed by .Files.Get in the chart)
#   - deploy/k8s/logstash/ (consumed by kustomize configMapGenerator)
#
# Run after editing deploy/filebeat-logstash/logstash/pipeline/otg.conf.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/deploy/filebeat-logstash/logstash/pipeline/otg.conf"

HELM_DST="$ROOT/deploy/helm/openthreatgrid/files/otg.conf"
K8S_DST="$ROOT/deploy/k8s/logstash/otg.conf"

cp "$SRC" "$HELM_DST"
cp "$SRC" "$K8S_DST"
echo "Synced otg.conf -> $(realpath --relative-to="$ROOT" "$HELM_DST" 2>/dev/null || echo "$HELM_DST")"
echo "Synced otg.conf -> $(realpath --relative-to="$ROOT" "$K8S_DST" 2>/dev/null || echo "$K8S_DST")"
