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

