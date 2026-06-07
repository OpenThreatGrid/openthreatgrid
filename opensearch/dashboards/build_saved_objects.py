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


def _search_source(query: str = "") -> str:
    return json.dumps(
        {
            "query": {"query": query, "language": "kuery"},
            "filter": [],
            "indexRefName": INDEX_REF,
        }
    )


def visualization(vid: str, title: str, vis_state: dict, query: str = "") -> dict:
    return {
        "id": vid,
        "type": "visualization",
        "attributes": {
            "title": title,
            "visState": json.dumps({**vis_state, "title": title}),
            "uiStateJSON": "{}",
            "description": "",
            "version": 1,
            "kibanaSavedObjectMeta": {"searchSourceJSON": _search_source(query)},
        },
        "references": [
            {"name": INDEX_REF, "type": "index-pattern", "id": INDEX_PATTERN_ID}
        ],
    }


# ─── visState builders ──────────────────────────────────────────────────

def metric(field: str | None = None, agg: str = "count") -> dict:
    params = {"field": field} if field else {}
    return {
        "type": "metric",
        "aggs": [{"id": "1", "enabled": True, "type": agg, "schema": "metric", "params": params}],
        "params": {"metric": {"percentageMode": False}},
    }


def _terms_bucket(agg_id: str, field: str, size: int) -> dict:
    return {
        "id": agg_id,
        "enabled": True,
        "type": "terms",
        "schema": "bucket",
        "params": {"field": field, "size": size, "order": "desc", "orderBy": "1"},
    }


def terms_table(field: str, size: int = 10) -> dict:
    return {
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            _terms_bucket("2", field, size),
        ],
        "params": {"perPage": 10, "showTotal": True},
    }


