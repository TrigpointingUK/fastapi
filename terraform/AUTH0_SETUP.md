# Auth0 Terraform Setup Guide

This guide walks you through bringing your existing Auth0 configuration under Terraform management.

## Overview

Your Auth0 setup includes:
- **2 Database Connections**: `tme-users`, `tuk-users`
- **3 APIs**: api-tme, api-tuk, fastapi-tuk
- **7 Applications**: android, api-tme, api-tuk, fastapi-tuk, legacy, Swagger UI, TrigpointingUK
- **2 Roles**: tme-admin, tuk-admin
- **New**: Post User Registration Actions (will be created)

## Prerequisites

### 1. Create Terraform M2M Application in Auth0

Before you can use Terraform, you need an M2M application with Management API access:

1. Go to **Auth0 Dashboard** → **Applications** → **Applications**
2. Click **Create Application**
3. Name: `Terraform`
4. Type: **Machine to Machine**
5. Select **Auth0 Management API**
6. Grant the following permissions:
   - `create:clients`, `read:clients`, `update:clients`, `delete:clients`
   - `create:resource_servers`, `read:resource_servers`, `update:resource_servers`, `delete:resource_servers`
   - `create:connections`, `read:connections`, `update:connections`, `delete:connections`
   - `create:roles`, `read:roles`, `update:roles`, `delete:roles`
   - `create:actions`, `read:actions`, `update:actions`, `delete:actions`
   - `create:triggers`, `read:triggers`, `update:triggers`, `delete:triggers`
   - `create:client_grants`, `read:client_grants`, `update:client_grants`, `delete:client_grants`
7. Note the **Client ID** and **Client Secret**

### 2. Set Environment Variables

```bash
export AUTH0_DOMAIN="trigpointing.eu.auth0.com"
export AUTH0_CLIENT_ID="<your-terraform-client-id>"
export AUTH0_CLIENT_SECRET="<your-terraform-client-secret>"

# For the fetch script, you can use the same credentials:
export AUTH0_M2M_CLIENT_ID="$AUTH0_CLIENT_ID"
export AUTH0_M2M_CLIENT_SECRET="$AUTH0_CLIENT_SECRET"
```

## Step-by-Step Setup

### Step 1: Fetch Existing Resource IDs

Run the fetch script to get all your Auth0 resource IDs:

```bash
cd terraform/common
./scripts/fetch-auth0-ids.sh > auth0-ids.txt
```

This will output all your resource IDs. Review `auth0-ids.txt` and note the IDs you'll need.

### Step 2: Update Import Script

Edit `terraform/common/scripts/import-auth0.sh` and replace the placeholder IDs with actual values from Step 1:

```bash
# Find lines like:
terraform import auth0_connection.tme_users "con_XXXXXXXXXX"

# Replace with actual IDs:
terraform import auth0_connection.tme_users "con_abc123def456"
```

Key IDs to update:
- Database connection IDs (con_xxx)
- Resource server IDs (for APIs)
- Role IDs (rol_xxx)

**Note**: Client IDs are already filled in from the information you provided.

### Step 3: Create Terraform Variables File

Create `terraform/common/terraform.tfvars` (this file is .gitignored):

```hcl
# Auth0 Terraform Provider Credentials
auth0_terraform_client_id     = "YOUR_TERRAFORM_CLIENT_ID"
auth0_terraform_client_secret = "YOUR_TERRAFORM_CLIENT_SECRET"

# T:ME Configuration
tme_fastapi_url = "https://api.trigpointing.me"
tme_m2m_token   = "YOUR_TME_M2M_TOKEN"  # Get via client credentials flow

# T:UK Configuration
tuk_fastapi_url = "https://api.trigpointing.uk"
tuk_m2m_token   = "YOUR_TUK_M2M_TOKEN"  # Get via client credentials flow
```

#### Getting M2M Tokens for Actions

The Actions need M2M tokens to call your webhook. Get these tokens:

**For T:ME:**
```bash
curl --request POST \
  --url https://trigpointing.eu.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"7OkFtciXsTEE3glKFwEtyJbIIgxJO7X2",
    "client_secret":"YOUR_API_TME_SECRET",
    "audience":"https://api.trigpointing.me/",
    "grant_type":"client_credentials"
  }'
```

**For T:UK:**
```bash
curl --request POST \
  --url https://trigpointing.eu.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"X4QQSV9ZEqzVww9ffPJr85hzmq0k2iYu",
    "client_secret":"YOUR_API_TUK_SECRET",
    "audience":"https://api.trigpointing.uk/",
    "grant_type":"client_credentials"
  }'
```

**Important**: These tokens expire! Consider implementing token refresh in the Actions or rotating them regularly.

### Step 4: Initialize Terraform

```bash
cd terraform/common
terraform init
```

This will download the Auth0 provider (and update existing providers).

### Step 5: Import Existing Resources

Run the import script:

```bash
./scripts/import-auth0.sh
```

This will import all your existing Auth0 resources into Terraform state.

**Expected Output**: You should see "Import successful" messages for each resource.

