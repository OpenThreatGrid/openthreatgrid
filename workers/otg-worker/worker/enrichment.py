"""Enrichment for normalized events.

Tagging is self-contained (no external calls): it classifies source IPs
(private vs. public) and derives behavioural tags from commands. GeoIP/ASN
enrichment is optional — pass a :class:`worker.geoip.GeoIP` resolver to populate
``geo_country``/``geo_asn`` when MaxMind GeoLite2 databases are available; when
absent, those fields stay null and only tagging runs.
"""

from __future__ import annotations

import ipaddress
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from worker.geoip import GeoIP

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


def enrich_event(event: dict[str, Any], geoip: GeoIP | None = None) -> dict[str, Any]:
    """Return ``event`` with additional tags and optional geo fields.

    Mutates and returns the same dict for convenience. Tags are de-duplicated
    while preserving order. When ``geoip`` is supplied and resolves the source
    IP, ``geo_country``/``geo_asn`` are populated and the country is added as a
    tag.
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

    if geoip is not None:
        country, asn = geoip.lookup(event.get("source_ip"))
        if country:
            event["geo_country"] = country
            tags.append(country)
        if asn:
            event["geo_asn"] = asn

    # De-duplicate, preserve order.
    seen: set[str] = set()
    event["tags"] = [t for t in tags if not (t in seen or seen.add(t))]
    return event
