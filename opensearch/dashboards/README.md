# OpenSearch Dashboards saved objects

`otg-dashboards.ndjson` contains the OpenThreatGrid index pattern, core
visualizations, and the **Threat Overview** dashboard. Regenerate it after
editing [`build_saved_objects.py`](build_saved_objects.py):

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

> Open the dashboard at **Dashboards → OpenThreatGrid — Threat Overview**.
> The default time range is the last 7 days.
