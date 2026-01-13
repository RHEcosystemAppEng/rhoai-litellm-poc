# LlamaStack Client vs LiteLLM Client Demo

## Overview

This demo demonstrates that **LlamaStack** and **LiteLLM** clients can be swapped with minimal code changes because both implement the **OpenAI-compatible API interface**.

## Why This Matters

When building AI applications, vendor lock-in is a real concern. By using providers that adhere to the OpenAI API specification, you gain:

- **Flexibility**: Switch between providers without rewriting your application logic
- **Portability**: Move workloads between different infrastructure setups
- **Reduced Risk**: Avoid being locked into a single provider's ecosystem

## How It Works

Both LiteLLM and LlamaStack expose OpenAI-compatible endpoints, meaning the core API patterns are identical:

```python
# LiteLLM (via OpenAI client)
client = OpenAI(base_url="http://litellm:4000", api_key=api_key)
response = client.chat.completions.create(
    model="llama-fp8",
    messages=[{"role": "user", "content": "Hello!"}]
)

# LlamaStack
client = LlamaStackClient(base_url="http://llamastack:8321", api_key=api_key)
response = client.chat.completions.create(
    model="litellm-provider/llama-fp8",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Key Differences

| Aspect | LiteLLM | LlamaStack |
|--------|---------|------------|
| **Client Library** | `openai.OpenAI` | `llama_stack_client.LlamaStackClient` |
| **Model Naming** | Direct model name (e.g., `llama-fp8`) | Prefixed with provider (e.g., `litellm-provider/llama-fp8`) |
| **Default Port** | 4000 | 8321 |

### What Stays the Same

- `chat.completions.create()` method signature
- Message format (`[{"role": "user", "content": "..."}]`)
- Response structure
- Authentication via API key

## Running the Demo

### Using the Helm Deployment

This demo is designed to work seamlessly with the Helm deployment in this repository. When you deploy using Helm, the following services are automatically created and exposed:

1. **Deploy the stack** from the `deploy/` directory:

```bash
cd deploy
make install
```

2. **Get the service URLs** after deployment:

```bash
# Get LiteLLM URL
oc get route litellm -n litellm -o jsonpath='{.spec.host}'

# Get LlamaStack URL  
oc get route llamastack -n litellm -o jsonpath='{.spec.host}'
```

3. **Set environment variables** pointing to your deployed services:

```bash
# Use the external routes (replace with your actual cluster URLs)
export LITELLM_URL="https://litellm-litellm.apps.your-cluster.example.com"
export LLAMASTACK_URL="https://llamastack-litellm.apps.your-cluster.example.com"

# API keys from values.yaml (seed.users section)
export LITELLM_MASTER_API_KEY="master-key"
export LITELLM_API_KEY="sk-eng-user-key"
export LLAMA_STACK_API_KEY="sk-eng-user-key"

# Optional: switch between providers
export DEMO_PROVIDER="litellm"  # or "llamastack"
```

> **Note:** The Helm deployment automatically:
> - Creates LiteLLM and LlamaStack services
> - Configures LlamaStack to use LiteLLM as its backend provider
> - Sets up API keys and routes for external access
> - Generates a shared API key for LlamaStack to authenticate with LiteLLM

### Manual Setup (Without Helm)

If you're not using the Helm deployment, set the following environment variables manually:

```bash
export LITELLM_URL="http://litellm:4000"
export LLAMASTACK_URL="http://llamastack:8321"
export LITELLM_MASTER_API_KEY="your-master-key"
export LITELLM_API_KEY="your-api-key"        # Optional, will be created if not set
export LLAMA_STACK_API_KEY="your-llama-key"
```

### Execute

```bash
# Run with LiteLLM (default)
python llamastack_client_vs_llm_client.py

# Run with LlamaStack
DEMO_PROVIDER=llamastack python llamastack_client_vs_llm_client.py
```

## The `CompletionClient` Wrapper

The demo includes a `CompletionClient` class that abstracts away the minor differences between providers:

```python
client = CompletionClient(
    api_key=api_key,
    base_url=url,
    provider="litellm"  # or "llamastack"
)

# Same interface regardless of provider
response = client.completion(model="llama-fp8", prompt="Hello!")
models = client.list_models()
```

This pattern demonstrates how easily you can build provider-agnostic AI applications.

## Conclusion

By leveraging the OpenAI-compatible interface that both LiteLLM and LlamaStack provide, you can:

1. Build applications that are **provider-agnostic**
2. **Switch providers** with a simple configuration change
3. **Test locally** with one provider and **deploy to production** with another
4. **Future-proof** your application against provider changes
