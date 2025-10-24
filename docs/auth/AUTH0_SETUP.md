# Auth0 Terraform Setup Guide

This guide explains how to set up and manage Auth0 resources using Terraform for the TrigPointing FastAPI application.

## Architecture

The Auth0 infrastructure is managed using a **modular approach**:

- **Module**: `terraform/modules/auth0/` - Reusable module defining all Auth0 resources
- **Staging**: `terraform/staging/auth0.tf` - Staging environment configuration
- **Production**: `terraform/production/auth0.tf` - Production environment configuration

Each environment has its own **separate Auth0 tenant** for complete isolation.

## Module Features

The Auth0 module creates:

1. **Database Connection** - User authentication database
2. **API Resource Server** - API with defined scopes/permissions
3. **Client Applications**:
   - M2M client for API access
   - SPA client for Swagger UI OAuth2
   - Regular web application client
   - Native Android client
4. **RBAC** - Admin role with permissions
5. **Post User Registration Action** - Automated user provisioning webhook

## Prerequisites

### 1. Create Auth0 Tenants

Create separate Auth0 tenants for staging and production:

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Create tenant for staging (e.g., `trigpointing-staging.eu.auth0.com`)
3. Create tenant for production (e.g., `trigpointing-prod.eu.auth0.com`)

### 2. Create Terraform M2M Application (Per Tenant)

For each tenant, create a Machine-to-Machine application for Terraform:

1. Go to Auth0 Dashboard → Applications → Create Application
2. Name: `terraform-provider`
3. Type: Machine to Machine
4. Authorise for **Auth0 Management API** with these scopes:
   ```
   read:clients, create:clients, update:clients, delete:clients
   read:client_grants, create:client_grants, update:client_grants, delete:client_grants
   read:resource_servers, create:resource_servers, update:resource_servers, delete:resource_servers
   read:connections, create:connections, update:connections, delete:connections
   read:roles, create:roles, update:roles, delete:roles
   read:actions, create:actions, update:actions, delete:actions
   read:triggers, update:triggers
   ```

5. Note the **Client ID** and **Client Secret**

### 3. Generate M2M Tokens for Post-Registration Actions

The post-registration Action needs an M2M token to call your FastAPI webhook. For each environment:

**Option A: Generate Token via Auth0 (Manual)**

1. Create another M2M application (e.g., `post-registration-webhook`)
2. Authorise for your API with scopes `api:admin`, `api:write`, `api:read-pii`
3. Get a token from the Test tab
4. **Note**: Tokens expire, so this is only for initial testing

**Option B: Use FastAPI M2M Client (Recommended)**

After Terraform creates your Auth0 resources, you can use the generated M2M client:

```bash
# Get M2M credentials from Terraform output
cd terraform/staging
terraform output auth0_m2m_client_id
terraform output auth0_m2m_client_secret

# Get a token (example using curl)
curl -X POST https://your-tenant.eu.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "YOUR_M2M_CLIENT_ID",
    "client_secret": "YOUR_M2M_CLIENT_SECRET",
    "audience": "https://api.trigpointing.me/api/v1/",
    "grant_type": "client_credentials"
  }'
```

## Initial Setup - Staging Environment

Since your staging tenant is empty, we can create everything from scratch.

### Step 1: Set Environment Variables

```bash
# Staging Auth0 Terraform Provider
export AUTH0_DOMAIN="trigpointing-staging.eu.auth0.com"
export AUTH0_CLIENT_ID="your_terraform_client_id"
export AUTH0_CLIENT_SECRET="your_terraform_client_secret"
```

### Step 2: Create Auth0 Secrets File

Create `terraform/staging/auth0.auto.tfvars` from the example:

```bash
cd terraform/staging
cp auth0.example.tfvars auth0.auto.tfvars
```

Edit `auth0.auto.tfvars`:

```hcl
# Auth0 M2M Token for Post-Registration Action
auth0_m2m_token = "temporary"  # Use temporary value for initial setup
```

**Note**: The `auth0.auto.tfvars` file is gitignored. Auth0 provider credentials come from environment variables (Step 1).

**Note on `auth0_m2m_token`**: For the initial `terraform apply`, use a temporary token. After the first apply, Terraform will create the M2M client. Then:
1. Get a proper token using the created M2M client
2. Update `auth0_m2m_token` in `auth0.auto.tfvars`
3. Run `terraform apply` again to update the Action with the real token

### Step 3: Initialise and Plan

```bash
cd terraform/staging
terraform init
terraform plan
```

Review the plan carefully. It should show creation of:
- 1 database connection
- 1 API resource server
- 4 client applications
- 2 client grants
- 1 role with permissions
- 1 action (if enabled)
- 1 trigger binding (if action enabled)

