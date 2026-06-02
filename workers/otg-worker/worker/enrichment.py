"""Lightweight, dependency-free enrichment for normalized events.

The MVP keeps enrichment self-contained: no external API calls, no MaxMind
database required. It classifies source IPs (private vs. public) and derives
behavioural tags from commands. GeoIP/ASN and AbuseIPDB scoring are deferred to
the post-MVP backlog (see the development plan) — the ``geo_*`` fields are left
for those integrations to populate.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Any

# Command substrings that indicate common botnet / malware-staging behaviour.
_BOTNET_PATTERNS = {
    "download": re.compile(r"\b(wget|curl|tftp|ftpget)\b", re.IGNORECASE),
    "execution": re.compile(r"\b(chmod\s+\+?x|\./|sh\s+-c|bash\s+-c)\b", re.IGNORECASE),
    "persistence": re.compile(
        r"\b(crontab|rc\.local|systemctl|\.ssh/authorized_keys)\b", re.IGNORECASE
    ),
    "recon": re.compile(r"\b(uname|whoami|cat\s+/proc|/etc/passwd|cpuinfo)\b", re.IGNORECASE),
    "miner": re.compile(r"\b(xmrig|minerd|stratum\+tcp)\b", re.IGNORECASE),
}


def _ip_tags(source_ip: str | None) -> list[str]:
    if not source_ip:
        return []
    try:
        ip = ipaddress.ip_address(source_ip)
    except ValueError:
        return ["invalid_ip"]
    tags = []
    if ip.is_private:
        tags.append("private_ip")
    if ip.is_loopback:
        tags.append("loopback")
    return tags


def _command_tags(command: str | None) -> list[str]:
    if not command:
        return []
    return [name for name, pattern in _BOTNET_PATTERNS.items() if pattern.search(command)]


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return ``event`` with additional tags derived from its contents.

    Mutates and returns the same dict for convenience. Tags are de-duplicated
    while preserving order.
    """
    tags = list(event.get("tags") or [])

    if event.get("protocol"):
        tags.append(event["protocol"])
    tags.extend(_ip_tags(event.get("source_ip")))

    cmd_tags = _command_tags(event.get("command"))
    tags.extend(cmd_tags)
    if cmd_tags:
        tags.append("botnet_indicator")

    if event.get("payload_url"):
        tags.append("payload")

    # De-duplicate, preserve order.
    seen: set[str] = set()
    event["tags"] = [t for t in tags if not (t in seen or seen.add(t))]
    return event