def terms_table_multi(fields: list[str], size: int = 10) -> dict:
    """Data table split by several term buckets (e.g. username × password pairs)."""
    aggs = [{"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}]
    aggs += [_terms_bucket(str(i), f, size) for i, f in enumerate(fields, start=2)]
    return {"type": "table", "aggs": aggs, "params": {"perPage": 10, "showTotal": True}}


def terms_table_metric(bucket_field: str, metric_field: str, agg: str = "cardinality",
                       size: int = 10) -> dict:
    """Data table: one term bucket with a non-count metric (e.g. unique users per IP)."""
    return {
        "type": "table",
        "aggs": [
            {"id": "1", "enabled": True, "type": agg, "schema": "metric",
             "params": {"field": metric_field}},
            _terms_bucket("2", bucket_field, size),
        ],
        "params": {"perPage": 10, "showTotal": False},
    }


def terms_pie(field: str, size: int = 10) -> dict:
    return {
        "type": "pie",
        "aggs": [
            {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}},
            {**_terms_bucket("2", field, size), "schema": "segment"},
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


# ─── Visualization registry ─────────────────────────────────────────────
# id -> (title, visState, query). A visualization may be referenced by more
# than one dashboard; it is emitted once.
def V(vid: str, title: str, state: dict, query: str = "") -> dict:
    return {"id": vid, "title": title, "state": state, "query": query}


# Suspicious-command query reused by hunting panels.
BOTNET_KQL = 'tags:("download" or "execution" or "persistence" or "miner" or "recon")'

# ─── Dashboards (plan §10) ──────────────────────────────────────────────
# Each panel is (viz, (w, h, x, y)) on the 48-column OSD grid.
DASHBOARDS = [
    {
        "id": "otg-threat-overview",
        "title": "OpenThreatGrid — Threat Overview",
        "description": "High-level honeypot attack visibility.",
        "panels": [
            (V("otg-total-events", "Total Events", metric()), (12, 8, 0, 0)),
            (V("otg-unique-ips", "Unique Source IPs", metric("source_ip", "cardinality")), (12, 8, 12, 0)),
            (V("otg-unique-sensors", "Active Sensors", metric("sensor_id", "cardinality")), (12, 8, 24, 0)),
            (V("otg-payload-count", "Payload Attempts", metric(), 'event_type:"file_download"'), (12, 8, 36, 0)),
            (V("otg-events-over-time", "Events Over Time", events_over_time()), (48, 12, 0, 8)),
            (V("otg-event-types", "Event Action Distribution", terms_pie("event_type")), (16, 14, 0, 20)),
            (V("otg-top-source-ips", "Top Source IPs", terms_table("source_ip")), (16, 14, 16, 20)),
            (V("otg-top-countries", "Top Countries", terms_table("geo_country")), (16, 14, 32, 20)),
            (V("otg-top-usernames", "Top Usernames", terms_table("username")), (16, 14, 0, 34)),
            (V("otg-top-passwords", "Top Passwords", terms_table("password")), (16, 14, 16, 34)),
            (V("otg-top-commands", "Top Commands", terms_table("command")), (16, 14, 32, 34)),
        ],
    },
    {
        "id": "otg-cowrie-activity",
        "title": "OpenThreatGrid — Cowrie SSH/Telnet Activity",
        "description": "SSH/Telnet honeypot activity from the Cowrie sensor.",
        "panels": [
            (V("otg-ssh-over-time", "SSH Attempts Over Time", events_over_time(), 'protocol:"ssh"'), (24, 12, 0, 0)),
            (V("otg-telnet-over-time", "Telnet Attempts Over Time", events_over_time(), 'protocol:"telnet"'), (24, 12, 24, 0)),
            (V("otg-top-usernames", "Top Usernames", terms_table("username")), (16, 14, 0, 12)),
            (V("otg-top-passwords", "Top Passwords", terms_table("password")), (16, 14, 16, 12)),
            (V("otg-cred-pairs", "Top Username / Password Pairs", terms_table_multi(["username", "password"])), (16, 14, 32, 12)),
            (V("otg-top-commands", "Top Commands", terms_table("command")), (24, 14, 0, 26)),
            (V("otg-top-payload-urls", "Payload Download URLs", terms_table("payload_url")), (24, 14, 24, 26)),
            (V("otg-event-types", "Event Action Distribution", terms_pie("event_type")), (24, 14, 0, 40)),
        ],
    },
    {
        "id": "otg-credential-abuse",
        "title": "OpenThreatGrid — Credential Abuse",
        "description": "Brute force and credential-spraying behaviour.",
        "panels": [
            (V("otg-login-attempts", "Login Attempts", metric(), 'event_type:"login_attempt"'), (12, 8, 0, 0)),
            (V("otg-root-logins", "Root Login Attempts", metric(), 'username:"root"'), (12, 8, 12, 0)),
            (V("otg-admin-logins", "Admin Login Attempts", metric(), 'username:"admin"'), (12, 8, 24, 0)),
            (V("otg-unique-passwords", "Unique Passwords", metric("password", "cardinality")), (12, 8, 36, 0)),
            (V("otg-cred-over-time", "Credential Attempts Over Time", events_over_time(), 'event_type:"login_attempt"'), (48, 12, 0, 8)),
            (V("otg-top-usernames", "Top Usernames", terms_table("username")), (16, 14, 0, 20)),
            (V("otg-top-passwords", "Top Passwords", terms_table("password")), (16, 14, 16, 20)),
            (V("otg-cred-pairs", "Top Username / Password Pairs", terms_table_multi(["username", "password"])), (16, 14, 32, 20)),
            (V("otg-uniq-user-per-ip", "Unique Usernames per Source IP", terms_table_metric("source_ip", "username")), (24, 14, 0, 34)),
            (V("otg-uniq-pass-per-ip", "Unique Passwords per Source IP", terms_table_metric("source_ip", "password")), (24, 14, 24, 34)),
        ],
    },
    {
        "id": "otg-threat-hunting",
        "title": "OpenThreatGrid — Threat Hunting",
        "description": "Investigate suspicious activity, payloads, and botnet indicators.",
        "panels": [
            (V("otg-suspicious-count", "Suspicious Events", metric(), BOTNET_KQL), (16, 8, 0, 0)),
            (V("otg-payload-count", "Payload Attempts", metric(), 'event_type:"file_download"'), (16, 8, 16, 0)),
            (V("otg-top-source-ips", "High-Activity Source IPs", terms_table("source_ip")), (16, 14, 32, 0)),
            (V("otg-botnet-over-time", "Botnet-Tagged Events Over Time", events_over_time(), 'tags:"botnet_indicator"'), (32, 12, 0, 8)),
            (V("otg-suspicious-commands", "Suspicious Commands", terms_table("command"), BOTNET_KQL), (24, 14, 0, 20)),
            (V("otg-tag-distribution", "OTG Tag Distribution", terms_table("tags")), (24, 14, 24, 20)),
            (V("otg-top-payload-urls", "Payload Download URLs", terms_table("payload_url")), (24, 14, 0, 34)),
            (V("otg-payload-by-ip", "Payload Attempts by Source IP", terms_table("source_ip"), 'event_type:"file_download"'), (24, 14, 24, 34)),
        ],
    },
    {
        "id": "otg-malware-payload",
        "title": "OpenThreatGrid — Malware & Payload",
        "description": "Payload download attempts and suspected malware staging.",
        "panels": [
            (V("otg-payload-over-time", "Payload Attempts Over Time", events_over_time(), 'event_type:"file_download"'), (48, 12, 0, 0)),
            (V("otg-top-payload-urls", "Top Payload URLs", terms_table("payload_url")), (24, 14, 0, 12)),
            (V("otg-payload-by-ip", "Payload Attempts by Source IP", terms_table("source_ip"), 'event_type:"file_download"'), (24, 14, 24, 12)),
            (V("otg-payload-by-sensor", "Payload Attempts by Sensor", terms_table("sensor_id"), 'event_type:"file_download"'), (24, 14, 0, 26)),
            (V("otg-download-commands", "Top Download Commands", terms_table("command"), 'tags:"download"'), (24, 14, 24, 26)),
            (V("otg-botnet-tags", "Suspected Botnet Tags", terms_pie("tags"), BOTNET_KQL), (24, 14, 0, 40)),
            (V("otg-tag-distribution", "OTG Tag Distribution", terms_table("tags")), (24, 14, 24, 40)),
        ],
    },
    {
        "id": "otg-source-ip-intel",
        "title": "OpenThreatGrid — Source IP Intelligence",
        "description": "Profile attacker infrastructure by source IP, country, and ASN.",
        "panels": [
            (V("otg-top-source-ips", "Top Source IPs", terms_table("source_ip")), (24, 14, 0, 0)),
            (V("otg-events-over-time", "Source IP Activity Timeline", events_over_time()), (24, 14, 24, 0)),
            (V("otg-top-countries", "Source IPs by Country", terms_table("geo_country")), (16, 14, 0, 14)),
            (V("otg-source-asn", "Source IPs by ASN", terms_table("geo_asn")), (16, 14, 16, 14)),
            (V("otg-uniq-user-per-ip", "Usernames Tried per Source IP", terms_table_metric("source_ip", "username")), (16, 14, 32, 14)),
            (V("otg-payload-by-ip", "Payload Attempts by Source IP", terms_table("source_ip"), 'event_type:"file_download"'), (24, 14, 0, 28)),
            (V("otg-uniq-pass-per-ip", "Passwords Tried per Source IP", terms_table_metric("source_ip", "password")), (24, 14, 24, 28)),
        ],
    },
    {
        "id": "otg-sensor-health",
        "title": "OpenThreatGrid — Sensor Health",
        "description": "Sensor coverage and ingestion health (event-derived).",
        "panels": [
            (V("otg-unique-sensors", "Active Sensors", metric("sensor_id", "cardinality")), (16, 8, 0, 0)),
            (V("otg-total-events", "Total Events", metric()), (16, 8, 16, 0)),
            (V("otg-sensor-types", "Sensor Types", terms_pie("sensor_type")), (16, 8, 32, 0)),
            (V("otg-events-by-sensor", "Events by Sensor", terms_table("sensor_id")), (24, 14, 0, 8)),
            (V("otg-last-event-per-sensor", "Last Event per Sensor", terms_table_metric("sensor_id", "timestamp", agg="max")), (24, 14, 24, 8)),
            (V("otg-events-over-time", "Ingestion Rate", events_over_time()), (48, 12, 0, 22)),
        ],
    },
    {
        "id": "otg-executive-summary",
        "title": "OpenThreatGrid — Executive Summary",
        "description": "Non-technical overview for README, landing page, and portfolio.",
        "panels": [
            (V("otg-total-events", "Total Attacks Observed", metric()), (12, 8, 0, 0)),
            (V("otg-unique-ips", "Unique Attacking IPs", metric("source_ip", "cardinality")), (12, 8, 12, 0)),
            (V("otg-payload-count", "Payload Attempts", metric(), 'event_type:"file_download"'), (12, 8, 24, 0)),
            (V("otg-most-active-sensor", "Most Active Sensors", terms_table("sensor_id", size=5)), (12, 8, 36, 0)),
            (V("otg-events-over-time", "Weekly Trend", events_over_time()), (48, 12, 0, 8)),
            (V("otg-top5-countries", "Top 5 Countries", terms_table("geo_country", size=5)), (12, 14, 0, 20)),
            (V("otg-top5-usernames", "Top 5 Usernames", terms_table("username", size=5)), (12, 14, 12, 20)),
            (V("otg-top5-passwords", "Top 5 Passwords", terms_table("password", size=5)), (12, 14, 24, 20)),
            (V("otg-top5-commands", "Top 5 Commands", terms_table("command", size=5)), (12, 14, 36, 20)),
        ],
    },
]


def dashboard_object(did: str, title: str, description: str,
                     panels: list[dict], references: list[dict]) -> dict:
    return {
        "id": did,
        "type": "dashboard",
        "attributes": {
            "title": title,
            "description": description,
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

    visuals: dict[str, dict] = {}  # id -> saved object (deduped across dashboards)
    dashboards: list[dict] = []
    for dash in DASHBOARDS:
        panels, references = [], []
        for i, (v, (w, h, x, y)) in enumerate(dash["panels"], start=1):
            vid = v["id"]
            if vid not in visuals:
                visuals[vid] = visualization(vid, v["title"], v["state"], v["query"])
            panel_ref = f"panel_{i}"
            panels.append({
                "version": "2.11.0",
                "type": "visualization",
                "gridData": {"w": w, "h": h, "x": x, "y": y, "i": str(i)},
                "panelIndex": str(i),
                "embeddableConfig": {},
                "panelRefName": panel_ref,
            })
            references.append({"name": panel_ref, "type": "visualization", "id": vid})
        dashboards.append(dashboard_object(dash["id"], dash["title"], dash["description"], panels, references))

    return [index_pattern, *visuals.values(), *dashboards]


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
