#!/bin/bash

# LLM-D RedHatAI Model Inference Test Script

set -euo pipefail

NAMESPACE="${NAMESPACE:-llmd}"  # Generic namespace
# Original default: hacohen-llmd
MODEL="RedHatAI/DeepSeek-R1-Distill-Qwen-7B-quantized.w8a8"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

# Detect kubectl/oc
if command -v oc >/dev/null 2>&1; then
    KUBE_CMD="oc"
elif command -v kubectl >/dev/null 2>&1; then
    KUBE_CMD="kubectl"
else
    error "Neither 'oc' nor 'kubectl' found"
    exit 1
fi

log "🧪 Testing LLM-D RedHatAI Model Inference"
log "========================================="
log "Namespace: $NAMESPACE"
log "Model: $MODEL"
echo

# Check if deployment exists
log "Checking deployment status..."
if ! $KUBE_CMD get namespace "$NAMESPACE" >/dev/null 2>&1; then
    error "Namespace '$NAMESPACE' not found. Please deploy first with 'make install'"
    exit 1
fi

# Check if pods are running
PODS_READY=$($KUBE_CMD get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep "Running" | wc -l || echo "0")
if [ "$PODS_READY" -eq 0 ]; then
    warn "No running pods found. Checking pod status..."
    $KUBE_CMD get pods -n "$NAMESPACE"
    exit 1
fi
success "$PODS_READY pod(s) running"

# Set up port forwarding
log "Setting up port forwarding..."
$KUBE_CMD port-forward -n "$NAMESPACE" service/llm-d-model-service 8000:8200 >/dev/null 2>&1 &
PORT_FORWARD_PID=$!

# Wait for port forward to establish
sleep 3

# Cleanup function
cleanup() {
    if [ -n "${PORT_FORWARD_PID:-}" ]; then
        kill "$PORT_FORWARD_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Test health endpoint
log "Testing health endpoint..."
if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
    success "Health endpoint responding"
else
    warn "Health endpoint not responding (service may still be starting)"
fi

# Test model endpoint
log "Testing model endpoint..."
if curl -s -f http://localhost:8000/v1/models >/dev/null 2>&1; then
    success "Model endpoint responding"
    echo
    log "Available models:"
    curl -s http://localhost:8000/v1/models | jq '.data[].id' 2>/dev/null || true
else
    warn "Model endpoint not responding (model may still be loading)"
fi

echo

# Test inference
log "Testing inference with sample prompt..."
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"Explain quantum computing in simple terms:\",
        \"max_tokens\": 50,
        \"temperature\": 0.7
    }" 2>/dev/null || echo "")

if [[ $RESPONSE == *"choices"* ]]; then
    success "✅ Inference test passed!"
    echo
    log "Response excerpt:"
    echo "$RESPONSE" | jq '.choices[0].text' 2>/dev/null | head -3 || echo "$RESPONSE" | head -3
else
    error "❌ Inference test failed"
    echo "Response: $RESPONSE"
    exit 1
fi

echo

# Test prefix cache functionality
log "Testing prefix cache with repeated prompt..."
LONG_PREFIX="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."

log "First request (populating cache)..."
curl -s -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"$LONG_PREFIX What is the meaning of life?\",
        \"max_tokens\": 20
    }" >/dev/null 2>&1

sleep 2

log "Second request (should use cache)..."
curl -s -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"$LONG_PREFIX What is quantum mechanics?\",
        \"max_tokens\": 20
    }" >/dev/null 2>&1

# Check for cache activity in logs
log "Checking prefix cache logs..."
CACHE_LOGS=$($KUBE_CMD logs -l inferencepool=gaie-kv-events-epp -n "$NAMESPACE" --tail=50 2>/dev/null | grep -c "Got pod scores" 2>/dev/null || echo "0")
CACHE_LOGS=$(echo "$CACHE_LOGS" | tr -d '\n' | head -1)

if [ "$CACHE_LOGS" -gt 0 ]; then
    success "✅ Prefix cache activity detected ($CACHE_LOGS cache events)"
    $KUBE_CMD logs -l inferencepool=gaie-kv-events-epp -n "$NAMESPACE" --tail=10 | grep "Got pod scores" || true
else
    warn "⚠️  No obvious prefix cache activity in logs (may need more time)"
fi

echo
success "🎯 LLM-D inference test completed!"
echo
log "🔍 Monitoring Commands:"
log "  $KUBE_CMD logs -f -l app.kubernetes.io/name=llm-d-modelservice -n $NAMESPACE"
log "  $KUBE_CMD logs -l inferencepool=gaie-kv-events-epp -n $NAMESPACE --tail=100"
echo
log "🌐 Access the service:"
log "  $KUBE_CMD port-forward -n $NAMESPACE service/llm-d-model-service 8000:8200"
log "  curl http://localhost:8000/v1/models"