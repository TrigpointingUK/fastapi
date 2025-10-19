# Auth0 Configuration for Staging Environment
#
# This uses the auth0 module to create a complete Auth0 setup
# for the staging environment with its own tenant.

module "auth0" {
  source = "../modules/auth0"

  environment = "staging"

  # Database Connection
  database_connection_name = "staging-users"

  # API Configuration
  api_name       = "fastapi-staging"
  api_identifier = "https://api-staging.trigpointing.uk/api/v1/"

  # FastAPI Configuration
  fastapi_url = "https://api-staging.trigpointing.uk"
  m2m_token   = var.auth0_m2m_token

  # Swagger UI Callbacks
  swagger_callback_urls = [
    "https://api-staging.trigpointing.uk/docs/oauth2-redirect",
    "http://localhost:8000/docs/oauth2-redirect",
  ]

  swagger_allowed_origins = [
    "https://api-staging.trigpointing.uk",
    "http://localhost:8000",
  ]

  # Web App Callbacks
  web_app_callback_urls = [
    "https://staging.trigpointing.uk/auth/callback",
    "https://www.trigpointing.uk/forum/ucp.php?mode=login", # Legacy phpBB
    "http://localhost:3000/auth/callback",                  # Local development
  ]

  # Android Callbacks
  android_callback_urls = [
    "uk.trigpointing.android.staging://callback",
  ]

  # Role Configuration
  admin_role_name        = "staging-admin"
  admin_role_description = "Staging Environment Administrators"

  # Enable post-registration Action
  enable_post_registration_action = true
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "auth0_connection_id" {
  description = "Auth0 database connection ID"
  value       = module.auth0.connection_id
}

output "auth0_api_identifier" {
  description = "Auth0 API identifier (for FastAPI AUTH0_API_AUDIENCE)"
  value       = module.auth0.api_identifier
}

output "auth0_swagger_client_id" {
  description = "Swagger UI OAuth2 client ID"
  value       = module.auth0.swagger_client_id
}

output "auth0_m2m_client_id" {
  description = "M2M client ID (for FastAPI AUTH0_M2M_CLIENT_ID)"
  value       = module.auth0.m2m_client_id
  sensitive   = true
}

output "auth0_tenant_domain" {
  description = "Auth0 tenant domain"
  value       = module.auth0.tenant_domain
}

