# OpenSearch Dashboards saved objects

`otg-dashboards.ndjson` contains the OpenThreatGrid index pattern, the shared
visualizations, and the eight dashboards from plan §10:

- **Threat Overview** — high-level attack visibility.
- **Cowrie SSH/Telnet Activity** — SSH/Telnet attempts, credentials, commands, payloads.
- **Credential Abuse** — brute force / spraying, root & admin attempts, unique creds per IP.
- **Threat Hunting** — suspicious commands, botnet-tagged events, payload attempts, tag distribution.
- **Malware & Payload** — payload attempts over time, top URLs, by IP/sensor, download commands.
- **Source IP Intelligence** — top IPs, country/ASN breakdown, creds & payloads per IP.
- **Sensor Health** — active sensors, events & last-event per sensor, ingestion rate.
- **Executive Summary** — totals and top-5 countries/usernames/passwords/commands, weekly trend.

Regenerate after editing [`build_saved_objects.py`](build_saved_objects.py):

```bash
python opensearch/dashboards/build_saved_objects.py
```

## Import

**UI:** Dashboards → Management → Saved Objects → *Import* → choose
`otg-dashboards.ndjson` → *Import* (overwrite on conflict).

**API:**

```bash
curl -sk -u "$OSD_USER:$OSD_PASS" \
  -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "osd-xsrf: true" \
  --form file=@opensearch/dashboards/otg-dashboards.ndjson
```

Or run [`scripts/bootstrap_opensearch.sh`](../../scripts/bootstrap_opensearch.sh),
which also installs the index template.

> Open them under **Dashboards → "OpenThreatGrid — …"**. Each defaults to the
> last 7 days. Some panels are scoped with a KQL query (e.g. SSH/Telnet split by
> `protocol`, payloads by `event_type:"file_download"`, hunting by botnet tags).
