# Staging Auth0 Quick Start Guide

This guide walks you through setting up Auth0 for staging from scratch using the empty tenant you just created.

## Prerequisites

- Empty Auth0 staging tenant created (e.g., `trigpointing-staging.eu.auth0.com`)
- AWS CLI configured with appropriate credentials
- Terraform installed (v1.0+)

## Step 1: Create Terraform Provider M2M Application

1. Log in to your staging Auth0 tenant: https://manage.auth0.com/
2. Navigate to **Applications** → **Create Application**
3. Name: `terraform-provider`
4. Type: **Machine to Machine**
5. Authorise for **Auth0 Management API** with these scopes:
   
   ```
   read:clients
   create:clients
   update:clients
   delete:clients
   read:client_grants
   create:client_grants
   update:client_grants
   delete:client_grants
   read:resource_servers
   create:resource_servers
   update:resource_servers
   delete:resource_servers
   read:connections
   create:connections
   update:connections
   delete:connections
   read:roles
   create:roles
   update:roles
   delete:roles
   read:actions
   create:actions
   update:actions
   delete:actions
   read:triggers
   update:triggers
   ```

6. Note the **Client ID** and **Client Secret**

## Step 2: Configure Terraform Variables

Create `terraform/staging/terraform.tfvars` from the example:

```bash
cd terraform/staging
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and fill in:

```hcl
# Auth0 Configuration
auth0_domain = "trigpointing-staging.eu.auth0.com"
auth0_client_id = "YOUR_TERRAFORM_CLIENT_ID"  # From Step 1
auth0_client_secret = "YOUR_TERRAFORM_CLIENT_SECRET"  # From Step 1

# Temporary token for initial setup (we'll update this later)
auth0_m2m_token = "temporary"

# ... fill in other AWS/container configuration ...
```

## Step 3: Set Environment Variables

```bash
export AUTH0_DOMAIN="trigpointing-staging.eu.auth0.com"
export AUTH0_CLIENT_ID="YOUR_TERRAFORM_CLIENT_ID"
export AUTH0_CLIENT_SECRET="YOUR_TERRAFORM_CLIENT_SECRET"
```

## Step 4: Initialise Terraform

```bash
cd terraform/staging
terraform init -backend-config=backend-staging.conf
```

This will:
- Download the Auth0 provider
- Configure S3 backend for state storage

## Step 5: Review the Plan

```bash
terraform plan
```

You should see Terraform will create approximately:
- 1 database connection (`staging-users`)
- 1 API resource server (`fastapi-staging`)
- 4 client applications (M2M, Swagger, Web, Android)
- 2 client grants (M2M → API, M2M → Management API)
- 1 admin role with permissions
- 1 post-registration Action
- 1 trigger binding

Review carefully to ensure everything looks correct.

## Step 6: Apply Initial Configuration

```bash
terraform apply
```

Type `yes` when prompted.

This will create all the Auth0 resources. The Action will be created but won't work yet because we used a temporary token.

## Step 7: Generate Proper M2M Token

Now that the M2M client has been created, we can generate a proper token.

### Get M2M Credentials

```bash
terraform output auth0_m2m_client_id
terraform output -raw auth0_m2m_client_secret
```

### Generate Token

```bash
M2M_CLIENT_ID=$(terraform output -raw auth0_m2m_client_id)
M2M_CLIENT_SECRET=$(terraform output -raw auth0_m2m_client_secret)

# Get a token (this will last 24 hours)
curl -X POST https://trigpointing-staging.eu.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d "{
    \"client_id\": \"$M2M_CLIENT_ID\",
    \"client_secret\": \"$M2M_CLIENT_SECRET\",
    \"audience\": \"https://api-staging.trigpointing.uk/api/v1/\",
    \"grant_type\": \"client_credentials\"
  }" | jq -r '.access_token'