### Step 4: Apply

```bash
terraform apply
```

### Step 5: Update M2M Token

After the initial apply:

1. Get outputs:
   ```bash
   terraform output auth0_m2m_client_id
   terraform output auth0_m2m_client_secret
   ```

2. Generate a proper M2M token (see Option B above)

3. Update `auth0.auto.tfvars` with the new token

4. Apply again:
   ```bash
   terraform apply
   ```

### Step 6: Configure FastAPI

Update `fastapi-staging-app-secrets` in AWS Secrets Manager:

```bash
aws secretsmanager put-secret-value \
  --secret-id fastapi-staging-app-secrets \
  --secret-string '{
    "AUTH0_DOMAIN": "trigpointing-staging.eu.auth0.com",
    "AUTH0_M2M_CLIENT_ID": "...",  # From terraform output
    "AUTH0_M2M_CLIENT_SECRET": "...",
    "AUTH0_API_IDENTIFIER": "https://api.trigpointing.me/api/v1/",
    "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://api.trigpointing.me/api/v1/",
    "AUTH0_SWAGGER_CLIENT_ID": "..."  # From terraform output
  }'
```

## Production Setup

### Option 1: Fresh Production Tenant (Recommended)

If you have a fresh production tenant, follow the same steps as staging:

```bash
export AUTH0_DOMAIN="trigpointing-prod.eu.auth0.com"
export AUTH0_CLIENT_ID="your_prod_terraform_client_id"
export AUTH0_CLIENT_SECRET="your_prod_terraform_client_secret"

cd terraform/production
terraform init
terraform plan
terraform apply
```

### Option 2: Import Existing Production Resources

If you already have Auth0 resources in production that you want to manage with Terraform, you'll need to import them first.

#### Step 1: Fetch Resource IDs

You'll need to fetch existing resource IDs from Auth0. You can use the Auth0 Management API or the dashboard.

Using the Management API:

```bash
# Get an access token
ACCESS_TOKEN=$(curl -s -X POST https://trigpointing-prod.eu.auth0.com/oauth/token \
  -H 'Content-Type: application/json' \
  -d '{
    "client_id": "YOUR_TERRAFORM_CLIENT_ID",
    "client_secret": "YOUR_TERRAFORM_CLIENT_SECRET",
    "audience": "https://trigpointing-prod.eu.auth0.com/api/v2/",
    "grant_type": "client_credentials"
  }' | jq -r '.access_token')

# List clients
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://trigpointing-prod.eu.auth0.com/api/v2/clients | jq '.[] | {name, client_id}'

# List resource servers
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://trigpointing-prod.eu.auth0.com/api/v2/resource-servers | jq '.[] | {name, id, identifier}'

# List connections
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://trigpointing-prod.eu.auth0.com/api/v2/connections | jq '.[] | {name, id}'

# List roles
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://trigpointing-prod.eu.auth0.com/api/v2/roles | jq '.[] | {name, id}'

# List actions
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://trigpointing-prod.eu.auth0.com/api/v2/actions/actions | jq '.actions[] | {name, id}'
```

#### Step 2: Import Resources

```bash
cd terraform/production

# Database connection
terraform import 'module.auth0.auth0_connection.database' con_XXXXXXXXXX

# API resource server
terraform import 'module.auth0.auth0_resource_server.api' XXXXXXXXXX

# Clients
terraform import 'module.auth0.auth0_client.m2m_api' XXXXXXXXXX
terraform import 'module.auth0.auth0_client.swagger_ui' XXXXXXXXXX
terraform import 'module.auth0.auth0_client.web_app' XXXXXXXXXX
terraform import 'module.auth0.auth0_client.android' XXXXXXXXXX

# Client grants
terraform import 'module.auth0.auth0_client_grant.m2m_to_api' cgr_XXXXXXXXXX
terraform import 'module.auth0.auth0_client_grant.m2m_to_mgmt_api' cgr_XXXXXXXXXX

# Role
terraform import 'module.auth0.auth0_role.admin' rol_XXXXXXXXXX
terraform import 'module.auth0.auth0_role_permissions.admin_perms' rol_XXXXXXXXXX

# Action (if it exists)
terraform import 'module.auth0.auth0_action.post_user_registration[0]' XXXXXXXXXX
```

#### Step 3: Verify and Apply

```bash
terraform plan  # Should show no changes if import was successful
terraform apply
```

## Directory Structure

