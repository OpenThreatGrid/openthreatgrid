{{/* Common naming + label helpers. */}}

{{- define "otg.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "otg.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "otg.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "otg.labels" -}}
app.kubernetes.io/part-of: openthreatgrid
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{/* Fully-qualified image reference for an OTG-built image name. */}}
{{- define "otg.image" -}}
{{- printf "%s/%s:%s" .root.Values.image.registry .name .root.Values.image.tag -}}
{{- end -}}

{{/* Filebeat sidecar container. Params: root, logType, logPath, sensorId,
     logVolume, logMount. */}}
{{- define "otg.filebeatSidecar" -}}
- name: filebeat
  image: {{ .root.Values.filebeat.image }}
  args: ["-e", "--strict.perms=false"]
  env:
    - { name: LOG_TYPE, value: {{ .logType | quote }} }
    - { name: LOG_PATH, value: {{ .logPath | quote }} }
    - { name: SENSOR_ID, value: {{ .sensorId | quote }} }
    - { name: LOGSTASH_HOST, value: "logstash:5044" }
  resources:
    requests: { cpu: 50m, memory: 64Mi }
    limits: { cpu: 200m, memory: 128Mi }
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
  volumeMounts:
    - { name: {{ .logVolume }}, mountPath: {{ .logMount }}, readOnly: true }
    - { name: filebeat-config, mountPath: /usr/share/filebeat/filebeat.yml, subPath: filebeat.yml, readOnly: true }
    - { name: filebeat-data, mountPath: /usr/share/filebeat/data }
{{- end -}}

{{/* Volumes the Filebeat sidecar needs (config + registry). */}}
{{- define "otg.filebeatVolumes" -}}
- name: filebeat-config
  configMap:
    name: filebeat-config
- name: filebeat-data
  emptyDir: {}
{{- end -}}

