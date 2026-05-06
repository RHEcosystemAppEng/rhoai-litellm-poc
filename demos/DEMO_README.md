# Demo Guide Overview

This directory contains feature demonstrations for the LiteLLM platform. Each demo showcases specific capabilities with working code examples and detailed explanations.

## Available Demos

| Demo | Feature | Complexity | Prerequisites |
|------|---------|------------|---------------|
| **[Budget Management](budget_demo.md)** | API spend controls | Basic | LiteLLM deployment |
| **[Failover Routing](failover_demo.md)** | Model availability handling | Intermediate | Multiple models |
| **[Content Guardrails](guardrails_demo.md)** | AI safety & moderation | Advanced | LlamaGuard model |
| **[LlamaStack Budget](llamastack_budget_demo.md)** | Advanced budget integration | Expert | LlamaStack setup |

---

## Prerequisites

### System Requirements

All demos require:

- **Python 3.10+**
- **Access to deployed LiteLLM platform** (see [Deployment Guide](../deploy/DEPLOYMENT.md))
- **Virtual environment** (recommended)

### Python Environment Setup

#### Option 1: Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv litellm-demos
source litellm-demos/bin/activate  # Linux/Mac
# OR
litellm-demos\Scripts\activate     # Windows

# Install base dependencies
pip install --upgrade pip
```

#### Option 2: Using uv (Fast Alternative)

```bash
# Install uv if not available
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project environment
uv venv litellm-demos
source litellm-demos/bin/activate
```

### Required Python Packages

Install based on which demos you plan to run:

```bash
# Basic demos (budget, failover)
pip install litellm requests openai

# Advanced demos (guardrails, llamastack)
pip install litellm requests openai llamastack

# Development tools (optional)
pip install jupyter ipython
```

Or install all at once:
```bash
pip install litellm requests openai llamastack jupyter ipython
```

### Platform Access

Before running demos, ensure you have:

1. **LiteLLM deployment running** - See [Deployment Guide](../deploy/DEPLOYMENT.md)
2. **Admin access to create API keys** - See [Usage Guide](../USAGE_GUIDE.md)
3. **Route URLs** - Get from OpenShift: `oc get routes -n litellm`

---

## Getting Started

### Step 1: Verify Deployment

```bash
# Check that LiteLLM is accessible
curl "https://<your-litellm-route>/health"

# List available models
curl "https://<your-litellm-route>/models" \
  -H "Authorization: Bearer <your-api-key>"
```

### Step 2: Environment Configuration

Create a `.env` file in the demos directory:

```bash
# Demo environment variables
LITELLM_URL=https://your-litellm-route.apps.cluster.domain
LITELLM_API_KEY=sk-your-api-key
LITELLM_MASTER_KEY=your-master-key

# Optional: Model-specific settings
DEFAULT_MODEL=llama3
BUDGET_LIMIT=0.001
```

**Security Note:** Never commit `.env` files to git. Add to `.gitignore`.

### Step 3: Choose Your Demo

Start with simpler demos and progress to advanced ones:

1. **[Budget Demo](budget_demo.md)** - Understand API spend controls
2. **[Failover Demo](failover_demo.md)** - Learn about model redundancy  
3. **[Guardrails Demo](guardrails_demo.md)** - Explore content safety
4. **[LlamaStack Budget Demo](llamastack_budget_demo.md)** - Advanced integration

---

## Demo Patterns

### Common Demo Structure

Each demo follows this pattern:

```markdown
# Demo Title
## Overview - What the demo demonstrates
## Prerequisites - Specific requirements
## Configuration - Setup instructions  
## Running the Demo - Step-by-step execution
## Expected Output - What you should see
## Troubleshooting - Common issues
```

### Shared Configuration

Many demos use similar LiteLLM configurations:

#### Basic Model Setup
```yaml
litellm:
  config:
    model_list:
      - model_name: llama3
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
```

#### Budget Configuration
```yaml
seed:
  enabled: true
  teams:
    - team_alias: demo-team
      max_budget: 10.0
```

#### Failover Configuration
```yaml
router_settings:
  routing_strategy: usage-based-routing-v2
  fallbacks:
    - primary: llama3
      fallback: llama-fp8
