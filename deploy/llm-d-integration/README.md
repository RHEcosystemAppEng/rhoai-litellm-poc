# LLM-D Integration for RedHatAI Model

This integration uses the existing [LLM-D repository](https://github.com/llm-d/llm-d) to deploy **precise-prefix-cache-aware** inference with the **RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8** model on a single NVIDIA L40S GPU.

## Features

- 🚀 **Automated deployment** with comprehensive Makefile
- 🌐 **External HTTP endpoint** via OpenShift Routes (compatible with cross-cluster access)
- 🧠 **Prefix caching** for improved inference performance
- 🎯 **L40S GPU optimization** with proper node scheduling
- 🔒 **Secure token management** via environment variables
- 📊 **Comprehensive testing** with health checks and cache validation

## Prerequisites

1. **OpenShift cluster** with NVIDIA L40S GPU nodes
2. **Helm**, **kubectl/oc**, and **jq** installed
3. **Git** for cloning repositories
4. **HuggingFace Token** (see Security section below)

## 🔒 Security Setup

**Never commit tokens to Git!** Set your HuggingFace token as an environment variable:

```bash
# Set your HuggingFace token (replace with your actual token)
export HF_TOKEN=hf_your_token_here

# Verify it's set
echo "HF_TOKEN: $(echo $HF_TOKEN | cut -c1-10)..."
```

## 📥 Repository Setup

**Clone the LLM-D repository** (required dependency):

```bash
# Clone LLM-D repository to the same parent directory as this project
# (so both rhoai-litellm-poc and llm-d are siblings)
cd /path/to/your/repos  # e.g., /Users/username/Desktop/repos
git clone https://github.com/llm-d/llm-d.git

# Verify directory structure:
# repos/
# ├── rhoai-litellm-poc/
# │   └── deploy/llm-d-integration/
# └── llm-d/
#     └── guides/precise-prefix-cache-aware/
ls llm-d/guides/precise-prefix-cache-aware/
```

> 💡 **Note:** The Makefile expects `llm-d` and `rhoai-litellm-poc` to be sibling directories. If you forget this step, the Makefile will detect the missing repository and show you the exact commands to run.

## 🚀 Quick Deploy

```bash
# Navigate to integration directory
cd /path/to/your/repos/rhoai-litellm-poc/deploy/llm-d-integration

# Install prerequisites (one-time setup)
make prereqs

# Deploy everything automatically
make install
```

That's it! The deployment will:
- ✅ Install gateway dependencies
- ✅ Deploy LLM-D infrastructure
- ✅ Apply L40S GPU scheduling
- ✅ Create external HTTP route (no SSL for cross-cluster compatibility)
- ✅ Display your inference endpoint URL

## 🧪 Testing

### Quick Test
```bash
make test
```

### Comprehensive Test
```bash
bash test-inference.sh
```

### Manual Testing
```bash
# Get your external URL
make route-url

# Test via external endpoint (replace URL with yours)
curl -X POST http://llm-d-inference-hacohen-llmd.apps.your-cluster.com/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8",
    "prompt": "Explain quantum computing:",
    "max_tokens": 50
  }'
```

## 📊 Management Commands

| Command | Description |
|---------|-------------|
| `make install` | Deploy LLM-D with RedHatAI model |
| `make test` | Test inference endpoint (auto-detects route) |
| `make status` | Show deployment status |
| `make logs` | View service logs |
| `make route-url` | Display external endpoint URL |
| `make create-route` | Create external route (if missing) |
| `make delete-route` | Remove external route |
| `make uninstall` | Remove deployment |
| `make clean` | Complete cleanup including namespace |

## 🧹 Clean Up

```bash
# Remove deployment
make uninstall

# Complete cleanup (removes namespace)
make clean
```

## 🏗️ Architecture

```
External Request
      │
      ▼
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  OpenShift Route    │    │   LLM-D Model        │    │  GAIE KV Events     │
│  (HTTPS External)   │───▶│   Service            │───▶│  (Cache Manager)    │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                       │                           │
                                       ▼                           ▼
                           ┌──────────────────────┐    ┌─────────────────────┐
                           │  MS KV Events        │    │  Prefix Cache       │
                           │  (vLLM + RedHatAI)   │    │  (KV Cache Sharing) │
                           └──────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                           ┌──────────────────────┐
                           │  NVIDIA L40S GPU    │
                           │  (48GB VRAM)         │
                           └──────────────────────┘
```

## 🔧 Key Differences from Default

- **Model**: `RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8` (quantized for efficiency)
- **Namespace**: `hacohen-llmd` (isolated deployment)
- **GPU Target**: Single NVIDIA L40S with proper node scheduling
- **External Access**: OpenShift Route with HTTPS termination
- **Quantization**: w8a8 format for reduced memory usage
- **Storage**: 100Gi for model artifacts
- **Automation**: Complete Makefile-driven deployment

## 🚨 Troubleshooting

### Common Issues

**Pod Stuck in Pending:**
```bash
# Check GPU node availability
make gpu-status

# Check pod events
oc describe pods -l llm-d.ai/role=decode -n hacohen-llmd
```

**Route Not Working:**
```bash
# Recreate route
make delete-route
make create-route

# Check route URL
make route-url
```

**Model Loading Issues:**
```bash
# Check model service logs
oc logs -l llm-d.ai/role=decode -n hacohen-llmd -f

# Check deployment status
make status
```

**SSL Certificate Errors:**
```bash
# Use -k flag for self-signed certificates
curl -k -X POST https://your-route-url/v1/completions ...
```

### Verification Commands

```bash
# Check all components are healthy
make status

# Test inference endpoint
make test

# View comprehensive logs
make logs

# Monitor prefix cache activity
oc logs -l inferencepool=gaie-kv-events-epp -n hacohen-llmd -f
```

## 🎯 What's Working

✅ **Automated deployment** via Makefile
✅ **External HTTPS endpoint** via OpenShift Route
✅ **RedHatAI quantized model** serving via vLLM
✅ **L40S GPU scheduling** with proper tolerations
✅ **Prefix cache infrastructure** for performance optimization
✅ **Comprehensive testing** with health checks
✅ **Secure token management** via environment variables

## 📖 Learn More

- [LLM-D Official Repository](https://github.com/llm-d/llm-d)
- [RedHatAI Model on HuggingFace](https://huggingface.co/RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8)
- [vLLM Documentation](https://docs.vllm.ai/)
- [OpenShift Routes](https://docs.openshift.com/container-platform/latest/networking/routes/route-configuration.html)