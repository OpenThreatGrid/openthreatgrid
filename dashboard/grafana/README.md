# Grafana

Provisioned Grafana for OpenThreatGrid. Everything is config-as-code — no manual
clicking required.

```
provisioning/
├── datasources/postgres.yml      # OpenThreatGrid Postgres (read-only)
└── dashboards/
    ├── dashboards.yml            # file provider
    └── openthreatgrid.json       # 10-panel dashboard (plan §11)
```

## Local (docker-compose)

Mounted automatically; open http://localhost:3000 (admin / admin).

## Kubernetes

The same files are shipped as ConfigMaps — see
`deploy/k8s/grafana/`. The datasource uses the read-only `grafana_ro` role
created by `deploy/k8s/postgres/configmap.yaml`.

## Panels

Total Events · Unique Source IPs · Event Distribution · Attack Timeline ·
Sensor Activity · Top Source IPs · Top Usernames · Top Passwords · Top Commands ·
Botnet Commands (wget/curl) · File Downloads.

The datasource is selected via the `DS` dashboard variable, so the dashboard
binds to whatever Postgres datasource is provisioned.
