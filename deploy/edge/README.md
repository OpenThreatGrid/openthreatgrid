# Edge Proxy (DigitalOcean VPS)

The edge is a $6/month DigitalOcean droplet (1 vCPU / 1 GB) that is the only
internet-facing component. It runs **HAProxy** (raw TCP) and **Tailscale**.

It does **no compute and stores no data** — it forwards honeypot traffic across
the Tailscale tunnel to the K8s worker, sending PROXY PROTOCOL v2 so the real
attacker source IP survives to Cowrie.

```
Internet ──2222/2223/443──► HAProxy ──send-proxy-v2──► Tailscale ──► Traefik NodePorts
```

## Files

- `haproxy.cfg` — TCP frontends + PROXY-v2 backends. Replace
  `<TAILSCALE_IP_WORKER>` (the setup script does this for you).
- `setup-edge.sh` — installs Tailscale + HAProxy, deploys the config, and
  applies the UFW lockdown + SSH hardening from the plan's hardening checklist.

## Quick start

```bash
# On the droplet (Ubuntu 24.04), as root:
export WORKER_TS_IP=100.x.y.z        # Tailscale IP of the K8s worker
export TS_AUTHKEY=tskey-...          # optional, otherwise run 'tailscale up' manually
./setup-edge.sh
```

Then verify the source-IP chain from another host:

```bash
EDGE_HOST=<droplet-public-ip> ../../scripts/test_proxy_protocol.sh
```

## Notes

- The HAProxy stats page binds to the **Tailscale IP only** — edit the
  `frontend stats` bind address in `haproxy.cfg` to this droplet's Tailscale IP.
- The honeypot ports use the **raw droplet IP** (no domain, no Cloudflare) so
  attackers see an ordinary VPS. Only `dashboard.` / `api.` go through
  Cloudflare (see `docs/infrastructure.md`).
