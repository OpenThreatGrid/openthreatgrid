# Reports

Weekly threat-intelligence report generator. Renders a Markdown report (sections
1–10 of the development plan) from normalized OTG events.

## Usage

Against a running API:

```bash
pip install -r requirements.txt
python generate_report.py --api-url http://localhost:8000 --days 7 \
    --output output/weekly-$(date +%Y%m%d).md
```

Offline from a JSON file of events (useful for demos / CI examples):

```bash
python generate_report.py --from-file ../examples/sample-events/otg-events.json \
    --output output/example-report.md
```

## Files

- `generate_report.py` — CLI + aggregation logic.
- `templates/weekly_report.md.j2` — Jinja2 report template.
- `templates/weekly-report.md` — legacy flat template (kept for reference).
- `output/` — generated reports (git-ignored).

## In production

Runs as a weekly Kubernetes CronJob (`deploy/k8s/reports/cronjob.yaml`) that
calls the in-cluster API and writes the report to a PVC / object store.
