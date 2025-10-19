# Auth0 Configuration for Staging Environment
#
# This uses the auth0 module to create a complete Auth0 setup
# for the staging environment with its own tenant.

# ============================================================================
# SES EMAIL IDENTITY
# ============================================================================

# Verify ownership of the staging domain email address
resource "aws_ses_email_identity" "noreply" {
  email = "noreply@trigpointing.me"
}

# ============================================================================
# AUTH0 MODULE
# ============================================================================

module "auth0" {
  source = "../modules/auth0"

  environment = "staging"
  name_prefix = "tme"

  # Auth0 Domains
  auth0_custom_domain = var.auth0_custom_domain

  # Cloudflare Configuration
  cloudflare_zone_name = "trigpointing.me"

  # Database Connection
  database_connection_name = "tme-users"

  # API Configuration
  api_name       = "tme-api"
  api_identifier = "https://api.trigpointing.me/api/v1/"

  # FastAPI Configuration
  fastapi_url = "https://api.trigpointing.me"
  m2m_token   = var.auth0_m2m_token

  # Swagger UI Callbacks
  swagger_callback_urls = [
    "https://api.trigpointing.me/docs/oauth2-redirect",
    "http://localhost:8000/docs/oauth2-redirect",
  ]

  swagger_allowed_origins = [
    "https://api.trigpointing.me",
    "http://localhost:8000",
  ]

  # Website Callbacks
  website_callback_urls = [
    "https://www.trigpointing.me/auth/callback",
    "http://localhost:3000/auth/callback", # Local development
  ]

  # Android Callbacks
  android_callback_urls = [
    "me.trigpointing.android://callback",
  ]

  # Optional Apps (disabled for staging)
  enable_forum = false
  enable_wiki  = false

  # Role Configuration
  admin_role_name        = "staging-admin"
  admin_role_description = "Staging Environment Administrators"

  # Email Provider (SES) - SMTP user created per environment
  smtp_host  = "email-smtp.eu-west-1.amazonaws.com"
  smtp_port  = 587
  from_email = "noreply@trigpointing.me"
  from_name  = "Trigpointing UK (Staging)"

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

output "auth0_m2m_client_id" {
  description = "M2M client ID (for FastAPI AUTH0_M2M_CLIENT_ID)"
  value       = module.auth0.m2m_client_id
  sensitive   = true
}

output "auth0_tenant_domain" {
  description = "Auth0 tenant domain"
  value       = module.auth0.tenant_domain
}

output "auth0_smtp_user_name" {
  description = "IAM username for Auth0 SMTP"
  value       = module.auth0.smtp_user_name
}

output "auth0_smtp_username" {
  description = "Auth0 SMTP username (AWS Access Key ID)"
  value       = module.auth0.smtp_username
  sensitive   = true
}

output "auth0_smtp_password" {
  description = "Auth0 SMTP password"
  value       = module.auth0.smtp_password
  sensitive   = true
}

