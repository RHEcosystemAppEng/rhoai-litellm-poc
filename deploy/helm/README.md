# LiteLLM Helm Chart

This directory contains the Helm chart for deploying LiteLLM.

## Documentation

For complete deployment instructions, configuration options, and troubleshooting, see the **[Deployment Guide](../DEPLOYMENT.md)**.

## Quick Reference

```bash
# Install with default settings
helm install litellm . --namespace litellm --create-namespace

# Install with custom values
helm install litellm . -f custom-values.yaml --namespace litellm --create-namespace

# Upgrade configuration
helm upgrade litellm . --namespace litellm
```

## Files in This Directory

- `Chart.yaml` - Chart metadata
- `values.yaml` - Default configuration values
- `templates/` - Kubernetes manifests
- `charts/` - Chart dependencies (pgvector, llama-stack)

For detailed configuration examples and production setup, refer to the **[main deployment documentation](../DEPLOYMENT.md)**.