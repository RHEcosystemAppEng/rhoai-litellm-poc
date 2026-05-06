# LiteLLM Usage Guide

This guide explains how to use the deployed LiteLLM platform for managing teams, users, API keys, and interacting with language models.

> **Prerequisites**: Ensure LiteLLM is deployed using the **[Deployment Guide](deploy/DEPLOYMENT.md)** before following this guide.

---

## What Gets Configured

The platform automatically creates demo resources to get you started:

### Teams and Budgets

| Team | Budget | Purpose |
|------|--------|---------|
| Engineering | $100 | Development and testing |
| Marketing | $50 | Content generation |

### Demo Users

| User | Team | Access Level |
|------|------|-------------|
| eng-user@example.com | Engineering | Full access |
| mkt-user@example.com | Marketing | Limited access |

> [!NOTE]
> These are demonstration entries. You can customize teams and budgets through the admin interface or by modifying the deployment configuration.

---

## Accessing the LiteLLM Admin Interface

### Locate the Admin UI

1. In OpenShift, navigate to **Networking** → **Routes**
2. Find the **LiteLLM** route (not LiteLLM-ui)
3. Click the route URL to access the API home page

> [!TIP]
> **LiteLLM route** = Admin interface | **LiteLLM-ui route** = Chat interface

You should see the LiteLLM API Home Page:

<img src="docs/litellm_api_home.png" alt="LiteLLM API Home" width="700" />

### Access the Admin Panel

Click **LiteLLM Admin Panel** to access the administration interface.

<img src="docs/login_litellm.png" alt="LiteLLM Login" width="700" />

### Sign In

Use these credentials to log in:

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | Your deployment's `masterKey` value |

> [!INFO]
> The master key is configured during deployment in `helm/values.yaml` under `litellm.masterKey`.

---

## Managing Users and Teams

### Creating Users

1. Navigate to the **Users** tab in the admin interface
2. Click **Invite User**

<img src="docs/lite_llm_user_page.png" alt="LiteLLM User Page" width="700" />

3. Configure the user:

| Field | Description | Options |
|-------|-------------|---------|
| **Email** | User identifier (any valid email) | user@example.com |
| **Global Proxy Role** | Permission level | Admin (All), Admin (View Only), Internal User (CRUD), Internal (View Only) |
| **Team** | Team assignment | Engineering, Marketing, or custom teams |

> [!WARNING]
> Permissions can be set at both user and team levels. Choose the appropriate scope for your security requirements.

### Understanding User Roles

| Role | Permissions |
|------|-------------|
| **Admin (All)** | Full system access, can modify all settings |
| **Admin (View Only)** | Read-only admin access, can view all data |
| **Internal User (CRUD)** | Can create/modify own resources |
| **Internal (View Only)** | Read-only access to assigned resources |

---

## API Key Management

### Why API Keys Matter

API keys provide:
- **Security**: Access control without exposing provider credentials
- **Granular permissions**: Fine-tuned access to specific models and features
- **Usage tracking**: Monitor and limit consumption per key
- **Budget enforcement**: Set spending limits per key or team

<img src="docs/create_api_key_landing.png" alt="Create API Key Landing" width="700" />

### Creating API Keys

1. Navigate to **Virtual Keys** in the admin panel
2. Click **Create Key**

<img src="docs/api_key_props.png" alt="API Key Properties" width="700" />

3. Configure the key:

| Parameter | Purpose | Example |
|-----------|---------|---------|
| **Rate Limits** | Control request frequency | 100 requests/minute |
| **Model Restrictions** | Limit allowed models | Only GPT-4, Claude |
| **Budget Restrictions** | Set spending caps | $10/month |
| **Guardrails** | Content safety policies | Block harmful content |

4. Click **Create API Key** to generate

> [!CAUTION]
> **Save your API key immediately!** LiteLLM shows the key only once. You cannot retrieve it later.

---

## Using the Chat Interface

### Access the Chat UI

1. Return to **Networking** → **Routes** in OpenShift
2. Click the **LiteLLM-ui** route

<img src="docs/Image.jpeg" alt="Chat UI" width="700" />

### Configure the Interface

Use the sidebar to set up your session:

| Setting | Description | How to Get |
|---------|-------------|-----------|
| **API Key** | Authentication token | Created in admin interface |
| **URL** | LiteLLM endpoint | LiteLLM route URL from OpenShift |
| **Model** | LLM to use | Available models shown in dropdown |

### Available Models

The chat interface displays all models configured in your deployment:
- **Ollama models** (e.g., llama3) for local inference
- **Cloud providers** (OpenAI, Anthropic, etc.) if configured
- **RHOAI models** deployed via OpenShift AI

---

## Testing Platform Features

### Budget Enforcement

1. Create an API key with a low budget limit (e.g., $1)
2. Make multiple requests until the budget is exceeded
3. Observe budget limit error messages

### Rate Limiting

1. Configure an API key with strict rate limits
2. Send rapid successive requests
3. Verify rate limiting responses

### Content Guardrails

1. Enable content safety on an API key
2. Submit prompts with inappropriate content
3. Confirm safety filters block harmful requests

> [!IMPORTANT]
> All limits and guardrails provide detailed error messages explaining why requests were blocked.

---

## Advanced Usage

### Team-Based Access Control

- Assign users to teams for group management
- Set team-level budgets and restrictions
- Monitor usage by team for cost attribution

### Multi-Model Workflows

- Switch between models in the chat interface
- Compare responses from different providers
- Test failover behavior when models are unavailable

### API Integration

Use your API keys programmatically:

```bash
# Test with curl
curl "https://<litellm-route>/chat/completions" \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

```python
# Use with Python
import openai

client = openai.OpenAI(
    api_key="<your-api-key>",
    base_url="https://<litellm-route>"
)

response = client.chat.completions.create(
    model="llama3",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## Configuration Customization

### Modifying Teams and Budgets

Edit `deploy/helm/values.yaml` to customize initial setup:

```yaml
seed:
  enabled: true
  teams:
    - team_alias: engineering
      max_budget: 100.0
    - team_alias: marketing
      max_budget: 50.0
    - team_alias: sales
      max_budget: 75.0
```

Then upgrade the deployment:

```bash
cd deploy
make upgrade
```

### Adding New Models

Add model configurations in `values.yaml`:

```yaml
litellm:
  config:
    model_list:
      - model_name: gpt-4
        litellm_params:
          model: azure/gpt-4
          api_base: https://your-azure-endpoint.com/
          api_key: your-api-key
```

---

## Troubleshooting

### Cannot Access Admin UI

- **Check credentials**: Verify your master key is correct
- **Check routes**: Ensure you're using the LiteLLM route, not LiteLLM-ui
- **Check deployment**: Verify pods are running with `oc get pods -n litellm`

### API Key Not Working

- **Verify key format**: Should start with `sk-`
- **Check permissions**: Ensure the key has access to the requested model
- **Check budgets**: Verify budget limits haven't been exceeded

### Chat UI Cannot Connect

- **Check URL**: Use the full LiteLLM route URL including `https://`
- **Check API key**: Ensure it's entered correctly without extra spaces
- **Check model availability**: Verify the selected model is deployed

---

## Related Documentation

- **[Deployment Guide](deploy/DEPLOYMENT.md)** - How to deploy LiteLLM
- **[Demo Guides](demos/)** - Feature-specific demonstrations
- **[LLM-D Integration](deploy/llm-d-integration/README.md)** - RHOAI model setup
- **[Troubleshooting](TROUBLESHOOTING.md)** - Comprehensive problem resolution
- **[Configuration Reference](docs/CONFIGURATION.md)** - Detailed configuration examples

