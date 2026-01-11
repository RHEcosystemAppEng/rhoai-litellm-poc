# LlamaStack Budget Management Investigation

## Overview

This document summarizes our investigation into budget enforcement when using LlamaStack with LiteLLM. We tested whether budget limits (via LiteLLM virtual keys) work when requests flow through the LlamaStack orchestration layer.

## Architecture Components

### LiteLLM
- LLM proxy server with budget management features
- Supports virtual API keys with `max_budget` limits
- Tracks token usage and enforces spending limits
- Returns 400 error when budget exceeded

### LlamaStack
- Orchestration framework for building agentic AI applications
- Provides unified API for agents, RAG, tools, and safety
- Can use LiteLLM as a backend inference provider
- Configured via YAML with static provider credentials

### LlamaStackClient
- Python SDK for interacting with LlamaStack (or OpenAI-compatible) APIs
- Can connect to either LlamaStack server OR directly to LiteLLM
- Supports passing API keys for authentication

## Test Scenarios

### Scenario 1: Direct Connection (budget_test.py)
**Architecture:**
```
Python Script → LiteLLM (with budgeted key)
```

**Configuration:**
- Creates virtual key with `max_budget: $0.001`
- Uses `litellm.completion()` with the budgeted key
- Sends requests until budget exceeded

**Result:** ✅ **Budget enforcement works**
- Multiple successful requests
- Budget exceeded error after cumulative spend > $0.001
- Error message: `"Budget has been exceeded! Current cost: 0.00147, Max budget: 0.001"`

### Scenario 2: Through LlamaStack Server (initial attempt)
**Architecture:**
```
LlamaStackClient → LlamaStack Server → LiteLLM
```

**Configuration:**
- LlamaStack configured with static `apiToken: master-key` in ConfigMap
- Client creates budgeted key and initializes `LlamaStackClient` with it
- Connects to LlamaStack server URL

**Result:** ❌ **Budget enforcement DOES NOT work**
- Requests continue infinitely without budget enforcement
- LlamaStack uses its configured `apiToken: master-key` for all backend requests
- Client-provided API keys are ignored by LlamaStack server

**Evidence:**
```python
# Test with partial/invalid key
llamastack_client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    api_key=api_key[:5]  # Only first 5 characters
)
# Requests STILL succeed - proves api_key is unused
```

**Log Analysis:**
```
# Working (budget_test.py):
10.130.6.55 - - [11/Jan/2026] "POST /chat/completions HTTP/1.1" 400
# Requester IP: User's client
# Response: 400 (Budget exceeded)

# Not Working (llamastack_budget_test.py):
10.129.6.217 - - [11/Jan/2026] "POST /v1/chat/completions HTTP/1.1" 200
# Requester IP: LlamaStack pod
# Response: 200 (Always succeeds with master-key)
```

### Scenario 3: LlamaStackClient Direct to LiteLLM (final test)
**Architecture:**
```
LlamaStackClient → LiteLLM (with budgeted key)
```

**Configuration:**
- Creates virtual key with `max_budget: $0.001`
- LlamaStackClient connects directly to `LITELLM_URL` (not LlamaStack server)
- Passes budgeted key via `api_key=` parameter

**Result:** ✅ **Budget enforcement works perfectly**
```
Request #1: $0.005100 (cumulative: $0.005100)
Request #2: $0.004700 (cumulative: $0.009800)
Request #3: $0.004900 (cumulative: $0.014700)
Request #4: ERROR 400 - Budget has been exceeded!
```

## Key Findings

### 1. LlamaStack Server Architecture Limitation

The LlamaStack server uses a **static service account token** configured in its provider settings:

```yaml
# deploy/helm/values.yaml
llama-stack:
  models:
    litellm-provider:
      url: http://litellm:4000/v1
      apiToken: master-key  # Static token used for ALL requests
```

This token is used for:
- **Startup**: Registering models via `/v1/models` endpoint
- **Runtime**: All inference requests to LiteLLM backend

There is **no mechanism** in LlamaStack to:
- Pass through client-provided API keys to backend providers
- Use different tokens for different clients
- Support per-request authentication to backends

### 2. LlamaStackClient Library Works Fine

The `LlamaStackClient` Python library **does** support API keys and works correctly with budget enforcement when pointed directly at LiteLLM:

```python
# This works for budget enforcement
client = LlamaStackClient(
    base_url=LITELLM_URL,      # Point directly at LiteLLM
    api_key=budgeted_key        # Use budgeted virtual key
)
```

The library implements the OpenAI-compatible API and properly sends the `Authorization: Bearer <api_key>` header.

### 3. The Problem is the LlamaStack Server

