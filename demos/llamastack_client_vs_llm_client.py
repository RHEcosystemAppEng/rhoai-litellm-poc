# This file demonstrates the difference between using the LlamaStack client and the LiteLLM client
# Note this is intended to work with a deployed LiteLLM and LlamaStack server.
# You can use the helm chart to deploy both litellm and llamastack. This comes with some 
# api keys that can be found in the values.yaml file. 

from llama_stack_client import LlamaStackClient
from openai import OpenAI
import os
import logging
import requests
import sys

# Configure colored logging format
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging():
    """Configure logging with colored output and clear formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(
        fmt='%(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration from environment variables
# ═══════════════════════════════════════════════════════════════════════════════

LLAMASTACK_URL = os.getenv("LLAMASTACK_URL", "http://llamastack:8321")
LITELLM_URL = os.getenv("LITELLM_URL", "http://litellm:4000")

# LiteLLM Master Key is used for managing API keys and users like an admin key.
# We will use it to create a new API key for the demo.
LITELLM_MASTER_API_KEY = os.getenv("LITELLM_MASTER_API_KEY")
# LiteLLM API Key is used for the actual API calls.
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")

# LlamaStack API Key is used for the actual API calls.
LLAMA_STACK_API_KEY = os.getenv("LLAMA_STACK_API_KEY")


# ═══════════════════════════════════════════════════════════════════════════════
# CompletionClient - Unified interface for LiteLLM and LlamaStack
# ═══════════════════════════════════════════════════════════════════════════════

class CompletionClient:
    """
    A unified client for interacting with either LiteLLM or LlamaStack providers.
    
    This demonstrates that both providers use OpenAI-compatible interfaces,
    allowing you to swap between them with minimal code changes.
    """
    provider: str
    api_key: str
    base_url: str
    client: LlamaStackClient | OpenAI

    def __init__(
        self,
        api_key: str,
        base_url: str,
        provider: str = "litellm"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.provider = provider
        logger.info(f"Initializing CompletionClient for provider: {provider}")
        logger.info(f"  └─ Base URL: {base_url}")
        logger.info(f"  └─ API Key: {api_key[:10]}..." if api_key else "  └─ API Key: None")
        self.client = self._get_client()

    def _get_client(self) -> LlamaStackClient | OpenAI:
        """Create the appropriate client based on the provider."""
        if self.provider == "litellm":
            logger.info("  └─ Creating OpenAI client (LiteLLM uses OpenAI-compatible API)")
            return OpenAI(base_url=self.base_url, api_key=self.api_key)
        elif self.provider == "llamastack":
            logger.info("  └─ Creating LlamaStackClient")
            return LlamaStackClient(base_url=self.base_url, api_key=self.api_key)
        else:
            raise ValueError(f"Invalid provider: {self.provider}")

    def completion(self, model: str, prompt: str) -> str:
        """Create a chat completion with the given model and prompt."""
        model_name = self._get_completion_model(model)
        messages = self._get_completion_messages(prompt)
        
        logger.info(f"Creating chat completion...")
        logger.info(f"  └─ Model: {model_name}")
        logger.info(f"  └─ Prompt: \"{prompt[:50]}{'...' if len(prompt) > 50 else ''}\"")
        
        response = self.client.chat.completions.create(model=model_name, messages=messages)
        
        # Extract the response content
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            logger.info(f"  └─ Response received ({len(content)} characters)")
        
        return response

    def _get_completion_model(self, model: str) -> str:
        """
        Get the appropriate model name for the provider.
        
        LlamaStack requires a provider prefix (e.g., 'litellm-provider/model-name'),
        while LiteLLM uses the model name directly.
        """
        if self.provider == "litellm":
            return model
        elif self.provider == "llamastack":
            prefixed = f"litellm-provider/{model}"
            logger.debug(f"  └─ LlamaStack model prefix applied: {prefixed}")
            return prefixed
        else:
            raise ValueError(f"Invalid provider: {self.provider}")

    def _get_completion_messages(self, prompt: str) -> list:
        """Convert a prompt string to a messages list."""
        return [{"role": "user", "content": prompt}]

    def list_models(self) -> list:
        """List available models from the provider."""
        logger.info("Fetching available models...")
        models = self.client.models.list()
        return models

    def get_model(self, model: str):
        """Get a specific model by name."""
        logger.info(f"Retrieving model info for: {model}")
        return self.client.models.retrieve(model)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def check_env_variables():
    """Check that required environment variables are set."""
    logger.info("Checking environment variables...")
    
    missing = []
    
    if not LITELLM_MASTER_API_KEY:
        missing.append("LITELLM_MASTER_API_KEY")
    else:
        logger.info("  ✓ LITELLM_MASTER_API_KEY is set")
        
    if not LLAMA_STACK_API_KEY:
        missing.append("LLAMA_STACK_API_KEY")
    else:
        logger.info("  ✓ LLAMA_STACK_API_KEY is set")

    if not LITELLM_API_KEY:
        logger.warning("  ⚠ LITELLM_API_KEY is not set - will create a new one")
    else:
        logger.info("  ✓ LITELLM_API_KEY is set")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info("Environment check passed!")


def create_lite_llm_api_key(master_api_key: str) -> str:
    """Create a new LiteLLM API key using the master key."""
    logger.info("Creating new LiteLLM API key...")
    logger.info(f"  └─ Endpoint: {LITELLM_URL}/key/generate")
    
    url = f"{LITELLM_URL}/key/generate"
    headers = {"Authorization": f"Bearer {master_api_key}"}
    payload = {"max_budget": 0.001, "key_alias": "test-api-key"}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    api_key = response.json()["api_key"]
    logger.info(f"  ✓ API key created: {api_key[:15]}...")
    return api_key


def print_banner():
    """Print a nice banner for the demo."""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║       LlamaStack vs LiteLLM Client Demo                                      ║
    ║       ─────────────────────────────────                                      ║
    ║                                                                              ║
    ║       This demo shows that both clients use OpenAI-compatible APIs,          ║
    ║       allowing you to swap providers with minimal code changes.              ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Main Demo
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Main entry point demonstrating LiteLLM vs LlamaStack client usage.
    
    This demo proves that:
    1. Both LiteLLM and LlamaStack use OpenAI-compatible interfaces
    2. You can swap between providers with minimal code changes
    3. The core API patterns (chat.completions.create, models.list) are identical
    """
    setup_logging()
    print_banner()
    
    # ── Step 1: Check Environment Variables ──────────────────────────────────
    print_section("Step 1: Checking Environment Variables")
    check_env_variables()
    
    # ── Step 2: Configure Provider ───────────────────────────────────────────
    print_section("Step 2: Configuring Provider")
    
    # Toggle this to switch between providers!
    PROVIDER = os.getenv("DEMO_PROVIDER", "litellm")
    logger.info(f"Selected provider: {PROVIDER}")
    logger.info("  └─ (Set DEMO_PROVIDER env var to 'llamastack' to use LlamaStack)")
    
    # ── Step 3: Setup API Key ────────────────────────────────────────────────
    print_section("Step 3: Setting Up API Key")
    
    lite_llm_api_key = LITELLM_API_KEY
    # Note you can either create a new API key or use the existing one.
    if not lite_llm_api_key:
        logger.info("No LITELLM_API_KEY found, creating a new one...")
        lite_llm_api_key = create_lite_llm_api_key(
            master_api_key=LITELLM_MASTER_API_KEY
        )
    else:
        logger.info(f"Using existing LITELLM_API_KEY: {lite_llm_api_key[:15]}...")

    # ── Step 4: Create Client ────────────────────────────────────────────────
    print_section("Step 4: Creating Client")
    
    if PROVIDER == "litellm":
        logger.info("Creating LiteLLM client...")
        logger.info("  └─ LiteLLM exposes an OpenAI-compatible API")
        logger.info("  └─ We use the standard OpenAI Python client to connect")
        client = CompletionClient(
            api_key=lite_llm_api_key,
            base_url=LITELLM_URL,
            provider="litellm"
        )
    elif PROVIDER == "llamastack":
        logger.info("Creating LlamaStack client...")
        logger.info("  └─ LlamaStack also uses OpenAI-compatible patterns")
        logger.info("  └─ The API structure is nearly identical to LiteLLM")
        client = CompletionClient(
            api_key=LLAMA_STACK_API_KEY,
            base_url=LLAMASTACK_URL,
            provider="llamastack"
        )
    else:
        raise ValueError(f"Invalid provider: {PROVIDER}")
    
    logger.info("  ✓ Client created successfully!")

    # ── Step 5: List Available Models ────────────────────────────────────────
    print_section("Step 5: Listing Available Models")
    
    logger.info("Calling client.models.list() - same API for both providers!")
    models = client.list_models()
    
    # Pretty print the models
    if hasattr(models, 'data'):
        model_list = models.data
        logger.info(f"Found {len(model_list)} models:")
        for model in model_list[:5]:  # Show first 5
            model_id = model.id if hasattr(model, 'id') else str(model)
            logger.info(f"  • {model_id}")
        if len(model_list) > 5:
            logger.info(f"  ... and {len(model_list) - 5} more")
    else:
        logger.info(f"Models: {models}")

    # ── Step 6: Create Chat Completion ───────────────────────────────────────
    print_section("Step 6: Creating Chat Completion")
    
    prompt = "Hello! Please respond with a brief greeting and tell me what you are."
    logger.info("Calling client.chat.completions.create() - same API for both providers!")
    logger.info(f"Prompt: \"{prompt}\"")
    
    response = client.completion(
        model="llama-fp8",
        prompt=prompt
    )
    
    # Extract and display the response
    if hasattr(response, 'choices') and response.choices:
        content = response.choices[0].message.content
        print(f"\n{'=' * 60}")
        print("  MODEL RESPONSE")
        print(f"{'=' * 60}")
        print(f"\n{content}\n")
        print(f"{'=' * 60}\n")
    else:
        logger.info(f"Raw response: {response}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print_section("Demo Complete!")
    
    logger.info("Key Takeaways:")
    logger.info("  1. Both LiteLLM and LlamaStack use OpenAI-compatible APIs")
    logger.info("  2. client.models.list() works the same way for both")
    logger.info("  3. client.chat.completions.create() works the same way for both")
    logger.info("  4. Switching providers requires only changing the client initialization")
    logger.info("")
    logger.info("Try running with DEMO_PROVIDER=llamastack to see the same demo")
    logger.info("work with LlamaStack instead!")


if __name__ == "__main__":
    main()
