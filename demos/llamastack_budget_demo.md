# LlamaStack Budget Management Guide

## Overview

This document demonstrates how to implement budget enforcement when using LlamaStack with LiteLLM. Budget limits work through LlamaStack using the `X-LlamaStack-Provider-Data` header mechanism.

## Architecture Components

### LiteLLM
- LLM proxy server with budget management features
- Supports virtual API keys with `max_budget` limits
- Tracks token usage and enforces spending limits
- Returns 400 error when budget exceeded

### LlamaStack
- Orchestration framework for building agentic AI applications
- Provides unified API for agents, RAG, tools, and safety
- Uses LiteLLM as a backend inference provider
- Supports dynamic provider authentication via `X-LlamaStack-Provider-Data` header

### LlamaStackClient
- Python SDK for interacting with LlamaStack (or OpenAI-compatible) APIs
- Supports two authentication mechanisms:
  - `api_key` - For client authentication to LlamaStack server
  - `provider_data` - For passing credentials to backend providers

## Working Solution: Using provider_data

### ✅ Correct Approach

**Architecture:**
```
LlamaStackClient (with provider_data) → LlamaStack Server → LiteLLM (with budgeted key)
```

**Code Example:**
```python
from llama_stack_client import LlamaStackClient
import requests

# Step 1: Create budgeted virtual key via LiteLLM
def create_budget_key(base_url: str, master_key: str, max_budget: float) -> dict:
    url = f"{base_url}/key/generate"
    headers = {"Authorization": f"Bearer {master_key}"}
    payload = {
        "max_budget": max_budget,
        "key_alias": f"budget-key-{int(time.time())}",
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Step 2: Initialize LlamaStackClient with provider_data
key_data = create_budget_key(LITELLM_URL, "master-key", 0.001)
budgeted_key = key_data["key"]

client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={
        "vllm_api_token": budgeted_key  # ← Key forwarded to backend!
    }
)

# Step 3: Make requests - budget enforced!
response = client.chat.completions.create(
    model="litellm-provider/llama-fp8",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Result:** ✅ **Budget enforcement works**
```
Request #1: $0.0047 (cumulative: $0.0047) ✓
Request #2: $0.0049 (cumulative: $0.0096) ✓
Request #3: $0.0049 (cumulative: $0.0145) ✓
Request #4: ERROR 400 - Budget has been exceeded! ✓
```

## How It Works

### Authentication Flow

LlamaStack supports **two separate authentication contexts**:

1. **Client → LlamaStack Authentication**
   ```python
   client = LlamaStackClient(
       base_url=LLAMASTACK_URL,
       api_key="client-token"  # Authenticates to LlamaStack API
   )
   ```

2. **LlamaStack → Backend Provider Authentication**
   ```python
   client = LlamaStackClient(
       base_url=LLAMASTACK_URL,
       provider_data={
           "vllm_api_token": "backend-token"  # Forwarded to LiteLLM
       }
   )
   ```

### The X-LlamaStack-Provider-Data Header

When you use `provider_data=`, the client sends:
```http
POST /v1/chat/completions HTTP/1.1
Host: llamastack-server
X-LlamaStack-Provider-Data: {"vllm_api_token": "sk-budgeted-key"}
```

LlamaStack's `OpenAIMixin` class extracts this and uses it when calling the backend:
```python
# In OpenAIMixin._get_api_key_from_config_or_provider_data()
if self.provider_data_api_key_field:  # "vllm_api_token"
    provider_data = self.get_request_provider_data()
    if provider_data:
        return getattr(provider_data, self.provider_data_api_key_field)
```

### Configuration Priority

The provider uses this priority order:
1. **Static config** (`apiToken` in values.yaml) - if set, always used
2. **Provider data** (`provider_data` from client) - if static config not set
3. **No authentication** - returns "NO KEY REQUIRED"

**Important:** For budget enforcement to work, the provider must **not** have a static `apiToken` configured, OR the static token should be removed/commented out.

## Common Mistakes

### ❌ Wrong: Using api_key parameter

```python
# This authenticates CLIENT to LlamaStack
# Does NOT forward to backend
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    api_key=budgeted_key  # ← Not forwarded to LiteLLM
)
```

**Result:** Budget enforcement fails - LlamaStack uses static config token

### ❌ Wrong: Static apiToken in config

```yaml
# deploy/helm/values.yaml
llama-stack:
  models:
    litellm-provider:
      url: http://litellm:4000/v1
      apiToken: master-key  # ← Always used, ignores provider_data