```
terraform/
├── modules/
│   └── auth0/                      # Reusable Auth0 module
│       ├── main.tf                 # Module resources
│       ├── variables.tf            # Module inputs
│       ├── outputs.tf              # Module outputs
│       ├── README.md               # Module documentation
│       └── actions/
│           └── post-user-registration.js.tpl  # Action code template
├── staging/
│   ├── auth0.tf                    # Staging Auth0 configuration
│   ├── providers.tf                # Staging providers (inc. Auth0)
│   └── variables.tf                # Staging variables
├── production/
│   ├── auth0.tf                    # Production Auth0 configuration
│   ├── providers.tf                # Production providers (inc. Auth0)
│   └── variables.tf                # Production variables
└── AUTH0_SETUP.md                  # This file
```

## Customising the Configuration

### Modifying Callback URLs

Edit the respective environment's `auth0.tf`:

```hcl
module "auth0" {
  source = "../modules/auth0"
  
  # ... other config ...
  
  web_app_callback_urls = [
    "https://staging.trigpointing.uk/auth/callback",
    "http://localhost:3000/auth/callback",
    "https://new-callback-url.com/callback",  # Add new URL
  ]
}
```

### Adding API Scopes

Edit `terraform/modules/auth0/main.tf`:

```hcl
resource "auth0_resource_server" "api" {
  # ... existing config ...
  
  scopes {
    value       = "new:scope"
    description = "New permission"
  }
}
```

Then update permissions in the admin role if needed.

### Disabling the Post-Registration Action

In the environment's `auth0.tf`:

```hcl
module "auth0" {
  # ... other config ...
  enable_post_registration_action = false
}
```

## Managing State

Terraform state is stored in S3:

- **Staging**: `s3://tuk-terraform-state/fastapi-staging-eu-west-1/terraform.tfstate`
- **Production**: `s3://tuk-terraform-state/fastapi-production-eu-west-1/terraform.tfstate`

State includes sensitive data like client secrets. Ensure S3 bucket:
- Has encryption enabled
- Has versioning enabled
- Has restricted access

## Security Best Practices

1. **Never commit sensitive values** to Git:
   - Use `.tfvars` files locally (add to `.gitignore`)
   - Use environment variables
   - Store production secrets in AWS Secrets Manager

2. **Rotate credentials regularly**:
   - M2M tokens
   - Client secrets
   - Terraform provider credentials

3. **Principle of least privilege**:
   - Give Terraform provider only necessary Management API scopes
   - Give M2M clients only necessary API scopes

4. **Review Terraform plans** before applying in production

5. **Use separate tenants** for staging and production (already configured!)

## Troubleshooting

### Error: Resource Already Exists

If you see errors about resources already existing, you need to import them first (see "Import Existing Production Resources" above).

### Error: Invalid Credentials

Check your Auth0 provider credentials:

```bash
echo $AUTH0_DOMAIN
echo $AUTH0_CLIENT_ID
# Don't echo CLIENT_SECRET!
```

Verify the M2M application has necessary Management API permissions.

### Action Not Deploying

Check the Action code in `modules/auth0/actions/post-user-registration.js.tpl` for syntax errors.

View Action logs in Auth0 Dashboard → Monitoring → Logs.

### Client Grant Issues

Client grants can be tricky to import. If you encounter issues:

1. Delete the grant manually in Auth0 Dashboard
2. Let Terraform recreate it
3. Run `terraform apply`

## Module Documentation

For detailed module documentation, see [terraform/modules/auth0/README.md](modules/auth0/README.md).

## Related Documentation

- [Auth0 Native Registration Guide](../docs/auth/auth0-native-registration.md)
- [Auth0 Terraform Provider](https://registry.terraform.io/providers/auth0/auth0/latest/docs)
- [Parameter Store Setup](../docs/parameter-store-setup.md)

## Maintenance

### Regular Tasks

- Review and rotate M2M tokens monthly
- Review client configurations quarterly
- Update Action code as needed
- Monitor Action execution in Auth0 logs

### Terraform Updates

To update the Auth0 provider:

```bash
cd terraform/staging  # or production
terraform init -upgrade
terraform plan
terraform apply
```

### Disaster Recovery

State files are versioned in S3. To recover from a bad apply:

```bash
# List state file versions
aws s3api list-object-versions \
  --bucket tuk-terraform-state \
  --prefix fastapi-staging-eu-west-1/terraform.tfstate

# Download a previous version
aws s3api get-object \
  --bucket tuk-terraform-state \
  --key fastapi-staging-eu-west-1/terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate.backup
```

Then restore and re-apply.

## Support

For issues or questions:
1. Check [Auth0 Community](https://community.auth0.com/)
2. Review [Terraform Auth0 Provider Issues](https://github.com/auth0/terraform-provider-auth0/issues)
3. Check application logs in Auth0 Dashboard

---

**Last Updated**: October 2025
