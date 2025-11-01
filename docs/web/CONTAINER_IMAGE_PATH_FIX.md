# Fix: Container Image Path After Repository Rename

## Issue

After the GitHub repository was renamed from `fastapi` to `platform`, the CI/CD pipeline started building images to a new path, but Terraform was still trying to pull from the old path.

**Building to (new):**
```
ghcr.io/trigpointinguk/platform/api:develop
ghcr.io/trigpointinguk/platform/api:main
ghcr.io/trigpointinguk/platform/web:develop
ghcr.io/trigpointinguk/platform/web:main
```

**Deploying from (old):**
```
ghcr.io/trigpointinguk/fastapi:develop  ❌
ghcr.io/trigpointinguk/fastapi:main     ❌
```

This meant new builds weren't being deployed!

## Fix Applied

Updated Terraform configuration files to use the new image paths:

### Files Modified:

1. **`terraform/staging/staging.auto.tfvars`**
   ```diff
   - container_image = "ghcr.io/trigpointinguk/fastapi:develop"
   + container_image = "ghcr.io/trigpointinguk/platform/api:develop"
   ```

2. **`terraform/production/production.auto.tfvars`**
   ```diff
   - container_image = "ghcr.io/trigpointinguk/fastapi:main"
   + container_image = "ghcr.io/trigpointinguk/platform/api:main"
   ```

## Deployment Steps

### 1. Commit and Push Changes

```bash
cd /home/ianh/dev/platform

git add terraform/staging/staging.auto.tfvars
git add terraform/production/production.auto.tfvars

git commit -m "Fix: Update container image paths after repository rename

- Update staging to use ghcr.io/trigpointinguk/platform/api:develop
- Update production to use ghcr.io/trigpointinguk/platform/api:main
- Fixes deployment issue where ECS was pulling old image path"

git push origin develop
```

### 2. Apply Terraform Changes to Staging

```bash
cd /home/ianh/dev/platform/terraform/staging

# Review the changes
terraform plan

# Should show:
# ~ container_image = "ghcr.io/trigpointinguk/fastapi:develop" -> "ghcr.io/trigpointinguk/platform/api:develop"

# Apply the changes
terraform apply
```

This will:
1. Update the ECS task definition to use the new image path
2. Trigger a new deployment
3. ECS will pull the latest `platform/api:develop` image
4. Your new code (with stats endpoint) will be deployed!

### 3. Verify Deployment

After Terraform apply completes (~5-10 minutes):

```bash
# Test the stats endpoint
curl https://api.trigpointing.me/v1/stats/site

# Should now return JSON with site statistics!
```

### 4. Check ECS Service

```bash
# View the task definition
aws ecs describe-task-definition \
  --task-definition trigpointing-staging \
  --region eu-west-1 \
  --query 'taskDefinition.containerDefinitions[0].image'

# Should show: "ghcr.io/trigpointinguk/platform/api:develop"
```

## Why This Happened

When a GitHub repository is renamed:
- The repository URL changes: `github.com/TrigpointingUK/fastapi` → `github.com/TrigpointingUK/platform`
- GitHub Container Registry paths change: `ghcr.io/trigpointinguk/fastapi` → `ghcr.io/trigpointinguk/platform`
- CI/CD workflows automatically use `${{ github.repository }}` which picks up the new name
- But Terraform configuration is hardcoded and needs manual updates

## Prevention

To avoid this in the future, consider:

1. **Use Terraform variables** instead of hardcoded image names
2. **Document the image path** in a central location
3. **Add a validation check** in CI/CD to ensure Terraform is pulling the right image
4. **Monitor deployments** to catch mismatches early

## Status

- ✅ Terraform configurations updated
- ⏳ Pending: `terraform apply` in staging
- ⏳ Pending: Verification that stats endpoint works
- ⏳ Future: Apply same changes to production when ready

## Related Files

**GitHub Actions Workflows:**
- `.github/workflows/ci.yml` - Builds API to `platform/api:develop` and `platform/api:main`
- `.github/workflows/web-build.yml` - Builds web to `platform/web:develop` and `platform/web:main`

**Terraform Configuration:**
- `terraform/staging/staging.auto.tfvars` - Staging image paths
- `terraform/production/production.auto.tfvars` - Production image paths

## Timeline

After running `terraform apply`:
- **T+0:** Apply starts
- **T+2min:** New task definition registered
- **T+3min:** ECS starts pulling new image
- **T+5min:** New tasks start running
- **T+7min:** Old tasks drain and stop
- **T+8min:** Deployment complete
- **T+8min:** Test `/v1/stats/site` endpoint ✅

---

**Next Action:** Run `terraform apply` in staging directory to deploy the corrected configuration.