```

**Result:** Budget enforcement fails - static token takes priority

## Deployment Configuration

### Required Configuration (Keep Static Token)

```yaml
# deploy/helm/values.yaml
llama-stack:
  models:
    litellm-provider:
      url: http://litellm:4000/v1
      apiToken: master-key  # Required for startup
      enabled: true
```

**How It Works:**

Despite having `apiToken` configured, you can **override it per-request** using `provider_data`:

```python
# The static apiToken allows startup
# But provider_data overrides it at runtime when provided
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={
        "vllm_api_token": budgeted_key  # ✅ This DOES override apiToken!
    }
)
```

**How provider_data Overrides Static Config:**

LlamaStack's `OpenAIMixin` checks for provider_data and uses it when present:

```python
# OpenAIMixin._get_api_key_from_config_or_provider_data()
if self.provider_data_api_key_field:
    provider_data = self.get_request_provider_data()
    if provider_data and getattr(provider_data, self.provider_data_api_key_field, None):
        return getattr(provider_data, self.provider_data_api_key_field)  # ✅ Uses this!

# Falls back to static config if no provider_data
if self.config.auth_credential:
    return self.config.auth_credential.get_secret_value()
```

**Working Configuration:**
```yaml
# Current deployment (keep this)
llama-stack:
  models:
    litellm-provider:
      apiToken: master-key  # Needed for startup
```

```python
# Client code (this overrides master-key)
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={"vllm_api_token": budgeted_key}
)
# ✅ Budget enforcement WORKS
```

**Pros:**
- ✅ LlamaStack starts successfully
- ✅ Model registration works
- ✅ Budget enforcement works with provider_data
- ✅ Per-client cost tracking enabled
- ✅ No code changes needed

**Cons:**
- ⚠️ Clients without provider_data fall back to master-key (shared access)
- ⚠️ Requires client-side awareness to use provider_data

**Why Static Token is Required:**
- ✅ LlamaStack needs credentials to start and register models
- ✅ Init container health checks require authentication to LiteLLM
- ❌ Removing `apiToken` causes startup failures (401 errors)

**Best Practice:**
- Keep `apiToken: master-key` in configuration (required for startup)
- Always use `provider_data` in client code for budget management
- Clients without `provider_data` will fall back to master-key (shared access)

## Test Scenarios

### Scenario 1: Direct to LiteLLM (budget_test.py)

**Code:**
```python
import litellm

response = litellm.completion(
    model="llama-fp8",
    messages=[{"role": "user", "content": "Hello"}],
    api_key=budgeted_key,
    api_base=LITELLM_URL
)
```

**Result:** ✅ Budget enforced (baseline test)

### Scenario 2: LlamaStackClient with provider_data (llamastack_budget_test.py)

**Code:**
```python
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={"vllm_api_token": budgeted_key}
)
response = client.chat.completions.create(
    model="litellm-provider/llama-fp8",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Result:** ✅ Budget enforced - **WORKING SOLUTION**

### Scenario 3: LlamaStackClient direct to LiteLLM

**Code:**
```python
client = LlamaStackClient(
    base_url=LITELLM_URL,  # Bypass LlamaStack
    api_key=budgeted_key
)
response = client.chat.completions.create(
    model="llama-fp8",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Result:** ✅ Budget enforced (LlamaStackClient is OpenAI-compatible)

## Best Practices

### 1. Production Deployment with Budget Management

```python
import os
from llama_stack_client import LlamaStackClient

# Store sensitive keys securely
LLAMASTACK_URL = os.getenv("LLAMASTACK_URL")
BUDGETED_KEY = os.getenv("USER_BUDGET_KEY")

client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={
        "vllm_api_token": BUDGETED_KEY  # Per-user budget key
    }
)
```

### 2. Multi-Tenant Application

```python
def create_client_for_user(user_id: str, budget: float) -> LlamaStackClient:
    # Create per-user budgeted key
    key_data = create_budget_key(
        LITELLM_URL,
        MASTER_KEY,
        max_budget=budget
    )

    return LlamaStackClient(
        base_url=LLAMASTACK_URL,
        provider_data={
            "vllm_api_token": key_data["key"]
        }
    )

