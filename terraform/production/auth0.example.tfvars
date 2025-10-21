# Auth0 Configuration for Production (trigpointing.uk)
#
# Copy this file to auth0.auto.tfvars and fill in the actual values
# DO NOT COMMIT auth0.auto.tfvars - it's gitignored
#
# Naming convention matches staging for consistency

# Auth0 Tenant Domain (for Management API)
# This is the default Auth0 domain, e.g., trigpointing.eu.auth0.com
auth0_tenant_domain = "trigpointing.eu.auth0.com"

# Auth0 Custom Domain (for user-facing authentication)
# This is your branded domain, e.g., auth.trigpointing.uk
auth0_custom_domain = "auth.trigpointing.uk"

# Terraform Provider Credentials (for Terraform to manage Auth0)
# These are for the Terraform Management M2M application (NOT the FastAPI M2M app)
auth0_terraform_client_id     = "YOUR_TERRAFORM_PROVIDER_CLIENT_ID"
auth0_terraform_client_secret = "YOUR_TERRAFORM_PROVIDER_CLIENT_SECRET"

# FastAPI M2M Client Secret
# This is the secret from your existing tuk-api M2M client (used by FastAPI)
auth0_m2m_client_secret = "YOUR_FASTAPI_M2M_CLIENT_SECRET"

