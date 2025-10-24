# Auth0 Terraform Module

This Terraform module manages a complete Auth0 tenant setup for the TrigPointing application, including database connections, API resource servers, client applications, roles, and post-registration Actions.

## Features

- **Database Connection**: Auth0 database connection for user authentication
- **API Resource Server**: API with defined scopes/permissions
- **Client Applications**:
  - M2M client for API access
  - SPA client for Swagger UI OAuth2
  - Regular web application client
  - Native Android client
- **RBAC**: Admin role with permissions
- **Post User Registration Action**: Automated user provisioning webhook to FastAPI
- **Custom Email Provider**: AWS SES SMTP integration with per-environment IAM users
- **Custom Domain**: Auth0 custom domain with automatic SSL certificate management

## Architecture

Each environment (staging/production) gets:
- Its own Auth0 tenant
- Isolated user database
- Environment-specific API identifiers
- Separate callback URLs
- Independent post-registration Actions
- **Dedicated SES SMTP IAM user** for credential isolation and security

### Email Provider Architecture

This module creates a dedicated AWS IAM user per environment for SES SMTP access. This provides:

- **Security Isolation**: Staging credentials are completely separate from production
- **Independent Credential Rotation**: Rotate staging without affecting production
- **Granular IAM Policies**: Each IAM user is restricted to send from only its environment's email address
- **Cost Attribution**: Separate CloudWatch metrics and AWS Cost Explorer tracking
- **Environment Independence**: Each environment can be torn down without affecting others

The email identities (`noreply@trigpointing.uk`, `noreply@trigpointing.me`) remain in common infrastructure as they're shared AWS resources that need verification.

## Usage

### Staging Example

```hcl
module "auth0" {
  source = "../modules/auth0"

  environment = "staging"

  # Database Connection
  database_connection_name = "staging-users"

  # API Configuration
  api_name       = "tme-api"
  api_identifier = "https://api.trigpointing.me/api/v1/"

  # FastAPI Configuration
  fastapi_url = "https://api.trigpointing.me"
  # M2M authentication uses client credentials (automatically configured)

  # Swagger UI Callbacks
  swagger_callback_urls = [
    "https://api.trigpointing.me/docs/oauth2-redirect",
    "http://localhost:8000/docs/oauth2-redirect",
  ]

  swagger_allowed_origins = [
    "https://api.trigpointing.me",
    "http://localhost:8000",
  ]

  # Web App Callbacks
  web_app_callback_urls = [
    "https://www.trigpointing.me/auth/callback",
    "http://localhost:3000/auth/callback",
  ]

  # Android Callbacks
  android_callback_urls = [
    "me.trigpointing.android://callback",
  ]

  # Role Configuration - uses module defaults:
  # - api-admin: Full FastAPI administrative access
  # - wiki-admin: MediaWiki sysop access
  # - forum-admin: phpBB administrator access

  # Enable post-registration Action
  enable_post_registration_action = true
}
```

## Variables

| Name | Description | Type | Required | Default |
|------|-------------|------|----------|---------|
| `environment` | Environment name (staging or production) | `string` | Yes | - |
| `database_connection_name` | Name of the Auth0 database connection | `string` | Yes | - |
| `api_name` | Name of the API resource server | `string` | Yes | - |
| `api_identifier` | API identifier (audience) | `string` | Yes | - |
| `fastapi_url` | FastAPI base URL for webhook | `string` | Yes | - |
| `m2m_token` | M2M token for post-registration Action | `string` (sensitive) | Yes | - |
| `swagger_callback_urls` | List of Swagger OAuth2 callback URLs | `list(string)` | No | `[]` |
| `swagger_allowed_origins` | List of allowed origins for Swagger UI | `list(string)` | No | `[]` |
| `web_app_callback_urls` | List of web application callback URLs | `list(string)` | No | `[]` |
| `android_callback_urls` | List of Android app callback URLs | `list(string)` | No | `[]` |
| `enable_post_registration_action` | Enable post-registration Action | `bool` | No | `true` |
| `api_admin_role_name` | Name of the API admin role | `string` | No | `"api-admin"` |
| `wiki_admin_role_name` | Name of the wiki admin role | `string` | No | `"wiki-admin"` |
| `forum_admin_role_name` | Name of the forum admin role | `string` | No | `"forum-admin"` |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| `connection_id` | Auth0 database connection ID | No |
| `connection_name` | Auth0 database connection name | No |
| `api_id` | Auth0 API resource server ID | No |
| `api_identifier` | Auth0 API identifier (audience) | No |
| `m2m_client_id` | M2M client ID | Yes |
| `m2m_client_secret` | M2M client secret | Yes |
| `swagger_client_id` | Swagger UI client ID | No |
| `web_app_client_id` | Web application client ID | Yes |
| `android_client_id` | Android client ID | Yes |
| `admin_role_id` | Admin role ID | No |
| `action_id` | Post User Registration Action ID | No |
| `tenant_domain` | Auth0 tenant domain | No |

