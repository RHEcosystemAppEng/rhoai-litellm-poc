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
# OpenAIClientFactory - Creates OpenAI-compatible clients for any provider
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAIClientFactory:
    """
    Factory class that creates OpenAI-compatible clients for different providers.
    
    Both LiteLLM and LlamaStack expose OpenAI-compatible APIs, so this factory
    returns a client that can be used interchangeably with standard OpenAI code.
    
    The key insight: regardless of which provider you choose, you get back a client
    that works with the same API (chat.completions.create, models.list, etc.).
    """
    
    @staticmethod
    def create(
        provider: str,
        api_key: str,
        base_url: str,
        model_prefix: str | None = None
    ) -> LlamaStackClient | OpenAI:
        """
        Create an OpenAI-compatible client for the specified provider.
        
        Args:
            provider: The provider to use ("litellm" or "llamastack")
            api_key: API key for authentication
            base_url: Base URL of the provider's API
            model_prefix: Optional prefix for model names (e.g., "litellm-provider")
        
        Returns:
            An OpenAI-compatible client that can be used with standard OpenAI patterns
        
        Example:
            # Create client - either provider returns an OpenAI-compatible interface
            client = OpenAIClientFactory.create("litellm", api_key, base_url)
            
            # Use standard OpenAI API patterns - works the same for both providers!
            response = client.chat.completions.create(
                model="llama-fp8",
                messages=[{"role": "user", "content": "Hello!"}]
            )
        """
        logger.info(f"Creating OpenAI-compatible client for provider: {provider}")
        logger.info(f"  └─ Base URL: {base_url}")
        logger.info(f"  └─ API Key: {api_key[:10]}..." if api_key else "  └─ API Key: None")
        
        if provider == "litellm":
            logger.info("  └─ Using OpenAI client (LiteLLM exposes OpenAI-compatible API)")
            return OpenAI(base_url=base_url, api_key=api_key)
        elif provider == "llamastack":
            logger.info("  └─ Using LlamaStackClient (also OpenAI-compatible)")
            return LlamaStackClient(base_url=base_url, api_key=api_key)
        else:
            raise ValueError(f"Invalid provider: {provider}. Must be 'litellm' or 'llamastack'")


# ═══════════════════════════════════════════════════════════════════════════════
# LLMTester - Runs operations/tests using any OpenAI-compatible client
# ═══════════════════════════════════════════════════════════════════════════════

