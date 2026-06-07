# Filebeat + Logstash (ingestion — topology A)

OpenThreatGrid's ingestion: each sensor's log is shipped by **Filebeat** to a
single **Logstash** that normalizes + enriches and writes straight to OpenSearch.

```
Sensor → <log> → Filebeat (sidecar) → Logstash → OpenSearch (otg-events-*)
```

This directory holds the **Logstash image build context** and the **canonical
configs**; the running manifests live in the base deploy (`deploy/k8s/`, Helm).

| Path | Purpose |
|---|---|
| [`logstash/Dockerfile`](logstash/Dockerfile) | `logstash-oss:7.12.1` + `logstash-output-opensearch` + baked pipeline (image `otg-logstash`) |
| [`logstash/pipeline/otg.conf`](logstash/pipeline/otg.conf) | Unified pipeline; branches on `log_type` (cowrie / opencanary / http-trap) |
| [`filebeat/filebeat.yml`](filebeat/filebeat.yml) | Generic Filebeat config (env: `LOG_PATH` / `LOG_TYPE` / `SENSOR_ID`); mirrored into `deploy/k8s/filebeat/configmap.yaml` and the Helm chart |

## Licensing

The Apache-2.0 `-oss` builds are used (the default 7.12.1 is Elastic-Licensed):
`filebeat-oss:7.12.1` and `logstash-oss:7.12.1`. Logstash writes to OpenSearch
via the opensearch output plugin (Filebeat can't — it version-checks for
Elasticsearch).

## Index template first

Logstash uses `manage_template => false`, so apply the OTG mappings before any
events flow:

```bash
OPENSEARCH_URL=http://localhost:9200 ../../scripts/bootstrap_opensearch.sh
```

## Local PoC

The root [`docker-compose.yml`](../../docker-compose.yml) runs the whole stack
(Cowrie → Filebeat → Logstash → OpenSearch + Dashboards):

```bash
../../scripts/run_local.sh
ssh -p 2222 root@localhost          # generate events
# Dashboards: http://localhost:5601
```

## Kubernetes

Logstash + the per-sensor Filebeat sidecars are part of the base deploy
(`deploy/k8s/logstash/`, `deploy/k8s/filebeat/`, and each sensor's Deployment)
and the Helm chart (`logstash.enabled`, Filebeat sidecar via the
`otg.filebeatSidecar` helper). Validate the pipeline before rollout:

```bash
docker run --rm ghcr.io/openthreatgrid/otg-logstash:main \
  logstash -t -f /usr/share/logstash/pipeline/otg.conf
```

See [`docs/filebeat-logstash.md`](../../docs/filebeat-logstash.md) and
[`docs/sensor-integration.md`](../../docs/sensor-integration.md).
