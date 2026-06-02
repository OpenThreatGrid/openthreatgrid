# mmproxy sidecar

[go-mmproxy](https://github.com/path-network/go-mmproxy) restores the real client
IP for a backend sitting behind a PROXY-protocol-speaking load balancer.

Cowrie has **no native PROXY-protocol support**, so without this the only source
IP it can log is Traefik's pod IP. mmproxy solves that:

```
HAProxy(VPS) ─PROXYv2─► Traefik ─PROXYv2─► go-mmproxy ─transparent─► Cowrie
                                                                      └─ sees REAL attacker IP
```

## How it runs (in the Cowrie pod)

- **init container** (NET_ADMIN): adds the loopback routing table so transparent
  replies from Cowrie return through mmproxy:
  ```
  ip rule add from 127.0.0.1/8 iif lo table 123
  ip route add local 0.0.0.0/0 dev lo table 123
  ```
- **mmproxy-ssh / mmproxy-telnet sidecars** (NET_ADMIN): listen on 2222/2223,
  parse the PROXY header, and forward to Cowrie on `127.0.0.1:12222/12223` using
  `IP_TRANSPARENT` so Cowrie sees the original source.
- **cowrie** stays fully locked down (drops ALL caps) and listens only on
  localhost high ports.

Only the mmproxy/init containers hold `NET_ADMIN`; Cowrie itself does not.
