# LiteLLM Deployment Guide

This comprehensive guide covers deploying LiteLLM proxy service with optional Streamlit UI on Kubernetes/OpenShift.

## Prerequisites

- **Kubernetes 1.19+ or OpenShift 4.x**
- **Helm 3.0+**
- **kubectl/oc CLI** configured for your cluster

## Features

- ✅ **LiteLLM proxy** service for unified LLM API access
- ✅ **Optional Streamlit UI** for browsing and testing models
- ✅ **PostgreSQL (pgvector)** for persistence and enterprise features
- ✅ **OpenShift Route support** with auto-generated hostnames
- ✅ **Kubernetes Ingress support**
- ✅ **Configurable model endpoints** for multiple providers
- ✅ **Health checks** and auto-scaling ready

---

## Quick Start

### Option 1: Makefile Deployment (Recommended)

Deploy using the Makefile from the `deploy/` directory:

```bash
cd deploy

# Deploy everything (LiteLLM + UI + PostgreSQL)
make install

# Or deploy to a custom namespace
make install NAMESPACE=my-namespace
```

#### Available Commands

| Command | Description |
|---------|-------------|
| `make install` | Build UI image and deploy all services |
| `make install-api-only` | Deploy only LiteLLM (no Streamlit UI) |
| `make uninstall` | Remove the deployment |
| `make upgrade` | Apply configuration changes |
| `make status` | Show deployment status |
| `make logs` | View logs for all services |
| `make urls` | Display service URLs |
| `make clean` | Uninstall and delete namespace |

Run `make help` for the full list of commands.

### Option 2: Direct Helm Deployment

#### Prepare Dependencies

```bash
# Navigate to the helm directory
cd deploy/helm

# Download chart dependencies (pgvector and llama-stack)
helm dependency update
```

#### Deploy LiteLLM Only

```bash
helm install litellm . \
  --namespace litellm \
  --create-namespace
```

#### Deploy LiteLLM + UI

```bash
# Build UI image first (OpenShift)
cd ../../apps/ui
oc new-build --name litellm-ui --binary --strategy docker -n litellm
oc start-build litellm-ui --from-dir=. --follow -n litellm

# Deploy both services
cd ../../deploy/helm
helm install litellm . \
  --namespace litellm \
  --create-namespace \
  --set ui.enabled=true \
  --set ui.image.repository=image-registry.openshift-image-registry.svc:5000/litellm/litellm-ui \
  --set ui.image.tag=latest
```

---

## Accessing the Services

Once deployed, check that pods are running:

```bash
oc get pods -n litellm
```

Get the route URLs:

```bash
# Get all routes
oc get routes -n litellm

# Get specific URLs
LITELLM_URL=$(oc get route litellm -n litellm -o jsonpath='{.spec.host}')
echo "LiteLLM API: https://$LITELLM_URL"
echo "LiteLLM Admin UI: https://$LITELLM_URL/ui"

# Streamlit UI (if enabled)
UI_URL=$(oc get route litellm-ui -n litellm -o jsonpath='{.spec.host}')
echo "Streamlit UI: https://$UI_URL"

# Test the API
curl https://$LITELLM_URL/health
```

### Service Access Points

- **LiteLLM API**: `https://<litellm-route>` — Main API endpoint for model requests
- **LiteLLM Admin UI**: `https://<litellm-route>/ui` — Admin panel (username: `admin`, password: your `masterKey`)
- **Streamlit UI**: `https://<litellm-ui-route>` — Custom model browser interface

Once the deployment is complete, you should see screens similar to:

<img src='../litellm-ui.png'>

To access the management console, click on "LiteLLM Admin Panel UI". Log in with `admin` as the username and your `masterKey` as the password.

<img src='../login-ui.png'>

---

## Architecture

The deployment consists of three main components working together:

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenShift Namespace                       │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   LiteLLM    │◄───│  Streamlit   │    │  PostgreSQL  │   │
│  │   Proxy      │    │     UI       │    │  (pgvector)  │   │
│  │  Port 4000   │    │  Port 8501   │    │  Port 5432   │   │
│  └──────┬───────┘    └──────────────┘    └──────▲───────┘   │
│         │                                       │            │
│         └───────────────────────────────────────┘            │
│                      DATABASE_URL                            │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Streamlit UI** calls the LiteLLM API to fetch and display available models
2. **LiteLLM Proxy** handles all LLM requests and stores metadata in PostgreSQL
3. **PostgreSQL** persists API keys, teams, budgets, and usage logs

---

## Configuration

### Quick Configuration Changes

Edit `helm/values.yaml` to customize models, credentials, and settings, then apply changes:

```bash
make upgrade
```

### LiteLLM Proxy Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `ghcr.io/berriai/litellm-non_root` |
| `image.tag` | Image tag | `main-latest` |
| `service.port` | Service port | `4000` |
| `litellm.debug` | Enable debug mode | `true` |
| `litellm.masterKey` | Master key for admin UI | `master-key` |
| `litellm.config` | LiteLLM model configuration | See values.yaml |
| `route.enabled` | Enable OpenShift Route | `true` |
| `ingress.enabled` | Enable Kubernetes Ingress | `false` |

### Streamlit UI Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ui.enabled` | Enable UI deployment | `true` |
| `ui.replicaCount` | Number of UI replicas | `1` |
| `ui.image.repository` | UI image repository | `quay.io/ecosystem-appeng/litellm-streamlit-ui` |
| `ui.image.tag` | UI image tag | `latest` |
| `ui.service.port` | UI service port | `8501` |
| `ui.route.enabled` | Enable OpenShift Route for UI | `true` |

