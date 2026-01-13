import os
import traceback

import streamlit as st
from llama_stack_client import LlamaStackClient

# Page configuration
st.set_page_config(page_title="LlamaStack Chat", page_icon="💬", layout="wide")

# Custom CSS for better chat appearance
st.markdown("""
    <style>
        .stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stChatInput {
            border-radius: 0.5rem;
        }
        div[data-testid="stSidebarContent"] {
            padding-top: 1rem;
        }
    </style>
""",unsafe_allow_html=True,)

# Get LlamaStack URL from environment variable or default
LLAMASTACK_URL = os.getenv(
    "LLAMASTACK_URL",
    "http://llamastack:8321",
)

print(f"LLAMASTACK_URL: {LLAMASTACK_URL}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "models" not in st.session_state:
    st.session_state.models = []
if "client" not in st.session_state:
    st.session_state.client = None


def get_client(endpoint: str) -> LlamaStackClient:
    """Get or create LlamaStack client."""
    try:
        return LlamaStackClient(base_url=endpoint, api_key=os.getenv("LITELLM_API_KEY"))
    except Exception as e:
        st.error(f"Error creating client: {e}")
        return None


def fetch_models(client: LlamaStackClient) -> list:
    """Fetch available models from LlamaStack."""
    try:
        # LlamaStack API returns models directly
        models_response = client.models.list()

        # Handle different response formats
        if isinstance(models_response, list):
            return models_response
        elif hasattr(models_response, "__iter__"):
            # Convert iterator to list
            return list(models_response)
        else:
            st.warning(f"Unexpected models response type: {type(models_response)}")
            return []
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        st.code(traceback.format_exc())
        return []


def send_chat_message(client: LlamaStackClient, model: str, messages: list) -> str:
    """Send a chat message to LlamaStack and return the response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        # Handle different response formats from LlamaStack
        if response is None:
            return "⚠️ API returned None response"

        # Try standard OpenAI format (choices directly on response)
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content

        # LlamaStack returns data in a 'data' array for list responses
        if hasattr(response, "data") and response.data:
            # LlamaStack may return historical completions
            # We need to find the LATEST completion for THIS model with matching conversation history
            current_message = messages[-1]["content"]  # The user's latest message
            conversation_length = len(messages)

            # First pass: Find exact match by model, conversation length, and last message
            for completion in response.data:
                if isinstance(completion, dict):
                    completion_model = completion.get("model", "")
                    input_msgs = completion.get("input_messages", [])

                    # Must match model
                    if completion_model != model:
                        continue

                    # Must have same number of messages (same point in conversation)
                    if len(input_msgs) != conversation_length:
                        continue

                    # Must match the last user message
                    if input_msgs and len(input_msgs) > 0:
                        last_input = input_msgs[-1].get("content", "")
                        if last_input == current_message:
                            # Found exact match!
                            choices = completion.get("choices", [])
                            if choices and len(choices) > 0:
                                message = choices[0].get("message", {})
                                content = message.get("content", "")
                                if content:
                                    return content

            # Second pass: Find by matching entire conversation history
            for completion in response.data:
                if isinstance(completion, dict):
                    completion_model = completion.get("model", "")
                    input_msgs = completion.get("input_messages", [])

                    if completion_model != model:
                        continue

                    if len(input_msgs) != conversation_length:
                        continue

                    # Check if entire conversation matches
                    matches = True
                    for i, msg in enumerate(messages):
                        if i >= len(input_msgs):
                            matches = False
                            break
                        if input_msgs[i].get("content", "") != msg["content"]:
                            matches = False
                            break

                    if matches:
                        choices = completion.get("choices", [])
                        if choices and len(choices) > 0:
                            message = choices[0].get("message", {})
                            content = message.get("content", "")
                            if content:
                                return content

            return f"⚠️ No matching completion found for model: {model}"

        return f"⚠️ Unknown response format. Type: {type(response)}"

    except Exception as e:
        error_details = traceback.format_exc()
        st.error(f"Chat error:\n```\n{error_details}\n```")
        return f"⚠️ Error: {str(e)}"


# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

llamastack_url = st.sidebar.text_input(
    "LlamaStack URL", value=LLAMASTACK_URL, help="The URL of your LlamaStack server"
)

# Create or update client
if st.session_state.client is None or st.sidebar.button("🔄 Reconnect"):
    with st.sidebar:
        with st.spinner("Connecting..."):
            st.session_state.client = get_client(llamastack_url)
            if st.session_state.client:
                st.success("✅ Connected to LlamaStack")
                # Try to fetch models immediately to verify connection
                test_models = fetch_models(st.session_state.client)
                if test_models:
                    st.session_state.models = test_models
                    st.info(f"Auto-loaded {len(test_models)} models")
                else:
                    st.warning("⚠️ Connected but couldn't fetch models. Try 'Refresh Models'.")

# Fetch models button
if st.sidebar.button("🔄 Refresh Models"):
    if st.session_state.client:
        st.session_state.models = fetch_models(st.session_state.client)
        if st.session_state.models:
            st.sidebar.success(f"✅ Loaded {len(st.session_state.models)} models")
    else:
        st.sidebar.error("❌ Not connected. Click 'Reconnect' first.")

# Model selection
if st.session_state.models:
    # Extract model identifiers
    model_names = []
    for m in st.session_state.models:
        if hasattr(m, "identifier"):
            model_names.append(m.identifier)
        elif hasattr(m, "id"):
            model_names.append(m.id)
        elif isinstance(m, dict):
            model_names.append(m.get("identifier") or m.get("id", "unknown"))
        else:
            model_names.append(str(m))

    # Filter out safety/guard models and embedding models from chat selection
    chat_models = [
        name
        for name in model_names
        if "guard" not in name.lower()
        and "embedding" not in name.lower()
        and "sentence-transformers" not in name.lower()
    ]

    if chat_models:
        selected_model = st.sidebar.selectbox(
            "Select Model",
            options=chat_models,
            help="Choose which model to chat with (safety models filtered out)",
        )
    else:
        st.sidebar.warning("⚠️ No chat models available. Safety and embedding models are hidden.")
        selected_model = st.sidebar.text_input(
            "Model Name", value="litellm-provider/llama3", help="Enter model name manually"
        )
else:
    selected_model = st.sidebar.text_input(
        "Model Name",
        value="litellm-provider/llama3",
        help="Enter model name (format: provider_id/model_name) or click 'Refresh Models'",
    )

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Display model info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Session Info")
st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages)}")
st.sidebar.markdown(f"**Model:** {selected_model}")
st.sidebar.markdown(f"**Available Models:** {len(st.session_state.models)}")
st.sidebar.markdown(f"**Connected:** {'✅ Yes' if st.session_state.client else '❌ No'}")

# Debug info
with st.sidebar.expander("🔍 Debug Info"):
    st.code(f"URL: {llamastack_url}")
    st.code(
        f"Client: {type(st.session_state.client).__name__ if st.session_state.client else 'None'}"
    )
    if st.session_state.models:
        st.code(f"First model: {st.session_state.models[0]}")

# Main chat interface
st.title("💬 LlamaStack Chat")
st.markdown("Chat with your LLM models through LlamaStack server (powered by LiteLLM).")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    if not st.session_state.client:
        st.error(
            "❌ Not connected to LlamaStack. Please check configuration and click 'Reconnect'."
        )
    else:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Prepare messages for API (include conversation history)
                api_messages = [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ]

                response = send_chat_message(st.session_state.client, selected_model, api_messages)
                st.markdown(response)

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Show helpful info if no messages yet
if not st.session_state.messages:
    st.info("""
    👋 **Welcome to LlamaStack Chat!** To get started:
    1. The app connects to LlamaStack server (default: https://llamastack-hacohen-llmlite.apps.ai-dev02.kni.syseng.devcluster.openshift.com)
    2. Click **🔄 Refresh Models** to load available models
    3. Select a model from the dropdown (e.g., `litellm-provider/llama3`)
    4. Start chatting!

    **Note:** LlamaStack uses LiteLLM as the inference backend, giving you access to all configured models.
    """)

    # Show architecture info
    with st.expander("📐 Architecture"):
        st.markdown("""
        ```
        Streamlit UI → LlamaStack Server → LiteLLM Proxy → Ollama/RHOAI
        ```

        **Available models:**
        - `litellm-provider/llama3` - Via Ollama
        - `litellm-provider/llama-fp8` - Via OpenShift AI    
        """)