## Post User Registration Action

The module includes an Action that runs after user registration:

1. Generates a nickname from the user's email prefix
2. Attempts to create the user in FastAPI via `POST /v1/users`
3. On username collision (409 response):
   - Appends a random 6-digit number to the nickname
   - Retries up to 10 times
4. Sets the final nickname in Auth0 user metadata

### Action Requirements

The Action requires two secrets:
- `FASTAPI_URL`: Base URL of your FastAPI application
- `M2M_TOKEN`: Authentication token for the webhook

### Disabling the Action

To disable the post-registration Action:

```hcl
module "auth0" {
  # ... other configuration ...
  enable_post_registration_action = false
}
```

## Provider Requirements

This module requires the Auth0 Terraform provider:

```hcl
terraform {
  required_providers {
    auth0 = {
      source  = "auth0/auth0"
      version = "~> 1.0"
    }
  }
}

provider "auth0" {
  domain        = var.auth0_domain
  client_id     = var.auth0_client_id
  client_secret = var.auth0_client_secret
}
```

## Setting Up Auth0 Provider Credentials

### 1. Create M2M Application in Auth0

1. Go to Auth0 Dashboard → Applications → Create Application
2. Name: `terraform-provider`
3. Type: Machine to Machine
4. Authorise for Auth0 Management API with these scopes:
   - `read:clients`, `create:clients`, `update:clients`, `delete:clients`
   - `read:resource_servers`, `create:resource_servers`, `update:resource_servers`, `delete:resource_servers`
   - `read:connections`, `create:connections`, `update:connections`, `delete:connections`
   - `read:roles`, `create:roles`, `update:roles`, `delete:roles`
   - `read:actions`, `create:actions`, `update:actions`, `delete:actions`
   - `read:client_grants`, `create:client_grants`, `update:client_grants`, `delete:client_grants`

### 2. Set Environment Variables

```bash
export AUTH0_DOMAIN="your-tenant.eu.auth0.com"
export AUTH0_CLIENT_ID="your_terraform_client_id"
export AUTH0_CLIENT_SECRET="your_terraform_client_secret"
```

Or pass via Terraform variables:

```bash
terraform plan -var="auth0_domain=..." -var="auth0_client_id=..." -var="auth0_client_secret=..."
```

## Secrets Management

### Local Development

Use `.tfvars` files for local testing (never commit sensitive data):

```hcl
# staging.tfvars (DO NOT COMMIT)
auth0_domain        = "myapp-staging.eu.auth0.com"
auth0_client_id     = "..."
auth0_client_secret = "..."
```

**Note:** The `auth0_m2m_token` variable has been removed. M2M authentication now uses dynamic client credentials flow automatically.

### Production/Staging Deployment

Store sensitive values in AWS Secrets Manager:

```bash
# Add to tme-app-secrets
aws secretsmanager put-secret-value \
  --secret-id tme-app-secrets \
  --secret-string '{
    "AUTH0_DOMAIN": "myapp-staging.eu.auth0.com",
    "AUTH0_M2M_CLIENT_ID": "...",
    "AUTH0_M2M_CLIENT_SECRET": "...",
    "AUTH0_API_IDENTIFIER": "https://api.trigpointing.me/api/v1/",
    "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://api.trigpointing.me/api/v1/"
  }'
```

## Related Documentation

- [Auth0 Native Registration Guide](../../docs/auth/auth0-native-registration.md)
- [Auth0 Setup Guide](../AUTH0_SETUP.md)
- [Auth0 Terraform Provider Docs](https://registry.terraform.io/providers/auth0/auth0/latest/docs)

## Maintenance

### Updating the Action

The Action code is stored in `actions/post-user-registration.js.tpl`. To update:

1. Edit the template file
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to deploy

The Action will be redeployed automatically when the code changes.

### Rotating M2M Tokens

The `m2m_token` used by the Action should be rotated regularly:

1. Generate a new token in FastAPI
2. Update the variable in your deployment
3. Apply Terraform changes
4. The Action's secrets will be updated automatically

## Troubleshooting

### Action Not Triggering

Check the Auth0 Dashboard → Actions → Triggers → Post User Registration to ensure the Action is properly bound.

### Webhook Failures

Check the Action logs in Auth0 Dashboard → Monitoring → Logs for detailed error messages.

### Token Authentication Issues

Verify the M2M token has the correct audience and permissions in FastAPI.

## License

See [LICENSE](../../../LICENSE) in the repository root.