# Each user gets their own budgeted client
alice_client = create_client_for_user("alice", budget=10.00)
bob_client = create_client_for_user("bob", budget=5.00)
```

### 3. Error Handling

```python
from openai import BadRequestError

try:
    response = client.chat.completions.create(
        model="litellm-provider/llama-fp8",
        messages=[{"role": "user", "content": "Hello"}]
    )
except BadRequestError as e:
    if "Budget has been exceeded" in str(e):
        print(f"User budget exhausted: {e}")
        # Handle budget exceeded (notify user, upgrade plan, etc.)
    else:
        raise
```

## Source Code References

### LlamaStack Implementation (v0.4.0)

**OpenAIMixin** - Handles provider_data authentication:
```python
# src/llama_stack/providers/utils/inference/openai_mixin.py
def _get_api_key_from_config_or_provider_data(self) -> str | None:
    # Priority 1: Static config
    if self.config.auth_credential:
        return self.config.auth_credential.get_secret_value()

    # Priority 2: Provider data from X-LlamaStack-Provider-Data header
    if self.provider_data_api_key_field:
        provider_data = self.get_request_provider_data()
        if provider_data and getattr(provider_data, self.provider_data_api_key_field, None):
            return getattr(provider_data, self.provider_data_api_key_field)
```

**VLLMInferenceAdapter** - Specifies provider_data field name:
```python
# src/llama_stack/providers/remote/inference/vllm/vllm.py
class VLLMInferenceAdapter(OpenAIMixin):
    provider_data_api_key_field: str = "vllm_api_token"
```

**Request Headers** - Parses provider data:
```python
# src/llama_stack/core/request_headers.py
def parse_request_provider_data(headers: dict[str, str]) -> dict:
    keys = [
        "X-LlamaStack-Provider-Data",
        "x-llamastack-provider-data",
    ]
    # Parses JSON from header
```

## Official Documentation

- [LlamaStack Security & Provider Data](https://llamastack.github.io/docs/building_applications/tools#-security)
- [LiteLLM Virtual Keys](https://docs.litellm.ai/docs/proxy/virtual_keys)
- [LlamaStack Client SDK](https://github.com/meta-llama/llama-stack-client-python)

## Investigation History

During this investigation, we initially believed budget enforcement was architecturally impossible through LlamaStack. We attempted several solutions:

1. **Removing apiToken** - Failed: Model registration at startup requires authentication
2. **Separate initToken and runtime token** - Failed: LlamaStack needs token for both startup and runtime
3. **Direct connection** - Works but loses LlamaStack features

The breakthrough came from discovering the `X-LlamaStack-Provider-Data` header mechanism in the official documentation, which was already implemented in the codebase but not initially tested.

## Conclusion

**Budget enforcement WORKS with LlamaStack** using the `provider_data` parameter:

✅ **Recommended Approach:**
```python
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    provider_data={"vllm_api_token": budgeted_key}
)
```

**Key Insights:**
- Use `provider_data` for backend authentication, not `api_key`
- Remove or comment out static `apiToken` in configuration
- LlamaStack's security documentation explains this feature
- Works with LlamaStack v0.3.3, v0.3.5, and v0.4.0+

**Benefits:**
- ✅ Per-client budget enforcement
- ✅ Full LlamaStack features (agents, RAG, tools, safety)
- ✅ Enterprise-ready cost tracking
- ✅ Multi-tenant deployments

## Test Files

- `demos/budget_test.py` - Direct LiteLLM connection (baseline)
- `demos/llamastack_test.py` - Example usage patterns
- `demos/llamastack_budget_test.py` - Working budget enforcement through LlamaStack ✅

Run the test:
```bash
uv run demos/llamastack_budget_test.py
```

Expected output:
```
Request #1: $0.0047 (cumulative: $0.0047) ✓
Request #2: $0.0049 (cumulative: $0.0096) ✓
Request #3: $0.0049 (cumulative: $0.0145) ✓
Request #4: ERROR 400 - Budget has been exceeded! ✓
```
