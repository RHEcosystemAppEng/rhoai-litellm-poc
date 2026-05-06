"""
LlamaStack Budget Management Demo

This script demonstrates budget enforcement through the full integration stack:
LlamaStack server → LiteLLM proxy → backend models

The demo:
1. Creates a virtual key with a very small budget limit using LiteLLM's API
2. Uses the budgeted key with LlamaStack client to send completion requests
3. Shows how LiteLLM enforces the budget even when requests go through LlamaStack
4. Demonstrates that budget exceeded errors propagate correctly through the stack
5. Cleans up the temporary key at the end

Note: Spend is tracked from response token usage since the /key/info endpoint
updates asynchronously and may not reflect real-time spend.
"""

import re
import time
import requests
from llama_stack_client import LlamaStackClient


# Configuration - import from centralized config
from config import LITELLM_BASE_URL, LLAMASTACK_BASE_URL, LITELLM_MASTER_KEY, DEFAULT_LLAMASTACK_MODEL, get_demo_config, print_config

# Use centralized configuration
LITELLM_URL = LITELLM_BASE_URL
LLAMASTACK_URL = LLAMASTACK_BASE_URL
MASTER_KEY = LITELLM_MASTER_KEY
MODEL = DEFAULT_LLAMASTACK_MODEL  # Use configured LlamaStack model

# Get budget demo configuration
budget_config = get_demo_config("budget")

# Print configuration at startup
print("LlamaStack Budget Management Demo Configuration:")
print("=" * 60)
print(f"LiteLLM URL: {LITELLM_URL}")
print(f"LlamaStack URL: {LLAMASTACK_URL}")
print(f"Model: {MODEL}")
print(f"Max Budget: ${budget_config['max_budget']}")
print("=" * 60)

# Budget configuration - set very low to quickly demonstrate exhaustion
MAX_BUDGET = 0.001  # $0.001 USD

# Cost per token (must match your LiteLLM config)
INPUT_COST_PER_TOKEN = 0.0001   # $0.10 per 1K tokens
OUTPUT_COST_PER_TOKEN = 0.0002  # $0.20 per 1K tokens


def create_budget_key(base_url: str, master_key: str, max_budget: float) -> dict:
    """Create a virtual key with a specified budget limit."""
    url = f"{base_url}/key/generate"
    headers = {"Authorization": f"Bearer {master_key}"}
    # Use timestamp to ensure unique key alias
    key_alias = f"llamastack-budget-demo-{int(time.time())}"
    payload = {
        "max_budget": max_budget,
        "key_alias": key_alias,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    response.raise_for_status()
    return response.json()


def delete_key(base_url: str, master_key: str, api_key: str) -> None:
    """Delete a virtual key."""
    url = f"{base_url}/key/delete"
    headers = {"Authorization": f"Bearer {master_key}"}
    payload = {"keys": [api_key]}

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()


def make_completion_request(client: LlamaStackClient, model: str, prompt: str):
    """Make a completion request using the LlamaStack client with budgeted key."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response


def calculate_cost(response) -> float:
    """Calculate cost from response token usage."""
    usage = response.usage
    if usage:
        input_cost = usage.prompt_tokens * INPUT_COST_PER_TOKEN
        output_cost = usage.completion_tokens * OUTPUT_COST_PER_TOKEN
        return input_cost + output_cost
    return 0.0


def extract_cost_from_error(error_message: str) -> float:
    """Extract the current cost from the budget exceeded error message."""
    # Pattern: "Current cost: 0.0014300000000000003"
    match = re.search(r"Current cost:\s*([\d.]+)", error_message)
    if match:
        return float(match.group(1))
    return 0.0


def main():
    print("=" * 60)
    print("LlamaStack Budget Management Demo")
    print("=" * 60)

    # Step 1: Create a virtual key with a small budget
    print(f"\n[Step 1] Creating virtual key with ${MAX_BUDGET} budget...")
    key_data = create_budget_key(LITELLM_URL, MASTER_KEY, MAX_BUDGET)
    api_key = key_data["key"]
    print(f"  ✓ Created key: {api_key[:20]}...")
    print(f"  ✓ Max budget: ${MAX_BUDGET}")

    # Step 1.5: Initialize LlamaStack client ONCE with the budgeted key
    # Using X-LlamaStack-Provider-Data header to pass budgeted key to backend
    print("\n[Step 1.5] Initializing LlamaStack client with budgeted key via provider_data...")
    llamastack_client = LlamaStackClient(
        base_url=LLAMASTACK_URL,  # Connect to LlamaStack server
        provider_data={
            "vllm_api_token": api_key  # Pass budgeted key via X-LlamaStack-Provider-Data
        }
    )
    print("  ✓ Client initialized with provider_data")

    request_count = 0
    budget_exceeded = False
    cumulative_spend = 0.0
    final_cost = 0.0

    try:
        # Step 2: Send requests until budget is exhausted
        print("\n[Step 2] Sending completion requests through LlamaStack until budget is exhausted...")
        print("-" * 60)

        p_index = 0

        prompts = [
            "Say 'hello' in one word.",
            "What is the capital of France?",
            "What is the capital of the UK?",
            "What is the capital of the USA?",
            "Who is the founder of Apple?",
        ]

        while not budget_exceeded:
            request_count += 1
            prompt = prompts[p_index]  # "Say 'hello' in one word."
            p_index = (p_index + 1) % len(prompts)

            try:
                print(f"\n  Request #{request_count}:")
                print(f"    Prompt: {prompt}")

                response = make_completion_request(llamastack_client, MODEL, prompt)
                content = response.choices[0].message.content
                print(f"    Response: {content}")

                # Calculate and track spend from token usage
                request_cost = calculate_cost(response)
                cumulative_spend += request_cost

                # Show token usage
                if response.usage:
                    print(f"    Tokens: {response.usage.prompt_tokens} in / {response.usage.completion_tokens} out")
                print(f"    Request cost: ${request_cost:.6f}")
                print(f"    Cumulative spend: ${cumulative_spend:.6f} / ${MAX_BUDGET}")

            except Exception as e:
                error_message = str(e)
                if "Budget" in error_message or "budget" in error_message or "exceeded" in error_message.lower():
                    budget_exceeded = True
                    # Extract actual cost from error message
                    final_cost = extract_cost_from_error(error_message)
                    print("\n  ✗ REQUEST REJECTED - Budget Exceeded!")
                    print(f"    Error: {error_message}")
                else:
                    # Re-raise if it's a different error
                    raise

        # Step 3: Show summary
        print("\n" + "=" * 60)
        print("[Step 3] Budget Demo Summary")
        print("=" * 60)
        print(f"  • Total requests made: {request_count - 1} (successful)")
        print("  • Requests rejected: 1 (budget exceeded)")
        print(f"  • Max budget: ${MAX_BUDGET}")
        if final_cost > 0:
            print(f"  • Final spend (from LiteLLM): ${final_cost:.6f}")
        print(f"  • Tracked spend (calculated): ${cumulative_spend:.6f}")
        print("  • Integration: LlamaStack → LiteLLM ✓")

    finally:
        # Step 4: Cleanup - delete the temporary key
        print("\n[Step 4] Cleaning up temporary key...")
        try:
            delete_key(LITELLM_URL, MASTER_KEY, api_key)
            print("  ✓ Key deleted successfully")
        except Exception as e:
            print(f"  ✗ Failed to delete key: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
