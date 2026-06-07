# Kubernetes Manifests

Raw manifests for the OpenThreatGrid pipeline (topology A), namespace
`openthreatgrid`.

## Layout

```
k8s/
├── namespace.yaml
├── networkpolicy-global.yaml     # default-deny + DNS
├── traefik/                      # Helm values + IngressRouteTCP (Proxy Protocol)
├── opensearch/                   # StatefulSet + Service + NetworkPolicy
├── opensearch-dashboards/        # Deployment + Service + saved-objects import Job
├── filebeat/                     # shared Filebeat config (sensor sidecars)
├── logstash/                     # Logstash Deployment/Service/NetworkPolicy
├── cowrie/                       # honeypot + Filebeat sidecar + isolation policy
├── opencanary/ , http-trap/      # optional sensors (commented in kustomization)
├── reports/                      # weekly CronJob (reads OpenSearch)
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

# 3. Core app (OpenSearch, Dashboards, Logstash, Cowrie+Filebeat, reports)
kubectl apply -k .

# 4. Index template + dashboards (Logstash uses manage_template=false)
OPENSEARCH_URL=http://localhost:9200 ../../scripts/bootstrap_opensearch.sh
#    (or rely on the otg-dashboards-import Job for the saved objects)

# 5. IngressRoutes (after Traefik CRDs exist)
kubectl apply -f traefik/ingressroute-tcp.yaml
```

Optional extra sensors: uncomment the `opencanary/*` / `http-trap/*` entries in
`kustomization.yaml` (each needs its image on GHCR).

## Before production

- Set the real Tailscale IPs in `traefik/values.yaml` (`<TAILSCALE_IP_DO_VPS>`).
- Build & push images to `ghcr.io/openthreatgrid/*` (see `.github/workflows`).
- Enable OpenSearch security (TLS + auth) before any exposure; it runs
  internal-only with the plugin disabled by default.
- Enable etcd encryption-at-rest and a NodePort firewall that only admits the
  Tailscale subnet (hardening checklist in the development plan).

The NetworkPolicies implement the plan's matrix: sensors have **no outbound
internet** (only Logstash + DNS), OpenSearch only accepts Logstash/Dashboards/
reports, and everything else is default-deny.
