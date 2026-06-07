# OpenThreatGrid Logstash image — Apache-2.0 OSS build + OpenSearch output.
#
# 7.12.1-oss is the Apache-2.0 distribution (the non-oss 7.12.1 is Elastic
# Licensed). The opensearch output plugin lets it write to OpenSearch (the
# bundled elasticsearch output refuses OpenSearch's version string).
FROM docker.elastic.co/logstash/logstash-oss:7.12.1

# Network-isolated at runtime, so install the plugin at build time.
RUN bin/logstash-plugin install logstash-output-opensearch

# Bake the OTG pipeline in (single source of truth). Compose can still bind-mount
# over /usr/share/logstash/pipeline for live edits.
COPY pipeline/ /usr/share/logstash/pipeline/

# NOTE: do NOT set XPACK_MONITORING_ENABLED here — the -oss build has no X-Pack,
# so that setting is unregistered and Logstash exits FATAL on startup.
