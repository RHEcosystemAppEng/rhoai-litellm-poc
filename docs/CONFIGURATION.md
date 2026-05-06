# LiteLLM Configuration Reference

This comprehensive guide provides all YAML configuration examples used throughout the LiteLLM platform. Use this as your single source of truth for configuration options.

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [Model Configurations](#model-configurations)
- [Team and User Management](#team-and-user-management)
- [Security Settings](#security-settings)
- [Advanced Features](#advanced-features)
- [Demo-Specific Configurations](#demo-specific-configurations)
- [Production Configurations](#production-configurations)

---

## Basic Configuration

### Minimal Setup

The simplest functional configuration for testing:

```yaml
# deploy/helm/values.yaml
litellm:
  debug: true
  masterKey: "master-key"
  apiKey: "sk-1234567890"
  
  config:
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434

# PostgreSQL enabled by default
pgvector:
  enabled: true
  secret:
    user: postgres
    password: litellm_password
    dbname: litellm
    host: pgvector
    port: "5432"

# UI enabled by default
ui:
  enabled: true
```

### Production-Ready Basic Setup

Enhanced configuration for production environments:

```yaml
litellm:
  debug: false
  masterKey: "your-secure-master-key-here"
  apiKey: "sk-your-production-api-key"
  
  # Resource limits for production
  resources:
    limits:
      cpu: "2"
      memory: "4Gi"
    requests:
      cpu: "1"
      memory: "2Gi"
  
  config:
    general_settings:
      completion_model: "llama3"
      
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434

# Production database configuration
pgvector:
  enabled: true
  secret:
    user: postgres
    password: "your-secure-database-password"
    dbname: litellm
    host: pgvector
    port: "5432"
  
  # Database resource limits
  resources:
    limits:
      cpu: "1"
      memory: "2Gi"
    requests:
      cpu: "500m"
      memory: "1Gi"

# UI configuration
ui:
  enabled: true
  replicaCount: 2  # High availability
```

---

## Model Configurations

### Local Models (Ollama)

Configuration for locally hosted Ollama models:

```yaml
litellm:
  config:
    model_list:
      # Basic Ollama model
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
      
      # Ollama with custom parameters
      - model_name: llama3-custom
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          temperature: 0.7
          max_tokens: 1000
          timeout: 30
```

### Cloud Provider Models

#### OpenAI Configuration

```yaml
litellm:
  config:
    model_list:
      # Standard OpenAI
      - model_name: gpt-4
        litellm_params:
          model: gpt-4
          api_key: "your-openai-api-key"
      
      # OpenAI with organization
      - model_name: gpt-4-org
        litellm_params:
          model: gpt-4
          api_key: "your-openai-api-key"
          organization: "your-org-id"
```

#### Azure OpenAI Configuration

```yaml
litellm:
  config:
    model_list:
      - model_name: azure-gpt-4
        litellm_params:
          model: azure/gpt-4
          api_base: https://your-endpoint.openai.azure.com/
          api_key: "your-azure-api-key"
          api_version: "2024-02-15-preview"
```

#### Anthropic Claude Configuration

```yaml
litellm:
  config:
    model_list:
      - model_name: claude
        litellm_params:
          model: anthropic/claude-3-opus-20240229
          api_key: "your-anthropic-api-key"
      
      - model_name: claude-sonnet
        litellm_params:
          model: anthropic/claude-3-sonnet-20240229
          api_key: "your-anthropic-api-key"
```

#### Google Cloud Models

```yaml
litellm:
  config:
    model_list:
      - model_name: gemini-pro
        litellm_params:
          model: gemini/gemini-pro
          api_key: "your-google-api-key"
```

### Red Hat OpenShift AI Models

Configuration for RHOAI-deployed models:

```yaml
litellm:
  config:
    model_list:
      # RHOAI vLLM model
      - model_name: llama-fp8
        litellm_params:
          model: openai/llama-fp8
          api_base: http://llama-fp8-predictor.namespace.svc.cluster.local:8080/v1
          api_key: "none"  # No auth required for internal endpoints
      
      # Multiple RHOAI models
      - model_name: granite-code
        litellm_params:
          model: openai/granite-code
          api_base: http://granite-code-predictor.namespace.svc.cluster.local:8080/v1
          api_key: "none"
```

### Multi-Provider Setup

Complete configuration with multiple providers:

```yaml
litellm:
  config:
    model_list:
      # Local models
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
      
      # Cloud models
      - model_name: gpt-4
        litellm_params:
          model: gpt-4
          api_key: "your-openai-api-key"
      
      - model_name: claude
        litellm_params:
          model: anthropic/claude-3-opus-20240229
          api_key: "your-anthropic-api-key"
      
      # RHOAI models
      - model_name: llama-fp8
        litellm_params:
          model: openai/llama-fp8
          api_base: http://llama-fp8-predictor.namespace.svc.cluster.local:8080/v1
          api_key: "none"
```

---

## Team and User Management

### Basic Team Setup

Configuration for organizational structure:

```yaml
seed:
  enabled: true
  teams:
    - team_alias: engineering
      max_budget: 100.0
    - team_alias: marketing
      max_budget: 50.0
    - team_alias: sales
      max_budget: 75.0
```

### Advanced Team Configuration

Enhanced team setup with detailed budgets:

```yaml
seed:
  enabled: true
  teams:
    # Engineering team - high usage
    - team_alias: engineering
      max_budget: 500.0
      budget_duration: "1mo"  # Monthly budget
      models: ["gpt-4", "claude", "llama3"]  # Allowed models
    
    # Marketing team - moderate usage
    - team_alias: marketing
      max_budget: 200.0
      budget_duration: "1mo"
      models: ["gpt-4", "llama3"]  # Limited model access
    
    # Demo team - minimal usage
    - team_alias: demo
      max_budget: 10.0
      budget_duration: "1d"  # Daily budget for testing
      models: ["llama3"]  # Local models only

  # Default user configuration
  users:
    - user_email: "eng-admin@example.com"
      team: "engineering"
      role: "admin"
    - user_email: "mkt-user@example.com"
      team: "marketing"
      role: "user"
```

---

## Security Settings

### Authentication Configuration

```yaml
litellm:
  masterKey: "your-secure-master-key"
  apiKey: "sk-your-default-api-key"
  
  config:
    general_settings:
      # Security settings
      master_key: "your-secure-master-key"
      ui_access_mode: "admin_only"
      enforce_user_param: true
      
      # Rate limiting
      rpm: 500  # Requests per minute
      tpm: 100000  # Tokens per minute
```

### Database Security

```yaml
pgvector:
  enabled: true
  secret:
    user: postgres
    password: "your-very-secure-database-password-here"
    dbname: litellm
    host: pgvector
    port: "5432"
    
  # Network security
  networkPolicy:
    enabled: true
    ingress:
      - from:
          - podSelector:
              matchLabels:
                app.kubernetes.io/name: litellm
```

---

## Advanced Features

### Failover Configuration

Setup automatic model failover:

```yaml
litellm:
  config:
    router_settings:
      routing_strategy: usage-based-routing-v2
      model_group_alias: "production-llm"
      
      # Fallback chain
      fallbacks:
        - primary: gpt-4
          fallback: claude
        - primary: claude
          fallback: llama3
      
      # Health checks
      health_checks: true
      health_check_interval: 300  # 5 minutes

    model_list:
      # Primary models with fallback
      - model_name: gpt-4
        litellm_params:
          model: gpt-4
          api_key: "your-openai-key"
          rpm: 100
      
      - model_name: claude
        litellm_params:
          model: anthropic/claude-3-opus-20240229
          api_key: "your-anthropic-key"
          rpm: 50
      
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          rpm: 200  # Local model, higher limits
```

### Content Guardrails

Configuration for AI safety using LlamaGuard:

```yaml
litellm:
  config:
    # Content safety settings
    guardrails:
      enabled: true
      provider: "llamaguard"
      model: "llamaguard-3-8b"
      
    model_list:
      # Protected model with guardrails
      - model_name: gpt-4-safe
        litellm_params:
          model: gpt-4
          api_key: "your-openai-key"
          guardrails: ["llamaguard-3-8b"]
      
      # Guardrail model itself
      - model_name: llamaguard-3-8b
        litellm_params:
          model: ollama/llamaguard-3-8b
          api_base: http://ollama:11434
```

### LlamaStack Integration

Advanced configuration for LlamaStack integration:

```yaml
# LlamaStack specific configuration
llamastack:
  enabled: true
  config:
    inference_api:
      provider: litellm
      config:
        api_base: http://litellm:4000
        models:
          - model_id: llama3
            provider_model_id: ollama/llama3
          - model_id: gpt-4
            provider_model_id: gpt-4

litellm:
  config:
    # Enhanced for LlamaStack compatibility
    general_settings:
      completion_model: "llama3"
      llamastack_integration: true
      
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          # LlamaStack metadata
          metadata:
            llamastack_compatible: true
            context_length: 8192
```

---

## Demo-Specific Configurations

### Budget Demo Configuration

Minimal budget setup for testing:

```yaml
litellm:
  masterKey: "demo-master-key"
  apiKey: "sk-demo-key"
  
  config:
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          cost_per_token: 0.0001  # Low cost for testing

seed:
  enabled: true
  teams:
    - team_alias: demo-team
      max_budget: 0.10  # 10 cents for demo
```

### Guardrails Demo Configuration

Setup for content safety demonstration:

```yaml
litellm:
  config:
    model_list:
      # Main model with safety
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          guardrails: ["llamaguard-3-8b"]
      
      # Safety model
      - model_name: llamaguard-3-8b
        litellm_params:
          model: ollama/llamaguard-3-8b
          api_base: http://ollama:11434

# Ensure LlamaGuard model is available
# Note: This requires separate Ollama deployment with LlamaGuard
```

### Failover Demo Configuration

Setup for testing model failover:

```yaml
litellm:
  config:
    router_settings:
      routing_strategy: usage-based-routing-v2
      fallbacks:
        - primary: llama3
          fallback: llama-fp8
    
    model_list:
      # Primary model (will be scaled down in demo)
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
          timeout: 5  # Quick timeout for demo
      
      # Fallback model
      - model_name: llama-fp8
        litellm_params:
          model: openai/llama-fp8
          api_base: http://llama-fp8-predictor.namespace.svc.cluster.local:8080/v1
          api_key: "none"
```

---

## Production Configurations

### High Availability Setup

Configuration for production environments:

```yaml
# HA LiteLLM deployment
litellm:
  replicaCount: 3  # Multiple instances
  
  resources:
    limits:
      cpu: "2"
      memory: "4Gi"
    requests:
      cpu: "1"
      memory: "2Gi"
  
  # Production settings
  debug: false
  masterKey: "production-master-key-secure"
  
  config:
    general_settings:
      # Performance settings
      max_budget: 10000.0
      budget_duration: "30d"
      
      # Security settings
      enforce_user_param: true
      ui_access_mode: "admin_only"
      
      # Rate limiting
      rpm: 1000
      tpm: 500000
    
    model_list:
      # Production model pool
      - model_name: gpt-4
        litellm_params:
          model: gpt-4
          api_key: "prod-openai-key"
          rpm: 300
      
      - model_name: claude
        litellm_params:
          model: anthropic/claude-3-opus-20240229
          api_key: "prod-anthropic-key"
          rpm: 200

# HA Database
pgvector:
  enabled: true
  replicaCount: 3  # Database cluster
  
  secret:
    user: postgres
    password: "production-database-password-very-secure"
    dbname: litellm
  
  resources:
    limits:
      cpu: "2"
      memory: "8Gi"
    requests:
      cpu: "1"
      memory: "4Gi"

# HA UI
ui:
  enabled: true
  replicaCount: 2
  
  resources:
    limits:
      cpu: "1"
      memory: "2Gi"
    requests:
      cpu: "500m"
      memory: "1Gi"
```

### Enterprise Security Configuration

Enhanced security for enterprise deployments:

```yaml
litellm:
  config:
    general_settings:
      # Authentication
      master_key: "enterprise-master-key"
      ui_access_mode: "admin_only"
      enforce_user_param: true
      
      # Audit logging
      success_callback: ["langfuse"]
      failure_callback: ["slack"]
      
      # Content filtering
      content_policy: "strict"
      guardrails: ["llamaguard-3-8b"]
      
      # Rate limiting by user/team
      default_user_max_budget: 100.0
      default_team_max_budget: 1000.0

# Network security
networkPolicy:
  enabled: true
  ingress:
    # Only allow specific sources
    - from:
        - namespaceSelector:
            matchLabels:
              name: approved-apps
        - podSelector:
            matchLabels:
              app: trusted-client

# TLS configuration
route:
  enabled: true
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```

---

## Configuration Validation

### Syntax Validation

Always validate your YAML syntax:

```bash
# Validate Helm values
helm lint deploy/helm/

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('deploy/helm/values.yaml'))"

# Test configuration
helm template litellm deploy/helm/ --values custom-values.yaml
```

### Configuration Testing

Test configurations before deployment:

```bash
# Dry run installation
helm install litellm deploy/helm/ --dry-run --debug

# Validate against cluster
helm install litellm deploy/helm/ --dry-run --validate

# Check resource requirements
kubectl apply --dry-run=client -f <(helm template litellm deploy/helm/)
```

---

## Troubleshooting Configuration

### Common Configuration Errors

1. **Invalid YAML Syntax**
   ```bash
   # Error: mapping values are not allowed here
   # Fix: Check indentation and colons
   ```

2. **Missing Required Fields**
   ```yaml
   # Error: model_list item missing required fields
   # Fix: Ensure each model has name and litellm_params
   model_list:
     - model_name: required
       litellm_params:
         model: required
   ```

3. **Resource Conflicts**
   ```bash
   # Check for port conflicts
   oc get svc -n litellm
   
   # Check resource availability
   oc describe nodes | grep -A 5 "Allocated resources"
   ```

### Configuration Debugging

```bash
# Check applied configuration
oc get configmap litellm-config -n litellm -o yaml

# Verify environment variables
oc exec deployment/litellm -n litellm -- env | grep LITELLM

# Test configuration changes
make upgrade
oc rollout status deployment/litellm -n litellm
```

---

## Related Documentation

- **[Deployment Guide](../deploy/DEPLOYMENT.md)** - How to deploy with these configurations
- **[Usage Guide](../USAGE_GUIDE.md)** - Using the configured platform
- **[Demo Guides](../demos/)** - Practical configuration examples  
- **[Troubleshooting Guide](../TROUBLESHOOTING.md)** - Configuration problem resolution

---

## Configuration Templates

### Quick Start Template

```yaml
# Minimal working configuration
litellm:
  masterKey: "change-me"
  apiKey: "sk-change-me"
  config:
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
pgvector:
  enabled: true
ui:
  enabled: true
```

### Production Template

```yaml
# Production-ready configuration
litellm:
  debug: false
  replicaCount: 3
  masterKey: "secure-master-key"
  resources:
    limits: {cpu: "2", memory: "4Gi"}
    requests: {cpu: "1", memory: "2Gi"}
  config:
    general_settings:
      max_budget: 1000.0
      rpm: 500
    model_list:
      - model_name: production-model
        litellm_params:
          model: gpt-4
          api_key: "production-key"
pgvector:
  enabled: true
  replicaCount: 2
  resources:
    limits: {cpu: "1", memory: "4Gi"}
ui:
  enabled: true
  replicaCount: 2
```

Save these templates as starting points for your specific needs.