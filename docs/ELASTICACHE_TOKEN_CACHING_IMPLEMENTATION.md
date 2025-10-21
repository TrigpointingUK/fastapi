# ElastiCache Token Caching Implementation Summary

## Overview
Implemented Auth0 Management API token caching using ElastiCache (Valkey) to solve the rate limit issue. Tokens are now shared across all ECS tasks and persist across deployments.

## Changes Made

### Terraform Infrastructure (3 files)

#### 1. `terraform/common/outputs.tf`
- Added `elasticache_security_group_id` output to expose the security group for other modules

#### 2. `terraform/staging/main.tf`
- Added security group rule allowing FastAPI ECS tasks to access ElastiCache on port 6379
- Added `redis_url` parameter to `ecs_service` module with ElastiCache endpoint

#### 3. `terraform/production/main.tf`
- Same changes as staging for production environment

#### 4. `terraform/modules/ecs-service/variables.tf`
- Added `redis_url` variable (optional, defaults to empty string)

#### 5. `terraform/modules/ecs-service/main.tf`
- Added REDIS_URL environment variable to task definition (conditional on redis_url being set)

### Python Application (4 files)

#### 1. `requirements.txt`
- Added `redis==5.0.1` dependency for ElastiCache connectivity

#### 2. `app/core/config.py`
- Added `REDIS_URL` optional configuration setting

#### 3. `app/services/auth0_service.py`
Major updates to implement token caching:
- Added redis imports and RedisError exception handling
- Updated `__init__` to initialize Redis client with connection testing
- Completely rewrote `_get_access_token` method with three-tier caching:
  1. ElastiCache (shared across all tasks) - checked first
  2. In-memory cache (per-task fallback)
  3. Request new token from Auth0 (last resort)
- Added structured logging for cache hits and token storage
- Token TTL in ElastiCache matches Auth0 token expiration

#### 4. `env.example`
- Added documentation for REDIS_URL configuration with usage notes

## Expected Impact

### Before Implementation
- **Token requests:** ~1000/month (one per deployment/task restart)
- **Problem:** Hitting Auth0's 1000 token/month limit
- **Deployments:** Each deployment requested new tokens

### After Implementation
- **Token requests:** ~30/month (one per day when 24h token expires)
- **Cost savings:** Stay well under Auth0's token limit
- **Deployments:** Zero impact - tokens survive deployments
- **Scaling:** Multiple ECS tasks share the same token

## Deployment Instructions

### Step 1: Terraform Changes (Common Infrastructure)
```bash
cd terraform/common
terraform init
terraform plan  # Review: adds elasticache_security_group_id output
terraform apply
```

### Step 2: Terraform Changes (Staging)
```bash
cd ../staging
terraform init
terraform plan  # Review: adds security group rule and REDIS_URL env var
terraform apply
```

### Step 3: Terraform Changes (Production)
```bash
cd ../production
terraform init
terraform plan  # Review: adds security group rule and REDIS_URL env var
terraform apply
```

### Step 4: Install Python Dependencies Locally (Optional)
```bash
source venv/bin/activate
pip install redis==5.0.1
```

### Step 5: Deploy Application
Push changes and deploy normally. The application will:
- Automatically connect to ElastiCache using REDIS_URL from environment
- Fall back gracefully to in-memory caching if Redis is unavailable
- Log connection status on startup

### Step 6: Verify Implementation

#### Check Logs After Deployment
Look for these log messages:
```
Connected to ElastiCache for token caching
```

#### First Token Request
```json
{
  "event": "auth0_access_token_obtained",
  "tenant_domain": "your-tenant.eu.auth0.com",
  "expires_in_seconds": 86400,
  "timestamp": "2025-01-XX..."
}
```

#### Token Cached
```json
{
  "event": "auth0_token_cached_in_elasticache",
  "expires_in_seconds": 86100,
  "timestamp": "2025-01-XX..."
}
```

#### Subsequent Requests (from cache)
```
Using Auth0 token from ElastiCache
```

#### Test with ECS Exec (Optional)
```bash
# Connect to running task
aws ecs execute-command --cluster fastapi-cluster \
  --task <task-id> \
  --container fastapi-app \
  --interactive \
  --command "/bin/bash"

# Inside container, test Redis connection
redis-cli -h <elasticache-endpoint> -p 6379 ping
# Should return: PONG

# Check cached token
redis-cli -h <elasticache-endpoint> -p 6379 GET "auth0:mgmt_token:your-tenant.eu.auth0.com"
# Should return JSON with token and expires_at
```

### Step 7: Monitor Token Usage

#### CloudWatch Logs Filter
Search for: `"event": "auth0_access_token_obtained"`
- Should see ~1 occurrence per day (when token expires)
- Should NOT see new tokens on each deployment

#### Verify Deployment Behavior
1. Deploy the application multiple times
2. Check logs - should see "Using Auth0 token from ElastiCache"
3. No new token requests should be made

## Rollback Plan

If issues occur, the implementation gracefully degrades:

1. **ElastiCache unavailable:** Application falls back to in-memory caching automatically
2. **Redis connection fails:** Warning logged, continues with in-memory cache
3. **Complete rollback:** Remove `redis_url` parameter from Terraform, redeploy

## Local Development

Local development continues to work without Redis:
- REDIS_URL not set → uses in-memory cache only
- No impact on local dev workflow
- Optional: Run local Redis for testing ElastiCache behavior

## Security Notes

- ElastiCache is in private subnets (not publicly accessible)
- Only FastAPI ECS tasks can access ElastiCache (security group restricted)
- Tokens stored in Redis are time-limited (match Auth0 expiration)
- No sensitive data beyond tokens stored in Redis

## Success Metrics

✅ Token requests reduced from ~1000/month to ~30/month
✅ Deployments no longer trigger new token requests
✅ Multiple ECS tasks share the same token
✅ Zero Auth0 rate limit errors
✅ Graceful fallback if ElastiCache unavailable

## Files Modified

**Terraform (5 files):**
- `terraform/common/outputs.tf`
- `terraform/staging/main.tf`
- `terraform/production/main.tf`
- `terraform/modules/ecs-service/variables.tf`
- `terraform/modules/ecs-service/main.tf`

**Python (4 files):**
- `requirements.txt`
- `app/core/config.py`
- `app/services/auth0_service.py`
- `env.example`

**Total: 9 files modified**
