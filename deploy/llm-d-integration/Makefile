# LLM-D Integration Makefile
# Uses the existing LLM-D repository for deployment

# Configuration
NAMESPACE ?= hacohen-llmd
HF_TOKEN ?= $(shell echo $$HF_TOKEN)
HF_TOKEN_NAME ?= llm-d-hf-token
LLM_D_REPO ?= ../../../llm-d
MODEL_NAME = RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8

# Detect kubectl/oc
ifeq ($(shell which oc 2>/dev/null),)
KUBE_CMD = kubectl
else
KUBE_CMD = oc
endif

.PHONY: help prereqs install status test logs urls uninstall clean create-route delete-route route-url

help: ## Show this help message
	@echo "LLM-D Integration - RedHatAI DeepSeek-R1 Deployment"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Deploy LLM-D with RedHatAI model"
	@echo "  make status         Show deployment status"
	@echo "  make test           Test inference endpoint"
	@echo "  make logs           Show service logs"
	@echo "  make urls           Display service URLs"
	@echo "  make create-route   Create external route for inference"
	@echo "  make route-url      Display external route URL"
	@echo "  make delete-route   Remove external route"
	@echo "  make uninstall      Remove deployment"
	@echo "  make clean          Complete cleanup including namespace"
	@echo ""
	@echo "Prerequisites:"
	@echo "  make prereqs        Install gateway dependencies"
	@echo ""
	@echo "Configuration:"
	@echo "  NAMESPACE=$(NAMESPACE)"
	@echo "  HF_TOKEN=$(if $(HF_TOKEN),✓ Set,✗ Not set)"
	@echo "  LLM_D_REPO=$(LLM_D_REPO)"

prereqs: ## Install LLM-D gateway prerequisites
	@echo "🔧 Installing LLM-D gateway prerequisites..."
	@if [ ! -d "$(LLM_D_REPO)" ]; then \
		echo "❌ LLM-D repository not found at $(LLM_D_REPO)"; \
		echo ""; \
		echo "📥 Please clone the LLM-D repository as a sibling directory:"; \
		echo "  cd ../../../"; \
		echo "  git clone https://github.com/llm-d/llm-d.git"; \
		echo ""; \
		echo "Expected structure:"; \
		echo "  repos/"; \
		echo "  ├── rhoai-litellm-poc/"; \
		echo "  └── llm-d/"; \
		echo ""; \
		echo "Then run 'make prereqs' again."; \
		exit 1; \
	fi
	@cd $(LLM_D_REPO) && ./guides/prereq/gateway-provider/install-gateway-provider-dependencies.sh
	@cd $(LLM_D_REPO) && helmfile apply -f guides/prereq/gateway-provider/istio.helmfile.yaml
	@echo "✅ Prerequisites installed"

install: ## Deploy LLM-D with RedHatAI model
	@echo "🚀 Deploying LLM-D with $(MODEL_NAME)..."
	@if [ -z "$(HF_TOKEN)" ]; then \
		echo "❌ HF_TOKEN environment variable is required"; \
		echo "Please set: export HF_TOKEN=your_huggingface_token"; \
		exit 1; \
	fi

	# Create namespace if it doesn't exist
	@$(KUBE_CMD) get namespace $(NAMESPACE) >/dev/null 2>&1 || $(KUBE_CMD) create namespace $(NAMESPACE)

	# Create HuggingFace token secret
	@$(KUBE_CMD) create secret generic $(HF_TOKEN_NAME) \
		--from-literal="HF_TOKEN=$(HF_TOKEN)" \
		--namespace="$(NAMESPACE)" \
		--dry-run=client -o yaml | $(KUBE_CMD) apply -f -

	# Backup original values and copy our custom values
	@cd $(LLM_D_REPO)/guides/precise-prefix-cache-aware/ms-kv-events && \
		cp values.yaml values.yaml.backup 2>/dev/null || true
	@cp ms-kv-events-redhatai.yaml $(LLM_D_REPO)/guides/precise-prefix-cache-aware/ms-kv-events/values.yaml

	# Deploy LLM-D stack
	@cd $(LLM_D_REPO)/guides/precise-prefix-cache-aware && \
		helmfile apply -n $(NAMESPACE)

	@echo "🔧 Applying L40S GPU nodeSelector and tolerations..."
	@$(KUBE_CMD) patch deployment ms-kv-events-llm-d-modelservice-decode -n $(NAMESPACE) --type='merge' -p='{"spec":{"template":{"spec":{"nodeSelector":{"nvidia.com/gpu.product":"NVIDIA-L40S","nvidia.com/gpu.present":"true"},"tolerations":[{"key":"nvidia.com/gpu","operator":"Exists","effect":"NoSchedule"},{"key":"g6e-gpu","operator":"Equal","value":"true","effect":"NoSchedule"}]}}}}'

	@echo "🧹 Cleaning up pending pods..."
	@$(KUBE_CMD) delete pods -l llm-d.ai/role=decode --field-selector=status.phase=Pending -n $(NAMESPACE) --ignore-not-found=true

	@echo "🌐 Creating external route for inference endpoint..."
	@$(KUBE_CMD) apply -f model-service.yaml
	@echo "⏳ Waiting for route to be ready..."
	@sleep 5

	@echo ""
	@echo "✅ LLM-D deployment complete!"
	@echo ""
	@echo "🔗 External Inference Endpoint:"
	@ROUTE_HOST=$$($(KUBE_CMD) get route llm-d-inference -n $(NAMESPACE) --no-headers -o custom-columns=HOST:.spec.host 2>/dev/null); \
	if [ -n "$$ROUTE_HOST" ]; then \
		echo "  🌐 http://$$ROUTE_HOST"; \
		echo ""; \
		echo "📝 Test with curl:"; \
		echo "  curl -X POST http://$$ROUTE_HOST/v1/completions \\"; \
		echo "    -H \"Content-Type: application/json\" \\"; \
		echo "    -d '{\"model\": \"$(MODEL_NAME)\", \"prompt\": \"Hello!\", \"max_tokens\": 50}'"; \
	else \
		echo "  ⚠️  Route still provisioning. Run 'make route-url' in a moment."; \
	fi
	@echo ""
	@echo "🔍 Management Commands:"
	@echo "  make status     - Check deployment status"
	@echo "  make test       - Test inference endpoint"
	@echo "  make route-url  - Display external URL again"
	@echo "  make logs       - View service logs"

