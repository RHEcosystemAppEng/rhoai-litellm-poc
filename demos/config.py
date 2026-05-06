"""
Shared configuration for LiteLLM and LlamaStack demos.

This module provides centralized configuration for connecting to LiteLLM and LlamaStack
services deployed on OpenShift/Kubernetes.
"""

import os

# =============================================================================
# LiteLLM Configuration
# =============================================================================

# LiteLLM API URL - set via environment variable or use default
# When running inside the cluster, use the service URL
# When running outside, use the route URL (get with: oc get route litellm -o jsonpath='{.spec.host}')
LITELLM_BASE_URL = os.environ.get(
    "LITELLM_BASE_URL",
    "https://litellm-api-route.apps.example.cluster.local",  # Dummy cluster URL
    # Original: "https://litellm-hacohen-llmlite.apps.ai-dev02.kni.syseng.devcluster.openshift.com"
)

# LiteLLM Master Key for admin operations
LITELLM_MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY", "master-key")

# LiteLLM API Key for standard operations
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "demo-api-key")

# =============================================================================
# LlamaStack Configuration
# =============================================================================

# LlamaStack API URL - set via environment variable or use default
# When running inside the cluster, use the service URL
# When running outside, use the route URL (get with: oc get route llamastack -o jsonpath='{.spec.host}')
LLAMASTACK_BASE_URL = os.environ.get(
    "LLAMASTACK_BASE_URL",
    "https://llamastack-api-route.apps.example.cluster.local",  # Dummy cluster URL
    # Original: "https://llamastack-hacohen-llmlite.apps.ai-dev02.kni.syseng.devcluster.openshift.com"
)

# =============================================================================
# Model Configurations
# =============================================================================

# Default models to use in demos
DEFAULT_LITELLM_MODEL = os.environ.get("DEFAULT_LITELLM_MODEL", "llama3")
DEFAULT_LLAMASTACK_MODEL = os.environ.get("DEFAULT_LLAMASTACK_MODEL", "litellm-provider/llama3")

# Model configurations for different providers
OLLAMA_CONFIG = {
    "provider": "ollama",
    "model": "llama3",
    "api_base": "http://ollama-service:11434",  # Generic service name
    # Original: Used hardcoded URLs in individual demo files
}

LLAMA_FP8_CONFIG = {
    "provider": "openai",  # vLLM is OpenAI-compatible
    "model": "openai/llama-fp8",
    "custom_host": os.environ.get("LLAMA_FP8_SERVICE_HOST", "http://llama-fp8-service:8080"),  # Generic service name
    # Original: http://llama-fp8-predictor.hacohen-llmlite.svc.cluster.local:8080/v1
}

# =============================================================================
# Namespace Configuration
# =============================================================================

# Kubernetes namespaces
LITELLM_NAMESPACE = os.environ.get("LITELLM_NAMESPACE", "litellm")
LLMD_NAMESPACE = os.environ.get("LLMD_NAMESPACE", "llmd")

# =============================================================================
# Internal Service Configuration
# =============================================================================

# Internal cluster services (when running inside Kubernetes)
INTERNAL_LITELLM_URL = f"http://litellm.{LITELLM_NAMESPACE}.svc.cluster.local:4000"
INTERNAL_LLAMASTACK_URL = f"http://llamastack.{LITELLM_NAMESPACE}.svc.cluster.local:8001"

# =============================================================================
# Demo-Specific Settings
# =============================================================================

# Budget demo settings
BUDGET_DEMO_CONFIG = {
    "max_budget": 0.001,  # Very small budget for testing
    "model": DEFAULT_LITELLM_MODEL,
    "test_message": "Say 'hello' in one word.",
}

# Failover demo settings
FAILOVER_DEMO_CONFIG = {
    "primary_model": "llama-fp8",
    "fallback_model": "llama3",
    "test_message": "Hello, this is a failover test.",
}

# Guardrails demo settings
GUARDRAILS_DEMO_CONFIG = {
    "safety_model": "llamaguard-3-8b",
    "test_model": DEFAULT_LITELLM_MODEL,
    "safe_message": "Tell me about the weather.",
    "unsafe_message": "How to make explosives?",
}

# =============================================================================
# Default Settings
# =============================================================================

# Cache settings
CACHE_MAX_AGE = 300  # seconds (5 minutes)

# Request timeout settings
REQUEST_TIMEOUT = 30  # seconds

# =============================================================================
# Helper Functions
# =============================================================================


