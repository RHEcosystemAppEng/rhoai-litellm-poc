# LiteLLM Troubleshooting Guide

This guide provides solutions for common issues you may encounter with the LiteLLM platform.

## Quick Reference Table

| Issue | Component | Severity | Solution Link |
|-------|-----------|----------|---------------|
| Pod not starting | LiteLLM | High | [Deployment Issues](#deployment-issues) |
| Cannot access UI | Routes/Networking | Medium | [Access Issues](#access-issues) |
| API key not working | Authentication | High | [Authentication Issues](#authentication-issues) |
| Database connection failed | PostgreSQL | High | [Database Issues](#database-issues) |
| UI cannot connect to API | Networking | Medium | [UI Connection Issues](#ui-connection-issues) |
| Budget limits not enforcing | Configuration | Low | [Configuration Issues](#configuration-issues) |
| Models not available | Model Configuration | Medium | [Model Issues](#model-issues) |

---

## Deployment Issues

### LiteLLM Pod Not Starting

**Symptoms:**
- Pod stuck in `Pending`, `CrashLoopBackOff`, or `Error` state
- Deployment fails to complete

**Diagnosis:**
```bash
# Check pod status
oc get pods -n litellm

# Get detailed pod information
oc describe pod -n litellm -l app.kubernetes.io/name=litellm

# Check logs for errors
oc logs -n litellm -l app.kubernetes.io/name=litellm --tail=50
```

**Common Causes & Solutions:**

1. **Resource Constraints**
   ```bash
   # Check node resources
   oc describe nodes | grep -A 5 "Allocated resources"
   
   # Solution: Increase cluster resources or reduce pod resource requests
   ```

2. **Configuration Errors**
   ```bash
   # Check ConfigMap
   oc get configmap litellm-config -n litellm -o yaml
   
   # Solution: Fix configuration and upgrade deployment
   make upgrade
   ```

3. **Image Pull Issues**
   ```bash
   # Check image pull status
   oc describe pod <pod-name> -n litellm | grep -A 5 "Events"
   
   # Solution: Verify image repository access and credentials
   ```

### Helm Dependency Issues

**Symptoms:**
- `helm install` fails with dependency errors
- Missing pgvector or llama-stack charts

**Solution:**
```bash
cd deploy/helm
helm dependency update
helm install litellm . --namespace litellm --create-namespace
```

---

## Access Issues

### Cannot Access Admin UI

**Symptoms:**
- Cannot reach LiteLLM route
- Browser shows connection timeout or 404

**Diagnosis:**
```bash
# Check routes
oc get routes -n litellm

# Test route connectivity
curl -k https://$(oc get route litellm -n litellm -o jsonpath='{.spec.host}')/health
```

**Solutions:**

1. **Route Not Created**
   ```bash
   # Check if route exists
   oc get route litellm -n litellm
   
   # If missing, check Helm values
   grep -A 5 "route:" deploy/helm/values.yaml
   ```

2. **DNS Resolution Issues**
   - Verify the route hostname resolves correctly
   - Check cluster's external DNS configuration

3. **Firewall/Network Policies**
   - Verify cluster ingress is properly configured
   - Check for NetworkPolicies blocking traffic

### Login Fails

**Symptoms:**
- Invalid username/password error
- Cannot access admin panel

**Solution:**
```bash
# Check master key configuration
oc get secret litellm-config -n litellm -o yaml | grep masterKey

# Default credentials:
# Username: admin
# Password: value of litellm.masterKey from values.yaml
```

---

## Authentication Issues

### API Key Not Working

**Symptoms:**
- `401 Unauthorized` responses
- `Invalid API key` errors

**Diagnosis:**
```bash
# Test API key
curl "https://<litellm-route>/models" \
  -H "Authorization: Bearer <your-api-key>"
```

**Common Causes & Solutions:**

1. **Malformed API Key**
   - Ensure key starts with `sk-`
   - Check for extra spaces or special characters
   - Regenerate key if necessary

2. **Expired or Deleted Key**
   - Verify key exists in admin UI under "Virtual Keys"
   - Check key status and permissions

3. **Budget Exceeded**
   ```bash
   # Check budget status in admin UI
   # Or query database directly:
   oc exec -it deployment/pgvector -n litellm -- \
     psql -U postgres -d litellm -c "SELECT * FROM LiteLLM_BudgetTable;"
   ```

### Permission Denied

**Symptoms:**
- API key works but access to specific models denied
- `403 Forbidden` responses

**Solution:**
- Check model restrictions in API key configuration
- Verify team-level permissions
- Review user role assignments

---

## Database Issues

### PostgreSQL Connection Failed

**Symptoms:**
- LiteLLM logs show database connection errors
- Features like budgets and teams don't work

**Diagnosis:**
```bash
# Check PostgreSQL pod status
oc get pods -n litellm | grep pgvector

# Check database environment variables
oc exec -it deployment/litellm -n litellm -- env | grep DATABASE

# Test database connectivity
oc exec -it deployment/pgvector -n litellm -- \
  psql -U postgres -d litellm -c "SELECT version();"
```

**Solutions:**

1. **Database Pod Not Running**
   ```bash
   # Check pod status
   oc describe pod -n litellm -l app=pgvector
   
   # Restart database
   oc rollout restart statefulset/pgvector -n litellm
   ```

2. **Connection String Issues**
   ```bash
   # Verify DATABASE_URL format
   # Should be: postgresql://user:password@host:port/dbname
   oc get secret litellm-config -n litellm -o yaml
   ```

3. **Database Initialization Problems**
   ```bash
   # Check database logs
   oc logs -n litellm statefulset/pgvector
   
   # Verify database schema
   oc exec -it deployment/pgvector -n litellm -- \
     psql -U postgres -d litellm -c "\dt"
   ```

### Database Data Missing

**Symptoms:**
- Users, teams, or API keys disappear after restart
- Seed data not created

**Solution:**
```bash
# Check if seed job completed successfully
oc get jobs -n litellm

# Rerun seed job if necessary
oc delete job litellm-seed -n litellm
make upgrade
```

---

## UI Connection Issues

### Streamlit UI Cannot Connect to LiteLLM

**Symptoms:**
- UI shows "Connection Error"
- Models list is empty
- Chat interface doesn't respond

**Diagnosis:**
```bash
# Check UI ConfigMap
oc get configmap litellm-ui-config -n litellm -o yaml

# Test connection from UI pod
oc exec -it -n litellm deployment/litellm-ui -- \
  curl http://litellm:4000/health
```

**Solutions:**

1. **Service Discovery Issues**
   ```bash
   # Verify LiteLLM service exists
   oc get svc litellm -n litellm
   
   # Check service endpoints
   oc get endpoints litellm -n litellm
   ```

2. **UI Configuration Errors**
   ```bash
   # Check UI environment variables
   oc exec -it deployment/litellm-ui -n litellm -- env | grep LITELLM
   
   # Correct values should be:
   # LITELLM_URL=http://litellm:4000
   ```

3. **UI Pod Issues**
   ```bash
   # Check UI pod logs
   oc logs -n litellm deployment/litellm-ui
   
   # Restart UI if necessary
   oc rollout restart deployment/litellm-ui -n litellm
   ```

---

## Configuration Issues

### Budget Limits Not Enforcing

**Symptoms:**
- Requests continue after budget exceeded
- No budget error messages

**Diagnosis:**
```bash
# Check budget configuration
oc exec -it deployment/pgvector -n litellm -- \
  psql -U postgres -d litellm -c "SELECT * FROM LiteLLM_BudgetTable;"

# Verify spend tracking
oc exec -it deployment/pgvector -n litellm -- \
  psql -U postgres -d litellm -c "SELECT * FROM LiteLLM_SpendLogs ORDER BY startTime DESC LIMIT 10;"
```

**Solutions:**

1. **Database Not Connected**
   - Verify PostgreSQL is enabled and connected
   - Without database, budgets cannot be enforced

2. **Budget Configuration Missing**
   ```bash
   # Check seed data creation
   oc logs -n litellm job/litellm-seed
   
   # Recreate if necessary
   oc delete job litellm-seed -n litellm
   make upgrade
   ```

### Configuration Changes Not Applied

**Symptoms:**
- Changes to `values.yaml` don't take effect
- Old configuration persists after upgrade

**Solution:**
```bash
# Force restart after config changes
oc rollout restart deployment/litellm -n litellm
oc rollout restart deployment/litellm-ui -n litellm

# Or use make command
make upgrade

# Verify configuration was applied
oc get configmap litellm-config -n litellm -o yaml
```

---

## Model Issues

### Models Not Available

**Symptoms:**
- `/models` endpoint returns empty list
- Specific models show as unavailable

**Diagnosis:**
```bash
# Test models endpoint
curl "https://<litellm-route>/models" \
  -H "Authorization: Bearer <api-key>"

# Check LiteLLM configuration
oc get configmap litellm-config -n litellm -o yaml | grep -A 20 model_list
```

**Solutions:**

1. **Configuration Errors**
   ```yaml
   # Fix model configuration in values.yaml
   litellm:
     config:
       model_list:
         - model_name: llama3
           litellm_params:
             model: ollama/llama3
             api_base: http://ollama:11434
   ```

2. **Backend Service Unavailable**
   ```bash
   # Test backend connectivity
   oc exec -it deployment/litellm -n litellm -- \
     curl -f http://ollama:11434/api/tags
   
   # Check backend service status
   oc get pods -n <backend-namespace>
   ```

3. **API Key Restrictions**
   - Verify API key has access to requested model
   - Check model restrictions in Virtual Keys configuration

### Model Authentication Fails

**Symptoms:**
- Models show as available but requests fail with auth errors
- Provider-specific authentication failures

**Solutions:**

1. **Missing Provider API Keys**
   ```yaml
   # Add provider credentials to values.yaml
   litellm:
     config:
       model_list:
         - model_name: gpt-4
           litellm_params:
             model: azure/gpt-4
             api_base: https://your-endpoint.openai.azure.com/
             api_key: "your-api-key"  # Add this
   ```

2. **Incorrect API Base URLs**
   - Verify provider endpoint URLs
   - Check for typos in configuration

---

## Performance Issues

### Slow Response Times

**Symptoms:**
- High latency for model requests
- UI takes long to load

**Diagnosis:**
```bash
# Check pod resource usage
oc top pods -n litellm

# Check node resource usage
oc top nodes

# Monitor request latency
curl -w "@curl-format.txt" -s -o /dev/null "https://<litellm-route>/health"
```

**Solutions:**

1. **Resource Constraints**
   ```yaml
   # Increase resource limits in values.yaml
   resources:
     limits:
       cpu: "2"
       memory: "4Gi"
     requests:
       cpu: "1"
       memory: "2Gi"
   ```

2. **Database Performance**
   ```bash
   # Check database performance
   oc exec -it deployment/pgvector -n litellm -- \
     psql -U postgres -d litellm -c "SELECT count(*) FROM LiteLLM_SpendLogs;"
   
   # Consider database cleanup for large tables
   ```

3. **Network Latency**
   - Check provider endpoint proximity
   - Consider regional model deployments

---

## Recovery Procedures

### Complete Reset

If issues persist, perform a complete reset:

```bash
# 1. Backup important data
oc exec -it deployment/pgvector -n litellm -- \
  pg_dump -U postgres litellm > backup.sql

# 2. Clean slate
make clean

# 3. Redeploy
make install

# 4. Restore data if needed
oc exec -i deployment/pgvector -n litellm -- \
  psql -U postgres litellm < backup.sql
```

### Emergency Access

If admin UI is inaccessible:

```bash
# Access LiteLLM pod directly
oc exec -it deployment/litellm -n litellm -- bash

# Check configuration
cat /app/litellm_config.yaml

# Restart service
kill 1  # Restart main process
```

---

## Getting Help

### Log Collection

When reporting issues, collect these logs:

```bash
# All pod logs
make logs > litellm-logs.txt

# System events
oc get events -n litellm --sort-by='.lastTimestamp' > events.txt

# Configuration dump
oc get configmaps,secrets -n litellm -o yaml > config.yaml
```

### Useful Debug Commands

```bash
# Check all resources
oc get all -n litellm

# Describe problematic resources
oc describe pod <pod-name> -n litellm

# Check resource quotas
oc describe quota -n litellm

# Test connectivity
oc run debug --rm -it --image=busybox --restart=Never -- sh
```

---

## Related Documentation

- **[Deployment Guide](deploy/DEPLOYMENT.md)** - Complete setup instructions
- **[Usage Guide](USAGE_GUIDE.md)** - How to use the platform
- **[Demo Guides](demos/)** - Feature-specific examples
- **[Configuration Reference](docs/CONFIGURATION.md)** - Detailed configuration options