The issue is specific to the **LlamaStack server** implementation, which:
- Acts as an orchestration layer between clients and backends
- Manages its own authentication to backend services
- Uses static provider credentials from its configuration
- Does not support API key passthrough

## Attempted Solutions

### Solution 1: Remove apiToken from Config
**Approach:** Remove `apiToken` from LlamaStack configuration to force passthrough

**Result:** ❌ Failed
- LlamaStack pod fails to start
- Error: `401 Unauthorized` when trying to register models
- LlamaStack requires a token to call LiteLLM's `/v1/models` during startup

### Solution 2: Separate Init and Runtime Tokens
**Approach:** Use `initToken` for health checks, no token for runtime

**Result:** ❌ Failed
- Created custom Helm templates to separate `initToken` from `apiToken`
- Init container used `initToken` for health checks
- Runtime config had no `apiToken`
- LlamaStack failed to start - needs token for model registration

**Code Changes Made (then reverted):**
- Created `llamastack-configmap.yaml` with conditional apiToken
- Created `llamastack-deployment.yaml` with initToken for init container
- Added `llamastackEnabled` flag to values.yaml
- All changes reverted after confirming architectural limitation

### Solution 3: Direct Connection (Working!)
**Approach:** Use LlamaStackClient library but connect directly to LiteLLM

**Result:** ✅ **Works perfectly**
```python
client = LlamaStackClient(
    base_url=LITELLM_URL,  # Bypass LlamaStack server
    api_key=budgeted_key   # Use budgeted virtual key
)
```

## Recommendations

### For Budget Management

If you need budget enforcement, you have two options:

**Option A: Use LiteLLM Directly**
```python
import litellm

response = litellm.completion(
    model="llama-fp8",
    messages=[{"role": "user", "content": "Hello"}],
    api_key=budgeted_key,
    api_base=LITELLM_URL
)
```

**Option B: Use LlamaStackClient with LiteLLM URL**
```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(
    base_url=LITELLM_URL,  # Point to LiteLLM, not LlamaStack
    api_key=budgeted_key
)
response = client.chat.completions.create(
    model="llama-fp8",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Both options work identically** - they both bypass the LlamaStack server and connect directly to LiteLLM.

### For LlamaStack Features

If you need LlamaStack's orchestration features (agents, RAG, tools, safety):

```python
client = LlamaStackClient(
    base_url=LLAMASTACK_URL  # Use LlamaStack server
)
# Note: Budget enforcement will NOT work
# All requests use the server's master-key
```

**Trade-off:** You get LlamaStack features but lose budget management.

### Future Enhancement

To support budget enforcement through LlamaStack, the upstream project would need to:

1. **Add API Key Passthrough**
   - Accept client API keys via request headers
   - Forward them to backend providers instead of using static credentials
   - Support per-request authentication

2. **Dynamic Provider Credentials**
   - Allow runtime override of provider `apiToken`
   - Support credential injection from request context
   - Maintain backward compatibility with static tokens

This would require changes to the LlamaStack core implementation and is beyond the scope of configuration changes.

## Conclusion

**Budget enforcement is architecturally impossible when using the LlamaStack server** because:

1. LlamaStack uses static service account credentials for backend providers
2. Client-provided API keys are not forwarded to backends
3. No passthrough mechanism exists in the current implementation

**Budget enforcement works perfectly when:**
- Connecting directly to LiteLLM (bypassing LlamaStack server)
- Using either `litellm.completion()` or `LlamaStackClient` with `base_url=LITELLM_URL`

**Recommendation:** For applications requiring budget management, connect directly to LiteLLM. For applications needing LlamaStack's orchestration features, accept that budget enforcement is not available and use other access control mechanisms.

## Test Files

- `demos/budget_test.py` - Direct LiteLLM connection (works ✅)
- `demos/llamastack_test.py` - Example of both connection patterns
- `demos/llamastack_budget_test.py` - LlamaStackClient with budgeted key (works when pointing to LiteLLM ✅)

## Configuration Files

- `deploy/helm/values.yaml` - LlamaStack configuration with static `apiToken: master-key`
- LlamaStack ConfigMap `run-config` - Contains provider configuration including `api_token`

## Additional Evidence

### Network Traffic Analysis
```
# Through LlamaStack Server:
Client → LlamaStack (any key or no key) → LiteLLM (always master-key)

# Direct to LiteLLM:
Client (budgeted key) → LiteLLM (budgeted key)
```

### Token Usage Test
```python
# Proof that LlamaStack ignores client API keys:
client = LlamaStackClient(
    base_url=LLAMASTACK_URL,
    api_key="sk-12345"  # Invalid/partial key
)
response = client.chat.completions.create(...)  # Still works!
```

This proves the `api_key` parameter is accepted by the client library but not used by the LlamaStack server.