status: ## Show deployment status
	@echo "📊 LLM-D Deployment Status (Namespace: $(NAMESPACE))"
	@echo "=================================================="
	@echo ""
	@echo "📋 Helm Releases:"
	@helm list -n $(NAMESPACE)
	@echo ""
	@echo "🚀 Pods:"
	@$(KUBE_CMD) get pods -n $(NAMESPACE)
	@echo ""
	@echo "🌐 Services:"
	@$(KUBE_CMD) get services -n $(NAMESPACE)

test: ## Test inference endpoint
	@echo "🧪 Testing LLM-D inference endpoint..."
	@echo "Checking for external route..."
	@ROUTE_HOST=$$($(KUBE_CMD) get route llm-d-inference -n $(NAMESPACE) --no-headers -o custom-columns=HOST:.spec.host 2>/dev/null); \
	if [ -n "$$ROUTE_HOST" ]; then \
		echo "🌐 Using external route: http://$$ROUTE_HOST"; \
		echo "Testing inference via external endpoint..."; \
		echo ""; \
		RESPONSE=$$(curl -s -X POST http://$$ROUTE_HOST/v1/completions \
			-H "Content-Type: application/json" \
			-d '{"model": "$(MODEL_NAME)", "prompt": "What is the capital of France?", "max_tokens": 50}' 2>/dev/null); \
		if [ -n "$$RESPONSE" ]; then \
			echo "📊 Response:"; \
			echo "$$RESPONSE" | jq . 2>/dev/null || echo "$$RESPONSE"; \
		else \
			echo "❌ No response received"; \
		fi; \
	else \
		echo "⚠️  No external route found. Using port forwarding..."; \
		echo "💡 Run 'make create-route' to create an external endpoint"; \
		echo ""; \
		POD_NAME=$$($(KUBE_CMD) get pods -n $(NAMESPACE) -l llm-d.ai/role=decode -o jsonpath='{.items[0].metadata.name}' 2>/dev/null); \
		if [ -n "$$POD_NAME" ]; then \
			echo "Port forwarding to pod: $$POD_NAME"; \
			$(KUBE_CMD) port-forward -n $(NAMESPACE) pod/$$POD_NAME 8000:8200 & \
			PORT_FORWARD_PID=$$!; \
			sleep 5; \
			echo "Testing inference via port forward..."; \
			echo ""; \
			RESPONSE=$$(curl -s http://localhost:8000/v1/completions \
				-H "Content-Type: application/json" \
				-d '{"model": "$(MODEL_NAME)", "prompt": "Explain quantum computing in simple terms:", "max_tokens": 50}' 2>/dev/null); \
			if [ -n "$$RESPONSE" ]; then \
				echo "📊 Response:"; \
				echo "$$RESPONSE" | jq . 2>/dev/null || echo "$$RESPONSE"; \
			else \
				echo "❌ No response received"; \
			fi; \
			kill $$PORT_FORWARD_PID 2>/dev/null || true; \
		else \
			echo "❌ No model service pod found"; \
		fi; \
	fi
	@echo "✅ Inference test complete"