def get_litellm_config() -> dict:
    """
    Get LiteLLM configuration for API calls.

    Returns:
        Dictionary with base_url, api_key, and other settings
    """
    return {
        "base_url": LITELLM_BASE_URL,
        "api_key": LITELLM_API_KEY,
        "master_key": LITELLM_MASTER_KEY,
        "timeout": REQUEST_TIMEOUT,
    }


def get_llamastack_config() -> dict:
    """
    Get LlamaStack configuration for API calls.

    Returns:
        Dictionary with base_url and other settings
    """
    return {
        "base_url": LLAMASTACK_BASE_URL,
        "timeout": REQUEST_TIMEOUT,
    }


def get_demo_config(demo_name: str) -> dict:
    """
    Get configuration for a specific demo.

    Args:
        demo_name: One of "budget", "failover", "guardrails"

    Returns:
        Demo-specific configuration dictionary
    """
    demos = {
        "budget": BUDGET_DEMO_CONFIG,
        "failover": FAILOVER_DEMO_CONFIG,
        "guardrails": GUARDRAILS_DEMO_CONFIG,
    }
    return demos.get(demo_name, {})


def validate_configuration():
    """
    Validate the current configuration and warn about potential issues.

    Returns:
        List of validation warnings/errors
    """
    warnings = []

    # Check for dummy/example values that need to be replaced
    if "example.cluster.local" in LITELLM_BASE_URL:
        warnings.append("⚠️  LiteLLM URL contains example domain - set LITELLM_BASE_URL environment variable")

    if "example.cluster.local" in LLAMASTACK_BASE_URL:
        warnings.append("⚠️  LlamaStack URL contains example domain - set LLAMASTACK_BASE_URL environment variable")

    if LITELLM_MASTER_KEY == "master-key":
        warnings.append("ℹ️  Using default master key - set LITELLM_MASTER_KEY for production")

    if LITELLM_API_KEY == "demo-api-key":
        warnings.append("ℹ️  Using default API key - set LITELLM_API_KEY for production")

    # Check for localhost usage (might indicate development vs production confusion)
    for service_name, url in [
        ("LiteLLM", LITELLM_BASE_URL),
        ("LlamaStack", LLAMASTACK_BASE_URL),
    ]:
        if "localhost" in url:
            warnings.append(f"⚠️  {service_name} uses localhost - ensure port-forwarding is active or use service names")

    # Check for proper HTTPS usage
    for service_name, url in [
        ("LiteLLM", LITELLM_BASE_URL),
        ("LlamaStack", LLAMASTACK_BASE_URL),
    ]:
        if not url.startswith(("http://", "https://")):
            warnings.append(f"⚠️  {service_name} URL should start with http:// or https://")

    return warnings


def print_config():
    """Print current configuration for debugging."""
    print("=" * 70)
    print("LiteLLM + LlamaStack Demo Configuration")
    print("=" * 70)
    print(f"LiteLLM URL: {LITELLM_BASE_URL}")
    print(f"LlamaStack URL: {LLAMASTACK_BASE_URL}")
    print(f"LiteLLM Namespace: {LITELLM_NAMESPACE}")
    print(f"LLM-D Namespace: {LLMD_NAMESPACE}")
    print("\nDefault Models:")
    print(f"  - LiteLLM Model: {DEFAULT_LITELLM_MODEL}")
    print(f"  - LlamaStack Model: {DEFAULT_LLAMASTACK_MODEL}")
    print("\nInternal Services:")
    print(f"  - LiteLLM Internal: {INTERNAL_LITELLM_URL}")
    print(f"  - LlamaStack Internal: {INTERNAL_LLAMASTACK_URL}")
    print("\nDemo Configurations:")
    print(f"  - Budget Demo: max_budget=${BUDGET_DEMO_CONFIG['max_budget']}")
    print(f"  - Failover Demo: {FAILOVER_DEMO_CONFIG['primary_model']} → {FAILOVER_DEMO_CONFIG['fallback_model']}")
    print(f"  - Guardrails Demo: safety_model={GUARDRAILS_DEMO_CONFIG['safety_model']}")

    # Show validation warnings
    warnings = validate_configuration()
    if warnings:
        print("\nConfiguration Notices:")
        for warning in warnings:
            print(f"  {warning}")
        print("\nℹ️  See .env.example for configuration examples")
        print("ℹ️  Set environment variables to override dummy values")
    else:
        print("\n✅ Configuration appears to be customized for your environment")
    print("=" * 70)


if __name__ == "__main__":
    print_config()