**If imports fail**: Check the error messages and verify:
- Resource IDs are correct
- Auth0 credentials have proper permissions
- Resources exist in Auth0

### Step 6: Review Terraform Plan

```bash
terraform plan
```

**What to look for:**
- Most resources should show "No changes"
- Actions and Trigger Actions will show as "to be created" (these are new)
- Minor differences in configuration (e.g., default values) are normal

**If there are unexpected changes:**
- Review `auth0.tf` and adjust configuration to match your actual Auth0 setup
- Some fields may need to be added/removed based on your actual configuration
- Run `terraform plan` again until you're happy with the changes

### Step 7: Review Action Configuration

The Action files are in `terraform/common/actions/`:
- `tme-post-user-registration.js`
- `tuk-post-user-registration.js`

These implement the username collision handling with random 6-digit suffixes as documented.

### Step 8: Apply Terraform Configuration

Once the plan looks good:

```bash
terraform apply
```

This will:
- Create the Post User Registration Actions
- Bind them to the post-user-registration trigger
- Update any configuration differences

## Post-Setup Tasks

### 1. Test the Actions

After applying:

1. Go to **Auth0 Dashboard** → **Actions** → **Library**
2. Find `tme-post-user-registration` and `tuk-post-user-registration`
3. Verify they're deployed and attached to the trigger
4. Check the code matches your expectations
5. Test by registering a new user

### 2. Update AWS Secrets Manager

Add the Auth0 webhook configuration to your FastAPI secrets:

**For staging (T:ME):**
```bash
aws secretsmanager update-secret \
  --secret-id fastapi-staging-app-secrets \
  --secret-string '{
    "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://api.trigpointing.me/",
    "AUTH0_API_IDENTIFIER": "https://api.trigpointing.me/",
    ...other existing secrets...
  }'
```

**For production (T:UK):**
```bash
aws secretsmanager update-secret \
  --secret-id fastapi-production-app-secrets \
  --secret-string '{
    "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://api.trigpointing.uk/",
    "AUTH0_API_IDENTIFIER": "https://api.trigpointing.uk/",
    ...other existing secrets...
  }'
```

### 3. Monitor Action Logs

After deployment, monitor the Action logs in Auth0:

1. **Actions** → **Monitoring**
2. Filter by action name
3. Look for errors or warnings
4. Verify successful user provisioning

## Troubleshooting

### Import Errors

**Problem**: `Error: Cannot import non-existent remote object`

**Solution**: 
- Verify the resource exists in Auth0
- Check the resource ID is correct
- Ensure you have permission to read the resource

### Plan Shows Many Changes

**Problem**: `terraform plan` shows many updates to existing resources

**Solution**:
- This is normal for first-time imports
- Review each change carefully
- Update `auth0.tf` to match your actual configuration
- Some differences (like computed fields) can be ignored

### Action Deployment Fails

**Problem**: Actions fail to deploy or don't appear in trigger

**Solution**:
- Check Action code syntax
- Verify secrets are set correctly
- Ensure axios dependency is added
- Check Auth0 logs for detailed error messages

### M2M Token Expiration

**Problem**: Actions fail with 401 after some time

**Solution**:
- M2M tokens in Action secrets expire
- Implement token refresh in Actions OR
- Rotate tokens regularly (recommended: daily/weekly)
- Consider using a token refresh mechanism

## Next Steps

Once Auth0 is under Terraform control:

1. **Add remaining resources**: Custom domains, branding, email templates
2. **Implement token rotation**: Automate M2M token updates
3. **Environment separation**: Consider separate Auth0 tenants for staging/production
4. **CI/CD integration**: Add Terraform apply to your deployment pipeline
5. **State locking**: Ensure Terraform state is locked during applies

## Resources

- [Auth0 Terraform Provider Docs](https://registry.terraform.io/providers/auth0/auth0/latest/docs)
- [Auth0 Actions Documentation](https://auth0.com/docs/actions)
- [Project Documentation](../docs/auth/auth0-native-registration.md)

## File Structure

```
terraform/common/
├── auth0.tf                              # Auth0 resource definitions
├── main.tf                               # Provider configuration (updated)
├── variables.tf                          # Variables (updated)
├── terraform.tfvars                      # Your secrets (create this, .gitignored)
├── scripts/
│   ├── fetch-auth0-ids.sh               # Fetch resource IDs
│   └── import-auth0.sh                   # Import existing resources
└── actions/
    ├── tme-post-user-registration.js    # T:ME Action
    └── tuk-post-user-registration.js    # T:UK Action
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit `terraform.tfvars`** - it contains secrets
2. **Terraform state contains secrets** - ensure S3 bucket is encrypted and access-controlled
3. **Rotate M2M tokens regularly** - especially those used in Actions
4. **Use AWS Secrets Manager** - for production secrets, not tfvars
5. **Review Action logs** - monitor for security issues or abuse

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Auth0 logs in the dashboard
3. Check FastAPI logs for webhook calls
4. Verify network connectivity (Auth0 → FastAPI)
5. Test webhook manually with curl

