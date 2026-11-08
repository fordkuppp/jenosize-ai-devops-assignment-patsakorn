{{- define "service-policy.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "service-policy.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Values.target.name | required "target.name is required" | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/* The Service in front of the target. Defaults to the workload name. */}}
{{- define "service-policy.serviceName" -}}
{{- default .Values.target.name .Values.target.service.name }}
{{- end }}

{{- define "service-policy.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
app.kubernetes.io/name: {{ include "service-policy.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ include "service-policy.fullname" . }}
{{- end }}

{{/* True when Flagger owns traffic, i.e. anything but a plain rolling update. */}}
{{- define "service-policy.flaggerManaged" -}}
{{- ne .Values.strategy.type "RollingUpdate" -}}
{{- end }}