```

### Testing Utilities

Create a shared utility script `demo_utils.py`:

```python
import os
import requests
from typing import Dict, Any

def get_litellm_config() -> Dict[str, str]:
    """Get LiteLLM configuration from environment."""
    return {
        'base_url': os.getenv('LITELLM_URL'),
        'api_key': os.getenv('LITELLM_API_KEY'),
        'master_key': os.getenv('LITELLM_MASTER_KEY')
    }

def test_connection(config: Dict[str, str]) -> bool:
    """Test connection to LiteLLM."""
    try:
        response = requests.get(f"{config['base_url']}/health")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def list_models(config: Dict[str, str]) -> list:
    """List available models."""
    headers = {'Authorization': f"Bearer {config['api_key']}"}
    response = requests.get(f"{config['base_url']}/models", headers=headers)
    return response.json().get('data', [])
```

---

## Troubleshooting

### Common Issues

#### Cannot Connect to LiteLLM

**Check deployment status:**
```bash
oc get pods -n litellm
oc get routes -n litellm
```

**Verify URL format:**
- Must include `https://`
- Should NOT include `/v1` suffix
- Example: `https://litellm-route.apps.cluster.domain`

#### API Key Issues

**Symptoms:** `401 Unauthorized` errors

**Solutions:**
1. **Verify key format** - Should start with `sk-`
2. **Check key permissions** - Ensure access to requested models
3. **Verify budget limits** - Check if spending limit exceeded

#### Import Errors

**Missing packages:**
```bash
# Install missing dependencies
pip install litellm requests openai

# For advanced demos
pip install llamastack
```

#### Model Not Available

**Check model configuration:**
```bash
# List configured models
curl "https://<litellm-route>/models" \
  -H "Authorization: Bearer <api-key>"

# Check specific model status
curl "https://<litellm-route>/model/info" \
  -H "Authorization: Bearer <api-key>" \
  -d '{"model": "llama3"}'
```

### Performance Tips

1. **Use small budget limits** for testing to avoid costs
2. **Run demos in sequence** to avoid rate limiting
3. **Monitor resource usage** in OpenShift console
4. **Clean up test resources** after demo completion

---

## Demo Development Guidelines

### Adding New Demos

When creating new demonstrations:

1. **Follow naming convention**: `feature_demo.md` and `feature_test.py`
2. **Include prerequisites section** with specific requirements
3. **Provide working configuration** examples
4. **Show expected output** with screenshots or logs  
5. **Add troubleshooting section** for common issues
6. **Update this overview** with demo entry

### Configuration Examples

Keep YAML configurations minimal and focused:

```yaml
# Good: Focused example
litellm:
  config:
    model_list:
      - model_name: test-model
        litellm_params:
          model: ollama/llama3
          api_base: http://ollama:11434
```

```yaml
# Avoid: Complex, unrelated settings
litellm:
  config:
    # ... many unrelated settings ...
    model_list:
      - model_name: test-model
        # ... complex configuration ...
```

### Testing Standards

Each demo should include:
- **Smoke test** - Basic functionality verification
- **Error handling** - Demonstrate expected failures
- **Cleanup code** - Resource removal after testing
- **Documentation** - Clear explanation of each step

---

## Related Documentation

- **[Usage Guide](../USAGE_GUIDE.md)** - Platform usage instructions
- **[Deployment Guide](../deploy/DEPLOYMENT.md)** - Setup and installation
- **[Configuration Reference](../docs/CONFIGURATION.md)** - Detailed configuration options
- **[Troubleshooting Guide](../TROUBLESHOOTING.md)** - Problem resolution

## Quick Demo Commands

```bash
# Test basic connectivity
python -c "
import requests
import os
url = os.getenv('LITELLM_URL', 'https://your-litellm-route')
key = os.getenv('LITELLM_API_KEY', 'sk-your-key')
response = requests.get(f'{url}/health')
print(f'Health check: {response.status_code}')
response = requests.get(f'{url}/models', headers={'Authorization': f'Bearer {key}'})
print(f'Models: {len(response.json().get(\"data\", []))} available')
"

# Run all demos in sequence
for demo in budget failover guardrails; do
    echo "Running ${demo} demo..."
    python ${demo}_test.py
    echo "Completed ${demo} demo"
    sleep 5
done
```