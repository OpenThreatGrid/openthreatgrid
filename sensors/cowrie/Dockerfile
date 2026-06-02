# OpenThreatGrid Cowrie sensor image.
# Builds on the upstream Cowrie image and layers in the OTG config overrides.
FROM cowrie/cowrie:latest

# Cowrie reads cowrie.cfg from its etc directory; our overrides take precedence
# over cowrie.cfg.dist.
COPY cowrie.cfg.override /cowrie/cowrie-git/etc/cowrie.cfg

# Logs are written to a volume shared with the OTG parser sidecar.
VOLUME ["/cowrie/var/log/cowrie"]

EXPOSE 2222 2223
