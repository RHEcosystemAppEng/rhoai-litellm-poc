# LiteLLM POC Overview

## Overview

The following describes how the LiteLLM and LlamaStack demo works and how to deploy, debug, and run the application.

## Functionality

This application does the following:

- Creates two teams:
    - Engineering - Budget: $100
    - Marketing - Budget: $50

- Creates two users:
    - eng-user@example.com
    - mkt-user@example.com

Data can be edited in the `deploy/helm/values.yaml` file.
```yaml
seed:
  enabled: true
  teams:
    - team_alias: engineering
      max_budget: 100.0
    - team_alias: marketing
      max_budget: 50.0
```

The above code executes in the [seed job](/deploy/helm/templates/seed-job.yaml). If this file is altered, it will create users and teams as needed.
The data is stored inside Postgres, so even after a restart the data will be saved.

> [!NOTE]
> LiteLLM by default creates API keys on behalf of the users. Refrain from creating users until the UI is up and running. 

### Getting to the LiteLLM UI

**Step 1)**, deploy the application using the [README](deploy/helm/README.md).

Use `make install` for the most basic deployment. This will create everything needed to run the demo.

**Step 2)** Once installed, navigate to the `Networking` tab in the left sidebar and click `Routes`. Find the LiteLLM route, NOT the LiteLLM-ui. The LiteLLM route is the actual LiteLLM Admin UI. The other is the chat interface. After clicking into the route, you should see the LiteLLM API Home Page, which contains links to the Admin UI.


<img src="docs/lite_llm_user_page.png" alt="LiteLLM API Home" width="300px" />


**Step 3)** Click on the first menu item "LiteLLM Admin Panel." This is the LiteLLM UI you want to interact with.

<img src="docs/login_litellm.png" alt="LiteLLM Login" width="700" />

**Step 4)** Once confronted by this menu, input the password as the `master_key` value and the username as the literal `admin`, then sign in. This should land you on the API Key Page. 

### Adding API Keys and Rules

**Step 1)** In the Users tab, create a new user by clicking the Invite User button, which opens a modal. 

<img src="docs/lite_llm_user_page.png" alt="LiteLLM User Page" width="700" />

**Step 2)** Now fill in:

- Email: Any email address
- Global Proxy Role: Admin (All), Admin (View Only), Internal User (CRUD), Internal (View Only)
- Team: The team you would like to add the user to.

> [!Warning]
> LiteLLM authorization can be assigned at the user level in the menu, but can also be assigned to a group.

**Step 3)** This creates a new user but with no access yet. This is where you create the API key.

- By creating API keys, you can distribute access keys without having to pass around the actual provider's API key to each person. 
- Additionally, API keys come with permissions and limits. 

<img src="docs/create_api_key_landing.png" alt="Create API Key Landing" width="700" />

**Step 4)** Now navigate to `Virtual Keys` and click Create Key. 

<img src="docs/api_key_props.png" alt="API Key Properties" width="700" />

This modal provides access to all the parameters you can control, including:

- Rate Limits
- Model Restrictions
- Budget Restrictions
- Guardrails
- ... and much more

**Step 5)** Now click Create API Key, this will enable a single user's API key.

> [!NOTE]
> LiteLLM only allows copying and viewing the API key upon creation. Be sure to save the API key in a safe place.

### Using the Chat UI

Once you have completed these steps, you can now interface with the Streamlit application, which points to LiteLLM. 

Navigate back to the Routes section in OpenShift and click on the Chat UI. 

<img src="docs/Image.jpeg" alt="Chat UI" width="700" /> 

#### The Sidebar

The sidebar has a set of controls for the following.
1) API Key: API Key created via LiteLLM Admin UI
2) URL: The OpenShift URL where the liteLLM API is hosted. This can be found in the Routes section in "Networking"
3) Model: The Model the current chat is using. 

You can now test all of the demos situations but with a live chat. 

**You should see and be confronted by errors when a rate limit, a guardrail or if a budget is exceeded.**




