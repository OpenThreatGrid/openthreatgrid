# Infrastructure

OpenThreatGrid runs across three Tailscale-meshed nodes for **$6/month**: a
cheap DigitalOcean VPS at the edge and an existing on-premise Kubernetes cluster
(one worker, one control-plane node) for compute and storage.

## Topology

```
                 Internet (attacker traffic)
                          │  2222 / 2223 / 443
                          ▼
   ┌─────────────────────────────────────────────┐
   │  DigitalOcean VPS  (1 vCPU · 1 GB · $6/mo)   │
   │  HAProxy  ──send-proxy-v2──►  Tailscale       │   ← edge, no data
   └───────────────────────┬─────────────────────┘
                           │ WireGuard (<30ms)
                           ▼
   ┌─────────────────────────────────────────────┐
   │  DC-A  K8s WORKER (32 CPU · 32 GB)            │
   │  Traefik (Proxy Protocol termination)        │
   │   └► Cowrie ─► parser ─► Redis ─► consumer    │
   │                                  └► API ─► OpenSearch ─► Dashboards / Reports
   └───────────────────────┬─────────────────────┘
                           │ WireGuard (<30ms)
                           ▼
   ┌─────────────────────────────────────────────┐
   │  DC-B  K8s MASTER (control plane only)        │
   │  kube-apiserver · etcd · scheduler            │
   │  Tainted NoSchedule — no workloads            │
   └─────────────────────────────────────────────┘
```

See [`architecture.md`](architecture.md) for the application data flow.

## Why an edge VPS?

The on-prem cluster shouldn't expose its IPs directly. The VPS is the only
internet-facing host. It runs **only** HAProxy + Tailscale — no compute, no data
— so if it is compromised it can be destroyed and rebuilt in minutes (see the
risk register in the development plan).

## Source IP preservation

Keeping the **real attacker IP** is the whole point of the honeynet, so it must
survive every hop:

```
Attacker 203.0.113.42
  └► HAProxy   mode tcp + send-proxy-v2   (PROXY TCP4 203.0.113.42 ...)
       └► Traefik  proxyProtocol.trustedIPs = <VPS Tailscale IP>   (terminates)
            └► Cowrie  sees source_ip = 203.0.113.42  ✅
```

`trustedIPs` must list **only** the VPS Tailscale IP, so no one else can spoof a
PROXY header. Verify the whole chain with
[`scripts/test_proxy_protocol.sh`](../scripts/test_proxy_protocol.sh).

## DNS & Cloudflare

| Record | Proxied | Target |
|---|---|---|
| `dashboard.openthreatgrid.io` | ✅ | DO VPS IP |
| `api.openthreatgrid.io` | ✅ | DO VPS IP |
| Honeypot (2222/2223) | ❌ | Raw DO VPS IP (no domain, no proxy) |

The honeypot must look like an ordinary VPS, so it uses the **raw IP** with no
Cloudflare in front. Only the dashboard and API hostnames are proxied.

## Tailscale mesh

- Three nodes: DO VPS ↔ DC-A worker ↔ DC-B master.
- WireGuard-encrypted, `< 30 ms` inter-node latency.
- Management SSH to the VPS is allowed **only** over `tailscale0`; the public
  firewall exposes just 2222/2223/443. See
  [`deploy/edge/setup-edge.sh`](../deploy/edge/setup-edge.sh).

## Resource budget

| Tier | Components | CPU req | RAM req |
|---|---|---|---|
| Edge VPS | HAProxy + Tailscale + OS | ~200m | ~328 MB (of 1 GB) |
| K8s worker | Traefik, Cowrie, API×2, OpenSearch, Dashboards, Redis, worker | ~3.5 cores | ~4.5 Gi (of 32) |

Plenty of headroom on the worker for additional sensors post-MVP.

## Hardening checklist

Implemented or documented across `deploy/`:

- VPS: UFW (only 2222/2223/443 public; SSH via Tailscale), key-only SSH,
  fail2ban, unattended-upgrades — see `deploy/edge/setup-edge.sh`.
- Cowrie: non-root, dropped capabilities, seccomp, and a NetworkPolicy that
  blocks **all** outbound internet — see `deploy/k8s/cowrie/networkpolicy.yaml`.
- OpenSearch runs internal-only with the security plugin disabled, guarded by
  NetworkPolicy (only the API and Dashboards reach `:9200`); enable the security
  plugin with TLS + credentials before any exposure.
- Master node tainted `NoSchedule`; schedule regular etcd backups (single
  master is a SPOF).
