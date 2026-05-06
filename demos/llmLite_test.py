import litellm
import requests

# Configuration - import from centralized config
from config import LITELLM_BASE_URL, LITELLM_API_KEY, DEFAULT_LITELLM_MODEL


if __name__ == "__main__":
    # Print configuration
    print("LiteLLM Test Configuration:")
    print("=" * 50)
    print(f"LiteLLM URL: {LITELLM_BASE_URL}")
    print(f"Default Model: {DEFAULT_LITELLM_MODEL}")
    print("=" * 50)

    # List available models
    models_url = f"{LITELLM_BASE_URL}/models"
    headers = {"Authorization": f"Bearer {LITELLM_API_KEY}"}

    try:
        response = requests.get(models_url, headers=headers)
        models = response.json()

        print("Available models:")
        for model in models["data"]:
            print(f"  - {model['id']}")
    except Exception as e:
        print(f"Error fetching models: {e}")

    # Test completion
    try:
        response = litellm.completion(
            model="openai/llama-fp8",
            messages=[
                {"role": "user", "content": "What is the capital of France? Answer in one sentence."}
            ],
            api_base=LITELLM_BASE_URL,
            api_key=LITELLM_API_KEY,
        )

        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"Error with completion: {e}")
        print("This is expected if using dummy configuration values.")
