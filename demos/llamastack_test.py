from llama_stack_client import LlamaStackClient

# Configuration - import from centralized config
from config import LLAMASTACK_BASE_URL, LITELLM_BASE_URL, LITELLM_API_KEY, DEFAULT_LITELLM_MODEL, DEFAULT_LLAMASTACK_MODEL, print_config

# Print configuration at startup
print("LlamaStack Integration Test Configuration:")
print("=" * 60)
print(f"LlamaStack URL: {LLAMASTACK_BASE_URL}")
print(f"LiteLLM URL: {LITELLM_BASE_URL}")
print(f"LiteLLM Model: {DEFAULT_LITELLM_MODEL}")
print(f"LlamaStack Model: {DEFAULT_LLAMASTACK_MODEL}")
print("=" * 60)

LLAMASTACK_URL = LLAMASTACK_BASE_URL
LITELLM_URL = LITELLM_BASE_URL

# Client with LiteLLM as backend
lite_client = LlamaStackClient(
    base_url=LITELLM_URL,  # Your LiteLLM URL
    api_key=LITELLM_API_KEY,
)

# Client with Llamastack server configured with LiteLLM as backend
llama_stack_client = LlamaStackClient(base_url=LLAMASTACK_URL)

# 1. List available models (Proves LiteLLM is forwarding the model list)
models = lite_client.models.list()
print("Available Models:", models)
print("Total Available Models:", len(models))


# 2. Run an Inference Call
response = lite_client.chat.completions.create(
    model=DEFAULT_LITELLM_MODEL,  # Use configured model
    messages=[{"role": "user", "content": "Hello! Are you compatible with Llama Stack?"}],
)

print("\nResponse:", response.choices[0].message.content, "\n")

# 1. List available models (Proves LiteLLM is forwarding the model list)
models = llama_stack_client.models.list()
print("Available Models:", models)
print("Total Available Models:", len(models))


# 2. Run an Inference Call
response = llama_stack_client.chat.completions.create(
    model=DEFAULT_LLAMASTACK_MODEL,  # Use configured model
    messages=[{"role": "user", "content": "Hello! Are you compatible with Llama Stack?"}],
)

print("\nResponse:", response.choices[0].message.content)