class LLMTester:
    """
    A test runner that works with any OpenAI-compatible client.
    
    This class demonstrates that once you have an OpenAI-compatible client,
    all operations work identically regardless of the underlying provider.
    
    The same code runs whether the client came from LiteLLM, LlamaStack,
    or even the official OpenAI API.
    """
    
    def __init__(self, client: LlamaStackClient | OpenAI, model_prefix: str = ""):
        """
        Initialize the tester with an OpenAI-compatible client.
        
        Args:
            client: Any OpenAI-compatible client (from LiteLLM, LlamaStack, etc.)
            model_prefix: Optional prefix to add to model names (e.g., "litellm-provider/")
        """
        self.client = client
        self.model_prefix = model_prefix
        logger.info("LLMTester initialized with OpenAI-compatible client")
        if model_prefix:
            logger.info(f"  └─ Model prefix: {model_prefix}")
    
    def _format_model_name(self, model: str) -> str:
        """Apply model prefix if configured."""
        if self.model_prefix:
            return f"{self.model_prefix}{model}"
        return model

    def list_models(self) -> list:
        """
        List available models from the provider.
        
        This uses the standard OpenAI models.list() API.
        """
        logger.info("Fetching available models via client.models.list()...")
        models = self.client.models.list()
        return models

    def get_model(self, model: str):
        """
        Get a specific model by name.
        
        This uses the standard OpenAI models.retrieve() API.
        """
        model_name = self._format_model_name(model)
        logger.info(f"Retrieving model info for: {model_name}")
        return self.client.models.retrieve(model_name)

    def completion(self, model: str, prompt: str):
        """
        Create a chat completion with the given model and prompt.
        
        This uses the standard OpenAI chat.completions.create() API.
        
        Args:
            model: The model to use (prefix will be applied if configured)
            prompt: The user prompt to send
        
        Returns:
            The completion response (standard OpenAI format)
        """
        model_name = self._format_model_name(model)
        messages = [{"role": "user", "content": prompt}]
        
        logger.info(f"Creating chat completion...")
        logger.info(f"  └─ Model: {model_name}")
        logger.info(f"  └─ Prompt: \"{prompt[:50]}{'...' if len(prompt) > 50 else ''}\"")
        
        response = self.client.chat.completions.create(model=model_name, messages=messages)
        
        # Log response info
        if hasattr(response, 'choices') and response.choices:
            content = response.choices[0].message.content
            logger.info(f"  └─ Response received ({len(content)} characters)")
        
        return response

    def run_all_tests(self, model: str, prompt: str = "Hello! Please respond with a brief greeting."):
        """
        Run a suite of tests to verify the client is working correctly.
        
        Args:
            model: The model to test with
            prompt: The test prompt to use
        
        Returns:
            dict with test results
        """
        results = {
            "list_models": None,
            "completion": None,
            "errors": []
        }
        
        # Test 1: List models
        try:
            logger.info("Test 1: Listing models...")
            results["list_models"] = self.list_models()
            logger.info("  ✓ list_models passed")
        except Exception as e:
            logger.error(f"  ✗ list_models failed: {e}")
            results["errors"].append(f"list_models: {e}")
        
        # Test 2: Chat completion
        try:
            logger.info("Test 2: Creating chat completion...")
            results["completion"] = self.completion(model, prompt)
            logger.info("  ✓ completion passed")
        except Exception as e:
            logger.error(f"  ✗ completion failed: {e}")
            results["errors"].append(f"completion: {e}")
        
        return results


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
    1. Both LiteLLM and LlamaStack return OpenAI-compatible clients
    2. The SAME test code runs identically on either provider
    3. Separation of concerns: client creation vs operations
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

    # ── Step 4: Create OpenAI-Compatible Client (via Factory) ────────────────
    print_section("Step 4: Creating OpenAI-Compatible Client")
    
    logger.info("Using OpenAIClientFactory to create a client...")
    logger.info("  └─ Both providers return OpenAI-compatible clients!")
    
    # Determine configuration based on provider
    if PROVIDER == "litellm":
        api_key = lite_llm_api_key
        base_url = LITELLM_URL
        model_prefix = ""  # LiteLLM uses model names directly
    elif PROVIDER == "llamastack":
        api_key = LLAMA_STACK_API_KEY
        base_url = LLAMASTACK_URL
        model_prefix = "litellm-provider/"  # LlamaStack requires provider prefix
    else:
        raise ValueError(f"Invalid provider: {PROVIDER}")
    
    # Create the OpenAI-compatible client using the factory
    client = OpenAIClientFactory.create(
        provider=PROVIDER,
        api_key=api_key,
        base_url=base_url
    )
    logger.info("  ✓ OpenAI-compatible client created successfully!")

    # ── Step 5: Create Tester with the Client ────────────────────────────────
    print_section("Step 5: Initializing LLMTester")
    
    logger.info("Creating LLMTester with the OpenAI-compatible client...")
    logger.info("  └─ LLMTester works with ANY OpenAI-compatible client")
    logger.info("  └─ Same test code runs on LiteLLM, LlamaStack, or OpenAI!")
    
    tester = LLMTester(client=client, model_prefix=model_prefix)
    logger.info("  ✓ LLMTester ready!")

    # ── Step 6: Run Tests ────────────────────────────────────────────────────
    print_section("Step 6: Running Tests with LLMTester")
    
    # Test: List models
    logger.info("Test: Listing available models...")
    logger.info("  └─ Using standard OpenAI API: client.models.list()")
    models = tester.list_models()
    
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

    # Test: Chat completion
    print_section("Step 7: Testing Chat Completion")
    
    prompt = "Hello! Please respond with a brief greeting and tell me what you are."
    logger.info("Test: Creating chat completion...")
    logger.info("  └─ Using standard OpenAI API: client.chat.completions.create()")
    logger.info(f"  └─ Prompt: \"{prompt}\"")
    
    response = tester.completion(model="llama-fp8", prompt=prompt)
    
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
    logger.info("  1. OpenAIClientFactory creates OpenAI-compatible clients for any provider")
    logger.info("  2. LLMTester runs the SAME code on any OpenAI-compatible client")
    logger.info("  3. Separation of concerns: client creation (Factory) vs operations (Tester)")
    logger.info("  4. Switching providers = just change the factory call, tests stay the same!")
    logger.info("")
    logger.info("Architecture:")
    logger.info("  ┌─────────────────────┐")
    logger.info("  │ OpenAIClientFactory │ ──▶ Creates OpenAI-compatible client")
    logger.info("  └─────────────────────┘")
    logger.info("            │")
    logger.info("            ▼")
    logger.info("  ┌─────────────────────┐")
    logger.info("  │     LLMTester       │ ──▶ Runs tests with that client")
    logger.info("  └─────────────────────┘")
    logger.info("")
    logger.info("Try running with DEMO_PROVIDER=llamastack to see the same tests")
    logger.info("work with LlamaStack instead!")


if __name__ == "__main__":
    main()
