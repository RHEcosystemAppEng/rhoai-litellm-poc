from llama_stack_client import LlamaStackClient

LLAMASTACK_URL = "https://llamastack-hacohen-llmlite.apps.ai-dev02.kni.syseng.devcluster.openshift.com"
LITELLM_URL = "https://litellm-hacohen-llmlite.apps.ai-dev02.kni.syseng.devcluster.openshift.com"

# Client with LiteLLM as backend
lite_client = LlamaStackClient(
    base_url=LITELLM_URL,  # Your LiteLLM URL
    api_key="master-key",
)

# Client with Llamastack server configured with LiteLLM as backend
llama_stack_client = LlamaStackClient(base_url=LLAMASTACK_URL)

# 1. List available models (Proves LiteLLM is forwarding the model list)
models = lite_client.models.list()
print("Available Models:", models)
print("Total Available Models:", len(models))


# 2. Run an Inference Call
response = lite_client.chat.completions.create(
    model="llama3",  # "llama-fp8", # LiteLLM maps this to your local Llama 3
    messages=[{"role": "user", "content": "Hello! Are you compatible with Llama Stack?"}],
)

print("\nResponse:", response.choices[0].message.content, "\n")

# 1. List available models (Proves LiteLLM is forwarding the model list)
models = llama_stack_client.models.list()
print("Available Models:", models)
print("Total Available Models:", len(models))


# 2. Run an Inference Call
response = llama_stack_client.chat.completions.create(
    model="litellm-provider/llama-fp8",  # "litellm-provider/llama-fp8", # LiteLLM maps this to your local Llama 3
    messages=[{"role": "user", "content": "Hello! Are you compatible with Llama Stack?"}],
)

print("\nResponse:", response.choices[0].message.content)
