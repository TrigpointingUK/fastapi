# Auth0 Configuration for Production Environment
#
# This uses the auth0 module to create a complete Auth0 setup
# for the production environment with its own tenant.

module "auth0" {
  source = "../modules/auth0"

  environment = "production"
  name_prefix = "tuk"

  # Auth0 Domains
  auth0_custom_domain = var.auth0_custom_domain

  # Cloudflare Configuration
  cloudflare_zone_name = "trigpointing.uk"

  # Database Connection
  database_connection_name = "tuk-users"

  # API Configuration
  api_name       = "tuk-api"
  api_identifier = "https://api.trigpointing.uk/api/v1/"

  # FastAPI Configuration
  fastapi_url = "https://api.trigpointing.uk"
  m2m_token   = var.auth0_m2m_token

  # Swagger UI Callbacks
  swagger_callback_urls = [
    "https://api.trigpointing.uk/docs/oauth2-redirect",
  ]

  swagger_allowed_origins = [
    "https://api.trigpointing.uk",
  ]

  # Website Callbacks
  website_callback_urls = [
    "https://www.trigpointing.uk/auth/callback",
  ]

  # Forum Callbacks
  forum_callback_urls = [
    "https://www.trigpointing.uk/forum/ucp.php?mode=login",
  ]

  # Wiki Callbacks
  wiki_callback_urls = [
    "https://www.trigpointing.uk/wiki/index.php?title=Special:OAuth2Client/callback",
  ]

  # Android Callbacks
  android_callback_urls = [
    "uk.trigpointing.android://callback",
  ]

  # Optional Apps (enabled for production)
  enable_forum = true
  enable_wiki  = true

  # Role Configuration
  admin_role_name        = "production-admin"
  admin_role_description = "Production Environment Administrators"

  # Email Provider (SES)
  smtp_host     = "email-smtp.eu-west-1.amazonaws.com"
  smtp_port     = 587
  smtp_username = data.terraform_remote_state.common.outputs.auth0_smtp_username
  smtp_password = data.terraform_remote_state.common.outputs.auth0_smtp_password
  from_email    = "noreply@trigpointing.uk"
  from_name     = "Trigpointing UK"

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
  description = "Swagger OAuth2 client ID"
  value       = module.auth0.swagger_client_id
}

output "auth0_website_client_id" {
  description = "Website client ID"
  value       = module.auth0.website_client_id
  sensitive   = true
}

output "auth0_forum_client_id" {
  description = "Forum client ID"
  value       = module.auth0.forum_client_id
  sensitive   = true
}

output "auth0_wiki_client_id" {
  description = "Wiki client ID"
  value       = module.auth0.wiki_client_id
  sensitive   = true
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

