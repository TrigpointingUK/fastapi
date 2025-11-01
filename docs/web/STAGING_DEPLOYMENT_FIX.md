# Staging Deployment Issues - Fix Guide

## Current Status

### Issue 1: Stats Endpoint Returns 404 ❌
```bash
$ curl https://api.trigpointing.me/v1/stats/site
{"detail":"Not Found"}
```

**Cause:** The new code hasn't been deployed to staging yet.

**What's in staging:** The last commit was "scaffolding web app" which doesn't include the stats endpoint.

### Issue 2: CORS Error on Logs Endpoint ❌  
```
https://api.trigpointing.me/v1/logs?limit=10&order=-upd_timestamp&include=photos
```

Getting CORS error when accessed from `https://trigpointing.me`

**Status:** CORS configuration looks correct in Terraform, but needs verification after deployment.

## Resolution Steps

### Step 1: Commit and Push All Changes ✅

You have uncommitted changes that need to be pushed:

```bash
cd /home/ianh/dev/platform

# Check current status
git status

# You should see:
# M  web/.gitignore
# A  web/src/components/logs/LogCard.tsx
# A  web/src/components/logs/LogList.tsx

# Commit everything
git add -A
git commit -m "Implement React homepage and photo album with Tailwind CSS

Features:
- Add Tailwind CSS v4 with custom green palette
- Create 13 React components (layout, ui, logs, photos)
- Implement homepage with stats, news, and recent logs
- Implement infinite scrolling photo album
- Add backend /v1/stats/site endpoint with Redis caching
- Fix gitignore to allow components/logs/ directory

Fixes:
- Remove unused sqlalchemy.func import
- Add type check for Redis cached data
- Configure CORS for local development
- Add /v1/stats/site to public endpoints"

# Push to develop
git push origin develop
```

### Step 2: Monitor GitHub Actions Deployment

After pushing, GitHub Actions will:

1. **Build Web App** (~2-3 minutes)
   - Install dependencies
   - Run type checking
   - Build production bundle
   - Create Docker image
   - Push to ghcr.io/trigpointinguk/platform/web:develop

2. **Build API** (~2-3 minutes)
   - Run linting
   - Run tests
   - Create Docker image
   - Push to ghcr.io/trigpointinguk/fastapi:develop

3. **Deploy to Staging** (handled by ECS)
   - ECS will automatically pull new images
   - Rolling update with zero downtime
   - Takes ~5 minutes for service to stabilize

**Monitor:** https://github.com/[your-org]/platform/actions

### Step 3: Verify Deployment

Once GitHub Actions completes successfully:

#### Verify Stats Endpoint:
```bash
# Should return JSON with site statistics
curl https://api.trigpointing.me/v1/stats/site

# Expected response:
{
  "total_trigs": 25810,
  "total_users": 14682,
  "total_logs": 468414,
  "total_photos": 402671,
  "recent_logs_7d": 123,
  "recent_users_30d": 5
}
```

#### Verify Frontend:
```bash
# Visit in browser
https://trigpointing.me/

# Should show:
- New homepage with Tailwind styling
- Site statistics
- Recent news
- Recent logs with photos
```

#### Verify Photo Album:
```bash
https://trigpointing.me/photos

# Should show:
- Infinite scrolling photo grid
- Photos loading as you scroll
```

### Step 4: Verify CORS is Working

Open browser DevTools (F12) and navigate to:
```
https://trigpointing.me/
```

Check the Network tab - API requests should:
- ✅ Return 200 status
- ✅ Have CORS headers:
  - `Access-Control-Allow-Origin: https://trigpointing.me`
  - `Access-Control-Allow-Methods: *`
  - `Access-Control-Allow-Headers: *`

## If Issues Persist

### Stats Endpoint Still 404

**Check ECS deployment:**
```bash
# Using AWS CLI
aws ecs list-tasks --cluster trigpointing-staging-cluster --service-name fastapi-staging-service --region eu-west-1

# Get task details
aws ecs describe-tasks --cluster trigpointing-staging-cluster --tasks <task-arn> --region eu-west-1
```

**Check if new image was pulled:**
- Look at `image` field in task definition
- Should be: `ghcr.io/trigpointinguk/fastapi:develop`
- Check the image digest - it should be recent

**Check CloudWatch logs:**
```bash
aws logs tail /ecs/trigpointing-staging-fastapi --follow --region eu-west-1
```

Look for:
- Startup messages showing all routes registered
- Should see: "Route: GET /v1/stats/site"

### CORS Still Failing

**Verify Terraform configuration is applied:**

```bash
cd /home/ianh/dev/platform/terraform/staging

# Check current state
terraform show | grep -A5 BACKEND_CORS_ORIGINS

# Should show:
# BACKEND_CORS_ORIGINS = ["https://trigpointing.me", "https://api.trigpointing.me"]
```

**If CORS config is wrong, update and apply:**
```bash
cd /home/ianh/dev/platform/terraform/staging

# Edit staging.auto.tfvars if needed
nano staging.auto.tfvars

# Apply changes
terraform plan
terraform apply
```

**Force ECS to redeploy:**
```bash
# Force new deployment to pick up environment changes
aws ecs update-service \
  --cluster trigpointing-staging-cluster \
  --service fastapi-staging-service \
  --force-new-deployment \
  --region eu-west-1
```

## Current Terraform Configuration

From `terraform/staging/staging.auto.tfvars`:

```hcl
cors_origins = ["https://trigpointing.me", "https://api.trigpointing.me"]
```

This is **correct** - includes the frontend URL needed for CORS.

## Verification Commands

### Check API is running:
```bash
curl https://api.trigpointing.me/health
```

### Check what routes are registered:
```bash
curl https://api.trigpointing.me/docs
```

Browse to the Swagger UI and check if `/v1/stats/site` is listed.

### Test from frontend origin:
```bash
curl -H "Origin: https://trigpointing.me" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://api.trigpointing.me/v1/logs?limit=10
```

Should return CORS headers.

## Timeline

After you push:
- **T+0:** Push to develop
- **T+3min:** GitHub Actions completes builds
- **T+8min:** ECS completes rolling update
- **T+10min:** Everything should be working

## Checklist

Before testing:
- [ ] All changes committed locally
- [ ] Pushed to origin/develop
- [ ] GitHub Actions build successful (check Actions tab)
- [ ] Wait 10 minutes for ECS deployment
- [ ] Clear browser cache
- [ ] Test stats endpoint
- [ ] Test frontend homepage
- [ ] Test photo album
- [ ] Check browser console for CORS errors

## Expected Behavior After Deployment

### Homepage (https://trigpointing.me/)
- ✅ Green Tailwind styling
- ✅ Header with logo and navigation
- ✅ Site stats showing real numbers
- ✅ Recent news (3 items)
- ✅ Recent logs with photo thumbnails
- ✅ Sidebar on desktop, hidden on mobile

### Photo Album (https://trigpointing.me/photos)
- ✅ Grid of photos (2/3/4 columns responsive)
- ✅ Infinite scroll - new photos load automatically
- ✅ Photo counter showing progress
- ✅ Smooth loading animations

### API (https://api.trigpointing.me/)
- ✅ GET /v1/stats/site returns site statistics
- ✅ CORS headers on all responses
- ✅ No authentication required for stats endpoint
- ✅ Swagger docs updated with new endpoint

---

**Status:** Ready to deploy after commit + push ✅

**Next Action:** Run the commands in Step 1 to commit and push your changes.

