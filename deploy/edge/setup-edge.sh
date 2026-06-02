#!/usr/bin/env bash
# OpenThreatGrid — DigitalOcean VPS edge bootstrap.
#
# Installs Tailscale + HAProxy, deploys the honeypot proxy config, and locks
# the box down with UFW (only 2222/2223/443 from the internet; management SSH
# via Tailscale only). Run as root on a fresh Ubuntu 24.04 droplet.
#
#   WORKER_TS_IP=100.x.y.z ./setup-edge.sh
set -euo pipefail

WORKER_TS_IP="${WORKER_TS_IP:-}"
TS_AUTHKEY="${TS_AUTHKEY:-}"        # optional: tailscale up --authkey
SSH_MGMT_PORT="${SSH_MGMT_PORT:-22}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root." >&2; exit 1
fi
if [[ -z "${WORKER_TS_IP}" ]]; then
  echo "Set WORKER_TS_IP to the K8s worker's Tailscale IP." >&2; exit 1
fi

echo "==> Updating base system..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y haproxy ufw fail2ban curl gnupg unattended-upgrades

echo "==> Installing Tailscale..."
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
if [[ -n "${TS_AUTHKEY}" ]]; then
  tailscale up --authkey "${TS_AUTHKEY}" --ssh
else
  echo "    No TS_AUTHKEY provided. Run 'tailscale up --ssh' manually, then re-run."
  tailscale up --ssh || true
fi

echo "==> Deploying HAProxy config (worker = ${WORKER_TS_IP})..."
# This VPS's own Tailscale IP — used to bind the stats page Tailscale-only.
VPS_TS_IP="$(tailscale ip -4 2>/dev/null | head -1)"
if [[ -z "${VPS_TS_IP}" ]]; then
  echo "Could not determine this VPS's Tailscale IP. Is 'tailscale up' done?" >&2
  exit 1
fi
echo "    VPS Tailscale IP: ${VPS_TS_IP}"

install -d -m 0755 /run/haproxy
sed -e "s/<TAILSCALE_IP_WORKER>/${WORKER_TS_IP}/g" \
    -e "s/<TAILSCALE_IP_DO_VPS>/${VPS_TS_IP}/g" \
    "$(dirname "$0")/haproxy.cfg" > /etc/haproxy/haproxy.cfg
haproxy -c -f /etc/haproxy/haproxy.cfg
systemctl enable --now haproxy
systemctl reload haproxy

echo "==> Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
# Honeypot + HTTPS from the whole internet (raw IP exposure, no Cloudflare).
ufw allow 2222/tcp comment 'cowrie ssh honeypot'
ufw allow 2223/tcp comment 'cowrie telnet honeypot'
ufw allow 443/tcp  comment 'traefik https'
# Management SSH ONLY over the Tailscale interface.
ufw allow in on tailscale0 to any port "${SSH_MGMT_PORT}" proto tcp comment 'mgmt ssh via tailscale'
# HAProxy stats page ONLY over Tailscale.
ufw allow in on tailscale0 to any port 8404 proto tcp comment 'haproxy stats via tailscale'
ufw --force enable

echo "==> Hardening SSH (key-only) and enabling auto-updates..."
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload ssh || systemctl reload sshd || true
systemctl enable --now fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades || true

echo "==> Done. Verify with: scripts/test_proxy_protocol.sh"
ufw status verbose
