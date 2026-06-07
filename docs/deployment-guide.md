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

This starts OpenSearch + Dashboards, installs the index template, imports the
Threat Overview dashboard, seeds sample data, then starts Logstash, Cowrie, and
its Filebeat sidecar (Cowrie → Filebeat → Logstash → OpenSearch). Then:

- Dashboards: http://localhost:5601 (Threat Overview)
- OpenSearch: http://localhost:9200
- Poke the honeypot: `ssh -p 2222 root@localhost`

Tear down: `docker compose down -v`.

### Run components without Docker

```bash
# Reports (tests + example render)
cd reports && pip install -r requirements-dev.txt && pytest
python generate_report.py --from-file ../examples/sample-events/otg-events.json --output output/report.md

# HTTP-trap sensor (tests)
cd sensors/http-trap && pip install -r requirements-dev.txt && pytest

# Validate the Logstash pipeline
docker run --rm ghcr.io/openthreatgrid/otg-logstash:main \
  logstash -t -f /usr/share/logstash/pipeline/otg.conf
```

---

## 2. Kubernetes (raw manifests)

Namespace `openthreatgrid`. Full steps and apply order in
[`deploy/k8s/README.md`](../deploy/k8s/README.md). Short version:

```bash
kubectl apply -f deploy/k8s/namespace.yaml
helm upgrade --install traefik traefik/traefik -n openthreatgrid -f deploy/k8s/traefik/values.yaml
kubectl apply -k deploy/k8s   # includes OpenSearch, Dashboards, and the saved-objects import Job
kubectl apply -f deploy/k8s/traefik/ingressroute-tcp.yaml
```

Run `./scripts/bootstrap_opensearch.sh` once to install the `otg-events` index
template (Logstash uses `manage_template => false`) and import the dashboards;
the `otg-dashboards-import` Job also loads them once Dashboards is ready.
Regenerate saved objects after editing with
`python opensearch/dashboards/build_saved_objects.py`.

Build & push images first (or let `.github/workflows/docker-build.yml` do it):
`otg-logstash`, `otg-reports`, `cowrie`, `mmproxy`, `opencanary`, `http-trap`
→ `ghcr.io/openthreatgrid/*`.

---

## 3. Kubernetes (Helm)

```bash
helm install otg deploy/helm/openthreatgrid \
  --namespace openthreatgrid --create-namespace
```

The chart ships OpenSearch (security plugin disabled, internal-only) and
OpenSearch Dashboards, and runs a `post-install`/`post-upgrade` hook that imports
the Threat Overview dashboard.

Toggle components with `--set <component>.enabled=false`. Values reference in
[`deploy/helm/openthreatgrid/values.yaml`](../deploy/helm/openthreatgrid/values.yaml).
Traefik + IngressRoutes are installed separately (step 2 above) so the chart
stays cluster-agnostic. Optional extra sensors: `--set opencanary.enabled=true`,
`--set httpTrap.enabled=true`.

---

## Updates & automatic rollouts

Images are built and pushed by [`docker-build.yml`](../.github/workflows/docker-build.yml)
on every push to `main`, with both a mutable `:main` tag and an **immutable
`sha-<commit>` tag**.

A mutable tag is a deploy trap: rebuilding `:main` does **not** change the
Deployment spec, so Fleet/Helm never roll the pods (`imagePullPolicy: Always`
only pulls when a pod is *created*). To get automatic rollouts, the `pin-deploy-tag`
CI job pins `fleet.yaml`'s `image.tag` to the new `sha-<commit>` after the build
and commits it (`[skip ci]`; the `GITHUB_TOKEN` push doesn't re-trigger CI). Fleet
then sees a changed spec and rolls **every** component.

Pin or revert manually with:

```bash
./scripts/bump_image_tag.sh sha-1a2b3c4   # pin to a specific build
./scripts/bump_image_tag.sh main          # back to the mutable tag
```

Force an immediate rollout of one component without a new image:

```bash
kubectl -n openthreatgrid rollout restart deploy/logstash
```

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
11. [DC-A]    Deploy OpenSearch, Logstash, Cowrie (+ Filebeat sidecar)
12. [DC-A]    Verify end-to-end: attacker IP visible in otg-events-* (_search)
13. [DC-A]    Deploy OpenSearch Dashboards; apply IngressRoutes
14. [CF]      Configure Cloudflare DNS (dashboard only)
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
