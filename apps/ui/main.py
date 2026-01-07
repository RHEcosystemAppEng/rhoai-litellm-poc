import streamlit as st
import requests
import os
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(
    base_url="http://llamastack:8321",
    api_key="master-key"
)

# Page configuration
st.set_page_config(
    page_title="LiteLLM Chat",
    page_icon="💬",
    layout="wide"
)

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
""", unsafe_allow_html=True)

# Get LiteLLM URL from environment variable, secrets, or default
LITELLM_URL = os.getenv("LITELLM_URL", "http://llamastack:8321")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "master-key")

print(f"LITELLM_URL: {LITELLM_URL}")
print(f"LITELLM_API_KEY: {LITELLM_API_KEY}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "models" not in st.session_state:
    st.session_state.models = []


def fetch_models(endpoint: str, api_key: str) -> list:
    """Fetch available models from LiteLLM."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        res = requests.get(f"{endpoint.rstrip('/')}/models", headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        st.error(f"Error fetching models: {e}")
        return []


def send_chat_message(endpoint: str, api_key: str, model: str, messages: list) -> str:
    """Send a chat message to LiteLLM and return the response."""
    try:
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "messages": messages,
        }
        
        res = requests.post(
            f"{endpoint.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        res.raise_for_status()
        
        response_data = res.json()
        return response_data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. The model may be slow or unavailable."
    except requests.exceptions.RequestException as e:
        return f"⚠️ Error: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"⚠️ Unexpected response format: {str(e)}"


# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

litellm_url = st.sidebar.text_input(
    "LiteLLM URL",
    value=LITELLM_URL,
    help="The URL of your LiteLLM proxy server"
)

api_key = st.sidebar.text_input(
    "API Key",
    value=LITELLM_API_KEY,
    type="password",
    help="Your LiteLLM API key for authentication"
)

# Fetch models button
if st.sidebar.button("🔄 Refresh Models"):
    st.session_state.models = fetch_models(litellm_url, api_key)

# Model selection
if st.session_state.models:
    model_names = [m.get("id", "unknown") for m in st.session_state.models]
    selected_model = st.sidebar.selectbox(
        "Select Model",
        options=model_names,
        help="Choose which model to chat with"
    )
else:
    selected_model = st.sidebar.text_input(
        "Model Name",
        value="llama3",
        help="Enter model name manually or click 'Refresh Models'"
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

# Main chat interface
st.title("💬 LiteLLM Chat")
st.markdown("Chat with your LLM models through LiteLLM proxy.")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
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
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            
            response = send_chat_message(
                litellm_url,
                api_key,
                selected_model,
                api_messages
            )
            st.markdown(response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Show helpful info if no messages yet
if not st.session_state.messages:
    st.info("""
    👋 **Welcome!** To get started:
    1. Configure your LiteLLM URL and API key in the sidebar
    2. Click **Refresh Models** to load available models
    3. Select a model and start chatting!
    """)
