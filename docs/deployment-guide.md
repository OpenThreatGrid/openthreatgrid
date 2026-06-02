# Deployment Guide

Three ways to run OpenThreatGrid, smallest to largest:

1. [Local dev (docker-compose)](#1-local-development) — the full pipeline on one machine.
2. [Kubernetes (raw manifests)](#2-kubernetes-raw-manifests)
3. [Kubernetes (Helm)](#3-kubernetes-helm)

Plus the [production edge + cluster bring-up order](#4-production-bring-up).

---

## 1. Local development

Requires Docker + Docker Compose.

```bash
./scripts/run_local.sh
# or: docker compose up --build
```

This starts Postgres, Redis, the API, the worker (consumer), Cowrie, the parser
sidecar, and Grafana, then seeds sample data. Then:

- API docs: http://localhost:8000/docs
- Stats:    http://localhost:8000/api/v1/stats/summary
- Grafana:  http://localhost:3000 (admin / admin)
- Poke the honeypot: `ssh -p 2222 root@localhost`

Tear down: `docker compose down -v`.

### Run components without Docker

```bash
# API
cd backend/otg-api && pip install -r requirements-dev.txt && pytest
uvicorn app.main:app --reload

# Worker tests
cd workers/otg-worker && pip install -r requirements-dev.txt && pytest

# Example report from sample data
cd reports && pip install -r requirements.txt
python generate_report.py --from-file ../examples/sample-events/otg-events.json --output output/report.md
```

---

## 2. Kubernetes (raw manifests)

Namespace `openthreatgrid`. Full steps and apply order in
[`deploy/k8s/README.md`](../deploy/k8s/README.md). Short version:

```bash
kubectl apply -f deploy/k8s/namespace.yaml
helm upgrade --install traefik traefik/traefik -n openthreatgrid -f deploy/k8s/traefik/values.yaml
kubectl apply -k deploy/k8s
kubectl -n openthreatgrid create configmap grafana-dashboards \
  --from-file=openthreatgrid.json=dashboard/grafana/provisioning/dashboards/openthreatgrid.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/k8s/traefik/ingressroute-tcp.yaml
```

Build & push images first (or let `.github/workflows/docker-build.yml` do it):
`otg-api`, `otg-worker`, `otg-reports`, `cowrie` → `ghcr.io/openthreatgrid/*`.

---

## 3. Kubernetes (Helm)

```bash
helm install otg deploy/helm/openthreatgrid \
  --namespace openthreatgrid --create-namespace \
  --set postgres.auth.password=$(openssl rand -hex 16) \
  --set grafana.adminPassword=$(openssl rand -hex 16)
```

Toggle components with `--set <component>.enabled=false`. Values reference in
[`deploy/helm/openthreatgrid/values.yaml`](../deploy/helm/openthreatgrid/values.yaml).
Traefik + IngressRoutes are installed separately (step 2 above) so the chart
stays cluster-agnostic.

---

## 4. Production bring-up

Order (matches the development plan's deployment order):

```
 1. [DO VPS]  Provision droplet, install Tailscale
 2. [DC-A]    Install Tailscale on worker
 3. [DC-B]    Install Tailscale on master
 4. [ALL]     Verify tailscale ping < 30ms
 5. [DC-B]    Init K8s master, taint NoSchedule
 6. [DC-A]    Join worker via Tailscale IP
 7. [DC-A]    kubectl apply namespace
 8. [DC-A]    Helm install Traefik (TCP + Proxy Protocol)
 9. [DO VPS]  ./deploy/edge/setup-edge.sh   (HAProxy + UFW + hardening)
10. [DO VPS]  Verify edge → Traefik reachability
11. [DC-A]    Deploy Postgres, Redis, API, Cowrie+parser, worker
12. [DC-A]    Verify end-to-end: attacker IP visible in PostgreSQL events
13. [DC-A]    Deploy Grafana; apply IngressRoutes
14. [CF]      Configure Cloudflare DNS (dashboard + API only)
15. [ALL]     Apply NetworkPolicies; UFW lockdown; verify Cowrie has no egress
```

Verify source-IP preservation end-to-end:

```bash
EDGE_HOST=<droplet-public-ip> ./scripts/test_proxy_protocol.sh
```

### Pre-flight security

- Replace every `change-me-*` secret.
- Set real Tailscale IPs in `deploy/k8s/traefik/values.yaml` and
  `deploy/edge/haproxy.cfg` (the edge script substitutes the worker IP for you).
- Confirm `kubectl -n openthreatgrid get networkpolicy` shows `cowrie-isolation`
  and `default-deny-all`.
- Confirm Cowrie cannot reach the internet (exec into the pod and try `curl` — it
  should fail).
