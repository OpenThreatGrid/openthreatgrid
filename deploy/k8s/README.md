# Kubernetes Manifests

Raw manifests for the OpenThreatGrid pipeline, namespace `openthreatgrid`.

## Layout

```
k8s/
├── namespace.yaml
├── networkpolicy-global.yaml     # default-deny + DNS
├── traefik/                      # Helm values + IngressRouteTCP (Proxy Protocol)
├── postgres/                     # StatefulSet + PVC + init schema + secret
├── redis/                        # queue
├── api/                          # otg-api (2 replicas)
├── worker/                       # consumer
├── cowrie/                       # honeypot + parser sidecar + isolation policy
├── grafana/                      # provisioned dashboard
├── reports/                      # weekly CronJob
└── kustomization.yaml
```

## Apply order

```bash
# 1. Namespace
kubectl apply -f namespace.yaml

# 2. Traefik (Helm) with TCP entrypoints + Proxy Protocol
helm repo add traefik https://traefik.github.io/charts && helm repo update
helm upgrade --install traefik traefik/traefik \
    -n openthreatgrid -f traefik/values.yaml

# 3. Core app (everything except the IngressRoutes)
kubectl apply -k .

# 4. Grafana dashboard JSON (kept out of the YAML; generated from source)
kubectl -n openthreatgrid create configmap grafana-dashboards \
    --from-file=openthreatgrid.json=../../dashboard/grafana/provisioning/dashboards/openthreatgrid.json \
    --dry-run=client -o yaml | kubectl apply -f -
kubectl -n openthreatgrid rollout restart deploy/grafana

# 5. IngressRoutes (after Traefik CRDs exist)
kubectl apply -f traefik/ingressroute-tcp.yaml
```

## Before production

- Replace every `change-me-*` secret value (`postgres/secret.yaml`,
  `grafana/deployment.yaml`, `postgres/configmap.yaml` grafana_ro password).
- Set the real Tailscale IPs in `traefik/values.yaml`
  (`<TAILSCALE_IP_DO_VPS>`).
- Build & push images to `ghcr.io/openthreatgrid/*` (see `.github/workflows`).
- Enable etcd encryption-at-rest and a NodePort firewall that only admits the
  Tailscale subnet (hardening checklist in the development plan).

The NetworkPolicies implement the plan's matrix: Cowrie has **no outbound
internet** (only Redis + DNS), Postgres only accepts API/Grafana, and everything
else is default-deny.