### Model Configuration Examples

#### Multiple Providers

```yaml
litellm:
  debug: true
  masterKey: "your-secure-key"
  apiKey: "sk-your-api-key"
  config:
    model_list:
      # Azure OpenAI
      - model_name: gpt-4
        litellm_params:
          model: azure/gpt-4
          api_base: https://your-endpoint.openai.azure.com/
          api_key: your-api-key
      
      # Anthropic Claude
      - model_name: claude
        litellm_params:
          model: anthropic/claude-3-opus-20240229
          api_key: your-api-key
      
      # Local Ollama
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
```

#### Deploy Without UI

```yaml
ui:
  enabled: false
```

#### Enable Kubernetes Ingress

```yaml
route:
  enabled: false

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: litellm.example.com
      paths:
        - path: /
          pathType: Prefix
```

### Customizing the Streamlit UI

The UI receives these environment variables from the Helm deployment:

| Variable | Purpose |
|----------|---------|
| `LITELLM_URL` | Internal URL to the LiteLLM service |
| `LITELLM_API_KEY` | API key for authenticated requests |
| `LITELLM_MASTER_KEY` | Master key for admin operations |

To modify the UI source code:

```bash
# Edit the code
cd apps/ui
vim main.py

# Rebuild the image
oc start-build litellm-ui --from-dir=. --follow -n litellm

# Restart the deployment
oc rollout restart deployment/litellm-ui -n litellm
```

---

## PostgreSQL Database (pgvector)

The PostgreSQL database enables LiteLLM's enterprise features. Without it, LiteLLM runs in stateless mode with limited functionality.

### What Gets Stored

| Data | Description |
|------|-------------|
| **Virtual API Keys** | Generated keys for users/applications to access the proxy |
| **Teams & Users** | Organization structure with assigned members |
| **Budgets** | Spending limits per user, team, or API key |
| **Spend Logs** | Usage tracking and cost attribution |
| **Model Access** | Which keys/teams can access which models |

### Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `pgvector.enabled` | Enable PostgreSQL | `true` |
| `pgvector.secret.user` | Database user | `postgres` |
| `pgvector.secret.password` | Database password | `litellm_password` |
| `pgvector.secret.dbname` | Database name | `litellm` |

Example configuration in `helm/values.yaml`:

```yaml
pgvector:
  enabled: true
  secret:
    user: postgres
    password: litellm_password  # Change in production!
    dbname: litellm
    host: pgvector
    port: "5432"
```

LiteLLM connects using the `DATABASE_URL` environment variable, automatically constructed from these values.

### Disabling the Database

For simple testing without persistence:

```yaml
pgvector:
  enabled: false
```

> **Warning:** Without a database, virtual keys, spend tracking, and team management will not be available.

---

## Troubleshooting

### Check Deployment Status

```bash
# Check pod status
oc get pods -n litellm
oc describe pod <pod-name> -n litellm

# Check services and routes
oc get svc,routes -n litellm

# Check deployment status
make status
```

### View Logs

```bash
# All services
make logs

# Specific components
make logs-api      # LiteLLM only
make logs-ui       # Streamlit UI only

# Direct kubectl/oc logs
oc logs -n litellm -l app.kubernetes.io/name=litellm
oc logs -n litellm deployment/litellm-ui
```

### Common Issues

#### LiteLLM Pod Not Starting

```bash
# Describe pod for events
kubectl describe pod -n litellm -l app.kubernetes.io/name=litellm

# Check logs for errors
kubectl logs -n litellm -l app.kubernetes.io/name=litellm
```

#### UI Cannot Connect to LiteLLM

```bash
# Check ConfigMap
kubectl get configmap litellm-ui-config -n litellm -o yaml

# Test connection from UI pod
kubectl exec -it -n litellm deployment/litellm-ui -- curl http://litellm:4000/health
```

#### Database Connection Issues

```bash
# Test database environment variables
oc exec -it deployment/litellm -n litellm -- env | grep DATABASE

# Test database connectivity
oc exec -it deployment/pgvector -n litellm -- psql -U postgres -d litellm -c "SELECT version();"
```

#### Configuration Changes Not Applied

```bash
# Force restart after config changes
oc rollout restart deployment/litellm -n litellm
oc rollout restart deployment/litellm-ui -n litellm

# Or use make command
make upgrade
```

---

## Production Considerations

### Security

- **Change default passwords** in `pgvector.secret.password`
- **Use strong master keys** for production deployments
- **Enable TLS termination** at the route/ingress level
- **Restrict network access** using NetworkPolicies

### Scaling

- **Increase replicas** for high availability:
  ```yaml
  replicaCount: 3
  ui:
    replicaCount: 2
  ```
- **Configure resource limits** based on your workload
- **Enable horizontal pod autoscaling** for dynamic scaling

### Monitoring

- **Health checks** are configured by default
- **Prometheus metrics** available at `/metrics` endpoint
- **Log aggregation** recommended for production environments

---

## Related Documentation

- **[Usage Guide](../USAGE_GUIDE.md)** - How to use the deployed application
- **[LLM-D Integration](llm-d-integration/README.md)** - RHOAI model serving setup
- **[Demo Guides](../demos/)** - Feature demonstrations
- **[UI Development](../apps/ui/README.md)** - Streamlit UI customization