```

Copy the token from the output.

### Update terraform.tfvars

Edit `terraform/staging/terraform.tfvars` and replace:

```hcl
auth0_m2m_token = "temporary"
```

with:

```hcl
auth0_m2m_token = "eyJ0eXAiOiJKV1QiLCJhbGc..."  # Your actual token
```

### Apply Again

```bash
terraform apply
```

This will update the Action's secrets with the proper token.

## Step 8: Configure FastAPI

Get the necessary outputs:

```bash
terraform output auth0_swagger_client_id
terraform output auth0_api_identifier
terraform output auth0_m2m_client_id
terraform output -raw auth0_m2m_client_secret
```

### Update AWS Secrets Manager

Create or update the `fastapi-staging-app-secrets` secret:

```bash
aws secretsmanager put-secret-value \
  --secret-id fastapi-staging-app-secrets \
  --secret-string '{
    "DATABASE_URL": "mysql+pymysql://user:pass@host/db",
    "AUTH0_DOMAIN": "trigpointing-staging.eu.auth0.com",
    "AUTH0_M2M_CLIENT_ID": "...",
    "AUTH0_M2M_CLIENT_SECRET": "...",
    "AUTH0_API_IDENTIFIER": "https://api-staging.trigpointing.uk/api/v1/",
    "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://api-staging.trigpointing.uk/api/v1/",
    "AUTH0_SWAGGER_CLIENT_ID": "...",
    "AWS_S3_BUCKET": "your-s3-bucket",
    "AWS_S3_REGION": "eu-west-1"
  }'
```

**Important**: The M2M token in the Action will expire after 24 hours. For long-term operation, you'll need to implement token refresh logic or rotate the token regularly.

## Step 9: Deploy FastAPI

Deploy your FastAPI application to staging. The ECS task will pick up the secrets from AWS Secrets Manager.

```bash
# Example deployment (adjust for your setup)
cd ../../
./scripts/deploy.sh staging
```

## Step 10: Test the Setup

### Test 1: Check API Health

```bash
curl https://api-staging.trigpointing.uk/health
```

Should return `{"status": "healthy"}`.

### Test 2: Test Swagger OAuth

1. Visit https://api-staging.trigpointing.uk/docs
2. Click **Authorize**
3. You should be redirected to Auth0 login
4. Try creating a test account

### Test 3: Verify User Provisioning

After creating a test account via Auth0:

1. Check Auth0 Dashboard → Users - user should exist
2. Check FastAPI logs - should show successful provisioning
3. Query your database - user record should exist with:
   - `name` = generated nickname
   - `email` = user's email
   - `auth0_user_id` = Auth0 user ID
   - `cryptpw` = random string
   - `email_valid` = 'Y'

## Troubleshooting

### Error: "Resource already exists"

If you see errors about existing resources, your tenant isn't actually empty. You'll need to import the existing resources. See [AUTH0_SETUP.md](AUTH0_SETUP.md) for import instructions.

### Error: "Invalid credentials"

Double-check your `AUTH0_CLIENT_ID` and `AUTH0_CLIENT_SECRET` from the terraform-provider M2M app.

### Action not triggering

1. Check Auth0 Dashboard → Actions → Flows → Post User Registration
2. The `staging-post-user-registration` Action should be present
3. Check logs in Auth0 Dashboard → Monitoring → Logs

### User not provisioned in database

Check the Action logs in Auth0:

1. Auth0 Dashboard → Monitoring → Logs
2. Look for entries related to `post-user-registration`
3. Check for errors like:
   - Network errors (check FastAPI is accessible from Auth0)
   - Authentication errors (check M2M token is valid)
   - 409 errors (username collision - should retry automatically)

### M2M Token Expired

If the token expires (after 24 hours), the Action will fail. To fix:

1. Generate a new token (Step 7)
2. Update `terraform.tfvars`
3. Run `terraform apply`

For production, consider:
- Using a longer-lived token
- Implementing automatic token refresh in the Action
- Monitoring Action failures and alerting

## Next Steps

1. **Test thoroughly** - Create multiple test accounts, verify provisioning
2. **Set up monitoring** - Watch Auth0 logs and FastAPI logs
3. **Configure production** - Follow [AUTH0_SETUP.md](AUTH0_SETUP.md) for production setup
4. **Implement token refresh** - For production, implement proper M2M token management

## Useful Commands

```bash
# View outputs
terraform output

# View sensitive outputs
terraform output -raw auth0_m2m_client_secret

# Check state
terraform show

# Re-initialise (if you update providers)
terraform init -upgrade

# Validate configuration
terraform validate

# Format Terraform files
terraform fmt -recursive

# View Auth0 resources
terraform state list | grep auth0

# Show specific resource
terraform state show 'module.auth0.auth0_connection.database'
```

## Cleanup (If Needed)

To destroy all Auth0 resources:

```bash
terraform destroy
```

**Warning**: This will delete all users, connections, and configurations! Only do this in staging/dev environments.

## Support

- **Auth0 Docs**: https://auth0.com/docs
- **Terraform Provider**: https://registry.terraform.io/providers/auth0/auth0/latest/docs
- **Module README**: [modules/auth0/README.md](modules/auth0/README.md)
- **Main Setup Guide**: [AUTH0_SETUP.md](AUTH0_SETUP.md)

---

**Created**: October 2025

