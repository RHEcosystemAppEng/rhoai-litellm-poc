{{/*
Expand the name of the chart.
*/}}
{{- define "litellm.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "litellm.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "litellm.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "litellm.labels" -}}
helm.sh/chart: {{ include "litellm.chart" . }}
{{ include "litellm.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "litellm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "litellm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "litellm.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "litellm.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the LlamaStack API key.
Priority:
1. Explicit llama-stack.litellmApiKey value if set
2. First seed user's api_key if seed is enabled and user has api_key
3. Fallback to the global litellm.apiKey
*/}}
{{- define "litellm.llamastackApiKey" -}}
{{- $llamastack := index .Values "llama-stack" -}}
{{- if and $llamastack $llamastack.litellmApiKey -}}
  {{- $llamastack.litellmApiKey -}}
{{- else if and .Values.seed .Values.seed.enabled .Values.seed.users -}}
  {{- range .Values.seed.users -}}
    {{- if .api_key -}}
      {{- .api_key -}}
      {{- break -}}
    {{- end -}}
  {{- end -}}
{{- else -}}
  {{- .Values.litellm.apiKey -}}
{{- end -}}
{{- end -}}

{{/*
Name of the LlamaStack API key secret.
This is a fixed name so it can be referenced in values.yaml for subcharts.
*/}}
{{- define "litellm.llamastackApiKeySecretName" -}}
llamastack-litellm-apikey
{{- end -}}
