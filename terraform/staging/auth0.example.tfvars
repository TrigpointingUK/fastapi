# Auth0 Configuration for Staging (trigpointing.me)
#
# Copy this file to auth0.auto.tfvars and fill in the actual values
# DO NOT COMMIT auth0.auto.tfvars - it's gitignored
#
# Auth0 Provider Credentials (for Terraform to manage Auth0)
# These should be set via environment variables instead:
#   export AUTH0_DOMAIN="your-staging-tenant.eu.auth0.com"
#   export AUTH0_CLIENT_ID="your_terraform_m2m_client_id"
#   export AUTH0_CLIENT_SECRET="your_terraform_m2m_client_secret"
#
# Alternatively, you can set them here (not recommended):
# auth0_domain        = "your-staging-tenant.eu.auth0.com"
# auth0_client_id     = "your_terraform_m2m_client_id"
# auth0_client_secret = "your_terraform_m2m_client_secret"

# Auth0 M2M Token for Post-Registration Action
# This token is used by the Auth0 Action to authenticate to your FastAPI webhook
# Generate this after first terraform apply using the created M2M client
auth0_m2m_token = "YOUR_M2M_TOKEN_HERE"

