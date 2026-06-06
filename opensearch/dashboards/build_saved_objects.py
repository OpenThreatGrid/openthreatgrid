#!/usr/bin/env python3
"""Generate the OpenSearch Dashboards saved-objects NDJSON for OpenThreatGrid.

Hand-escaping the nested JSON strings OSD uses (``visState``,
``searchSourceJSON``, ``panelsJSON``) is error-prone, so we build the objects as
Python dicts and serialise them here. Run after changing a visualization:

    python opensearch/dashboards/build_saved_objects.py

Then import the result in Dashboards → Stack Management → Saved Objects → Import,
or via the API (see opensearch/dashboards/README.md).
"""

from __future__ import annotations

import json
from pathlib import Path

INDEX_PATTERN_ID = "otg-events"
INDEX_REF = "kibanaSavedObjectMeta.searchSourceJSON.index"
OUT = Path(__file__).parent / "otg-dashboards.ndjson"
# Also emit a k8s ConfigMap so kustomize can mount the objects without reaching
# outside its root (kustomize forbids ../ file sources by default).
REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGMAP_OUT = REPO_ROOT / "deploy" / "k8s" / "opensearch-dashboards" / "dashboards-configmap.yaml"
# Helm cannot read files outside its chart dir, so keep a copy the chart can
# .Files.Get for the dashboards-import hook.
HELM_FILES_OUT = REPO_ROOT / "deploy" / "helm" / "openthreatgrid" / "files" / "otg-dashboards.ndjson"


def _search_source() -> str:
    return json.dumps(
        {
            "query": {"query": "", "language": "kuery"},
            "filter": [],
            "indexRefName": INDEX_REF,
        }
    )


def visualization(vid: str, title: str, vis_state: dict) -> dict:
    return {
        "id": vid,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps({**vis_state, "title": title}),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {"searchSourceJSON": _search_source()},
        },
        "references": [
            {"name": INDEX_REF, "type": "index-pattern", "id": INDEX_PATTERN_ID}
        ],
    }


def metric(field: str | None = None, agg: str = "count") -> dict:
    params = {"field": field} if field else {}
    return {
        "type": "metric",
        "aggs": [{"id": "1", "enabled": True, "type": agg, "schema": "metric", "params": params}],
        "params": {"metric": {"percentageMode": False}},
    }


def terms_table(field: str) -> dict:
    return {
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "bucket",
                "params": {"field": field, "size": 10, "order": "desc", "orderBy": "1"},
            },
        ],
        "params": {"perPage": 10, "showTotal": True},
    }


def terms_pie(field: str) -> dict:
    return {
        "type": "pie",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {
                "id": "2",
                "enabled": True,
                "type": "terms",
                "schema": "segment",
                "params": {"field": field, "size": 10, "order": "desc", "orderBy": "1"},
            },
        ],
        "params": {"isDonut": True, "addLegend": True},
    }


def events_over_time() -> dict:
    return {
        "type": "histogram",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {
                "id": "2",
                "enabled": True,
                "type": "date_histogram",
                "schema": "segment",
                "params": {"field": "timestamp", "interval": "auto"},
            },
        ],
        "params": {"addLegend": False, "addTimeMarker": False},
    }


# (id, title, visState, grid position w/h/x/y)
VISUALS = [
    ("otg-total-events", "Total Events", metric(), (12, 8, 0, 0)),
    ("otg-unique-ips", "Unique Source IPs", metric("source_ip", "cardinality"), (12, 8, 12, 0)),
    ("otg-unique-sensors", "Active Sensors", metric("sensor_id", "cardinality"), (12, 8, 24, 0)),
    ("otg-events-over-time", "Events Over Time", events_over_time(), (48, 12, 0, 8)),
    ("otg-event-types", "Event Action Distribution", terms_pie("event_type"), (16, 14, 0, 20)),
    ("otg-top-source-ips", "Top Source IPs", terms_table("source_ip"), (16, 14, 16, 20)),
    ("otg-top-countries", "Top Countries", terms_table("geo_country"), (16, 14, 32, 20)),
    ("otg-top-usernames", "Top Usernames", terms_table("username"), (16, 14, 0, 34)),
    ("otg-top-passwords", "Top Passwords", terms_table("password"), (16, 14, 16, 34)),
    ("otg-top-commands", "Top Commands", terms_table("command"), (16, 14, 32, 34)),
]


def build_dashboard() -> dict:
    panels = []
    references = []
    for i, (vid, _title, _vs, (w, h, x, y)) in enumerate(VISUALS, start=1):
        panel_ref = f"panel_{i}"
        panels.append(
            {
                "version": "2.11.0",
                "type": "visualization",
                "gridData": {"w": w, "h": h, "x": x, "y": y, "i": str(i)},
                "panelIndex": str(i),
                "embeddableConfig": {},
                "panelRefName": panel_ref,
            }
        )
        references.append({"name": panel_ref, "type": "visualization", "id": vid})

    return {
        "id": "otg-threat-overview",
        "type": "dashboard",
        "attributes": {
            "title": "OpenThreatGrid — Threat Overview",
            "description": "High-level honeypot attack visibility.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
            "version": 1,
            "timeRestore": True,
            "timeTo": "now",
            "timeFrom": "now-7d",
            "refreshInterval": {"pause": True, "value": 0},
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({"query": {"query": "", "language": "kuery"}, "filter": []})
            },
        },
        "references": references,
    }


def build() -> list[dict]:
    index_pattern = {
        "id": INDEX_PATTERN_ID,
        "type": "index-pattern",
        "attributes": {"title": "otg-events-*", "timeFieldName": "timestamp"},
        "references": [],
    }
    objects = [index_pattern]
    objects += [visualization(vid, title, vs) for vid, title, vs, _ in VISUALS]
    objects.append(build_dashboard())
    return objects


def write_configmap(ndjson: str) -> None:
    """Wrap the NDJSON in a k8s ConfigMap manifest (block scalar)."""
    indented = "\n".join("    " + line for line in ndjson.splitlines())
    manifest = (
        "# GENERATED by opensearch/dashboards/build_saved_objects.py — do not edit.\n"
        "# Mounted by the otg-dashboards-import Job (bootstrap-job.yaml).\n"
        "apiVersion: v1\n"
        "kind: ConfigMap\n"
        "metadata:\n"
        "  name: otg-dashboards\n"
        "  namespace: openthreatgrid\n"
        "data:\n"
        "  otg-dashboards.ndjson: |\n"
        f"{indented}\n"
    )
    CONFIGMAP_OUT.write_text(manifest)


def main() -> None:
    objects = build()
    lines = [json.dumps(obj) for obj in objects]
    lines.append(json.dumps({"exportedCount": len(objects), "missingRefObjects": [], "excludedObjects": []}))
    ndjson = "\n".join(lines) + "\n"
    OUT.write_text(ndjson)
    write_configmap(ndjson)
    HELM_FILES_OUT.parent.mkdir(parents=True, exist_ok=True)
    HELM_FILES_OUT.write_text(ndjson)
    print(f"Wrote {OUT} ({len(objects)} saved objects)")
    print(f"Wrote {CONFIGMAP_OUT}")
    print(f"Wrote {HELM_FILES_OUT}")


if __name__ == "__main__":
    main()