logs: ## Show service logs
	@echo "📝 LLM-D Service Logs (Namespace: $(NAMESPACE))"
	@echo "==============================================="
	@echo ""
	@echo "🔹 Infrastructure Logs:"
	@$(KUBE_CMD) logs -l type=infrastructure -n $(NAMESPACE) --tail=20 --prefix=true || true
	@echo ""
	@echo "🔹 GAIE KV Events Logs:"
	@$(KUBE_CMD) logs -l inferencepool=gaie-kv-events-epp -n $(NAMESPACE) --tail=20 --prefix=true || true
	@echo ""
	@echo "🔹 Model Service Logs:"
	@$(KUBE_CMD) logs -l app.kubernetes.io/name=llm-d-modelservice -n $(NAMESPACE) --tail=20 --prefix=true || true

logs-follow: ## Follow service logs in real-time
	@echo "📝 Following LLM-D Logs (Press Ctrl+C to stop)..."
	@$(KUBE_CMD) logs -f -l app.kubernetes.io/name=llm-d-modelservice -n $(NAMESPACE) --prefix=true

urls: ## Display service URLs
	@echo "🌐 LLM-D Service URLs (Namespace: $(NAMESPACE))"
	@echo "=============================================="
	@echo ""
	@echo "🔗 Port Forward Commands:"
	@echo "  $(KUBE_CMD) port-forward -n $(NAMESPACE) service/infra-kv-events-inference-gateway-istio 8000:80"
	@echo ""
	@echo "📡 Inference Endpoint:"
	@echo "  http://localhost:8000/v1/completions"
	@echo ""
	@echo "🔍 Health Check:"
	@echo "  http://localhost:8000/health"

uninstall: ## Remove LLM-D deployment
	@echo "🗑️  Removing LLM-D deployment..."
	@cd $(LLM_D_REPO)/guides/precise-prefix-cache-aware && helmfile destroy -n $(NAMESPACE) || true
	@echo "⏳ Waiting for pods to terminate..."
	@$(KUBE_CMD) wait --for=delete pods --all -n $(NAMESPACE) --timeout=120s || true
	# Restore original values file
	@cd $(LLM_D_REPO)/guides/precise-prefix-cache-aware/ms-kv-events && \
		mv values.yaml.backup values.yaml 2>/dev/null || true
	@echo "✅ LLM-D deployment removed"

clean: uninstall ## Complete cleanup including namespace
	@echo "🧹 Complete cleanup..."
	@$(KUBE_CMD) delete namespace $(NAMESPACE) --ignore-not-found=true
	@echo "✅ Cleanup complete"

validate-token: ## Validate HuggingFace token
	@echo "🔍 Validating HuggingFace token..."
	@if [ -z "$(HF_TOKEN)" ]; then \
		echo "❌ HF_TOKEN not set"; \
		exit 1; \
	fi
	@if ! echo "$(HF_TOKEN)" | grep -q "^hf_"; then \
		echo "⚠️  Warning: Token should start with 'hf_'"; \
	fi
	@echo "✅ Token format looks correct"

gpu-status: ## Check GPU node status
	@echo "🎮 GPU Node Status"
	@echo "=================="
	@$(KUBE_CMD) get nodes -l node.kubernetes.io/accelerator=nvidia-l40s -o wide || echo "No L40S nodes found"
	@$(KUBE_CMD) describe nodes -l node.kubernetes.io/accelerator=nvidia-l40s | grep -A5 "Allocatable" || true

create-route: ## Create external route for inference endpoint
	@echo "🌐 Creating external route for LLM-D inference..."
	@$(KUBE_CMD) apply -f model-service.yaml
	@echo "✅ Route created successfully"
	@echo ""
	@echo "🔗 Getting route URL..."
	@sleep 2  # Wait for route to be processed
	@$(KUBE_CMD) get route llm-d-inference -n $(NAMESPACE) --no-headers -o custom-columns=HOST:.spec.host 2>/dev/null | \
		while read host; do echo "🌐 External URL: http://$$host"; done || \
		echo "⏳ Route still being provisioned. Run 'make route-url' in a moment."

route-url: ## Display external route URL
	@echo "🌐 LLM-D Inference Endpoint"
	@echo "=========================="
	@ROUTE_HOST=$$($(KUBE_CMD) get route llm-d-inference -n $(NAMESPACE) --no-headers -o custom-columns=HOST:.spec.host 2>/dev/null); \
	if [ -n "$$ROUTE_HOST" ]; then \
		echo "🔗 External URL: http://$$ROUTE_HOST"; \
		echo ""; \
		echo "📝 Test with curl:"; \
		echo "  curl -X POST http://$$ROUTE_HOST/v1/completions \\"; \
		echo "    -H \"Content-Type: application/json\" \\"; \
		echo "    -d '{"; \
		echo "      \"model\": \"$(MODEL_NAME)\","; \
		echo "      \"prompt\": \"Explain quantum computing:\","; \
		echo "      \"max_tokens\": 50"; \
		echo "    }'"; \
	else \
		echo "❌ Route not found. Run 'make create-route' first."; \
	fi

delete-route: ## Remove external route
	@echo "🗑️  Removing external route..."
	@$(KUBE_CMD) delete -f model-service.yaml --ignore-not-found=true
	@echo "✅ Route removed"