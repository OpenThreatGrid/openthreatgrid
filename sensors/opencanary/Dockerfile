# OpenCanary multi-service deception sensor for OpenThreatGrid.
#
# Emits JSON log lines to /var/log/opencanary/opencanary.log, which the OTG
# worker parser (SENSOR_TYPE=opencanary) tails from a shared volume.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# scapy/pcap are runtime deps of some OpenCanary modules; build tools for wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpcap-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir opencanary scapy

# Non-root user; the configured ports are all >1024 so no extra capabilities.
RUN useradd --create-home --uid 10002 canary \
    && mkdir -p /var/log/opencanary \
    && chown -R canary:canary /var/log/opencanary

# opencanaryd reads ~/.opencanary.conf by default.
COPY opencanary.conf /home/canary/.opencanary.conf

USER canary
WORKDIR /home/canary

# Ports must match opencanary.conf above.
EXPOSE 2121 2222 2323 8080

# --dev keeps opencanaryd in the foreground (no daemonization) for containers.
CMD ["opencanaryd", "--dev"]
