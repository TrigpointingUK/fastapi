# Auth0 Module - Manages Auth0 resources for a single environment
#
# This module creates:
# - Database connection for user authentication
# - API resource server with scopes
# - M2M client for API access
# - SPA client for Swagger UI
# - Regular web application client
# - Native Android client
# - Admin role with permissions
# - Post User Registration Action (optional)

terraform {
  required_providers {
    auth0 = {
      source  = "auth0/auth0"
      version = "~> 1.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# Handle resource renames (prevents destroy/create cycles)
moved {
  from = auth0_client.swagger_ui
  to   = auth0_client.swagger
}

moved {
  from = auth0_client.web_app
  to   = auth0_client.website
}

# ============================================================================
# DATABASE CONNECTION
# ============================================================================
# Note: The default 'Username-Password-Authentication' connection should be
# manually deleted in the Auth0 dashboard to avoid confusion.

resource "auth0_connection" "database" {
  name     = var.database_connection_name
  strategy = "auth0"

  options {
    password_policy = "good"
    password_history {
      enable = true
      size   = 5
    }
    password_no_personal_info {
      enable = true
    }
    password_dictionary {
      enable = true
    }
    password_complexity_options {
      min_length = 8
    }
    brute_force_protection = true

    # Configuration settings
    disable_signup    = false
    requires_username = false # Use nickname instead (allows spaces, special chars)

    # Validation
    import_mode          = false
    non_persistent_attrs = []
  }
}

# Enable connection for all our clients
resource "auth0_connection_clients" "database_clients" {
  connection_id = auth0_connection.database.id

  enabled_clients = concat(
    [
      auth0_client.m2m_api.id,
      auth0_client.swagger.id,
      auth0_client.website.id,
      auth0_client.android.id,
    ],
    var.enable_forum ? [auth0_client.forum[0].id] : [],
    var.enable_wiki ? [auth0_client.wiki[0].id] : [],
  )
}

# ============================================================================
# API RESOURCE SERVER
# ============================================================================

resource "auth0_resource_server" "api" {
  name       = var.api_name
  identifier = var.api_identifier

  # Token settings
  token_lifetime = 86400 # 24 hours
  signing_alg    = "RS256"

  # RBAC
  enforce_policies                                = true
  token_dialect                                   = "access_token_authz"
  skip_consent_for_verifiable_first_party_clients = true
}

# Define API scopes/permissions
resource "auth0_resource_server_scopes" "api_scopes" {
  resource_server_identifier = auth0_resource_server.api.identifier

  scopes {
    name        = "read:users"
    description = "Read user data"
  }
  scopes {
    name        = "write:users"
    description = "Write user data"
  }
  scopes {
    name        = "read:trigs"
    description = "Read trig data"
  }
  scopes {
    name        = "write:trigs"
    description = "Write trig data"
  }
  scopes {
    name        = "read:photos"
    description = "Read photo data"
  }
  scopes {
    name        = "write:photos"
    description = "Write photo data"
  }
  scopes {
    name        = "admin"
    description = "Administrator access"
  }
}

# ============================================================================
# APPLICATIONS (CLIENTS)
# ============================================================================

# M2M Application for API access
resource "auth0_client" "m2m_api" {
  name        = "${var.name_prefix}-api-m2m"
  description = "Machine to Machine application for ${var.environment} API"
  app_type    = "non_interactive"

  grant_types = [
    "client_credentials",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

# Single Page Application (Swagger)
resource "auth0_client" "swagger" {
  name        = "${var.name_prefix}-swagger"
  description = "SPA for Swagger/OpenAPI documentation OAuth2 authentication"
  app_type    = "spa"

  callbacks           = var.swagger_callback_urls
  allowed_origins     = var.swagger_allowed_origins
  web_origins         = var.swagger_allowed_origins
  allowed_logout_urls = [for url in var.swagger_callback_urls : replace(url, "/oauth2-redirect", "")]

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  oidc_conformant = true
}

# Regular Web Application (Website)
resource "auth0_client" "website" {
  name        = "${var.name_prefix}-website"
  description = "Main website for ${var.environment}"
  app_type    = "regular_web"

  callbacks = var.website_callback_urls

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  oidc_conformant = true
}

# Regular Web Application (Forum) - Optional
resource "auth0_client" "forum" {
  count = var.enable_forum ? 1 : 0

  name        = "${var.name_prefix}-forum"
  description = "Forum (phpBB) for ${var.environment}"
  app_type    = "regular_web"

  callbacks = var.forum_callback_urls

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  oidc_conformant = true
}

# Regular Web Application (Wiki) - Optional
resource "auth0_client" "wiki" {
  count = var.enable_wiki ? 1 : 0

  name        = "${var.name_prefix}-wiki"
  description = "Wiki (MediaWiki) for ${var.environment}"
  app_type    = "regular_web"

  callbacks = var.wiki_callback_urls

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  oidc_conformant = true
}

# Native Application (Android)
resource "auth0_client" "android" {
  name        = "${var.name_prefix}-android"
  description = "Android mobile application for ${var.environment}"
  app_type    = "native"

  callbacks = var.android_callback_urls

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  oidc_conformant = true
}

# ============================================================================
# CLIENT GRANTS (M2M Authorizations)
# ============================================================================

# Grant M2M client access to API
resource "auth0_client_grant" "m2m_to_api" {
  client_id = auth0_client.m2m_api.id
  audience  = auth0_resource_server.api.identifier

  scopes = [
    "read:users",
    "write:users",
    "read:trigs",
    "write:trigs",
    "read:photos",
    "write:photos",
  ]
}

# Grant M2M client access to Management API (for user provisioning sync)
resource "auth0_client_grant" "m2m_to_mgmt_api" {
  client_id = auth0_client.m2m_api.id
  audience  = "https://${data.auth0_tenant.current.domain}/api/v2/"

  scopes = [
    "read:users",
    "update:users",
    "create:users",
  ]
}

# ============================================================================
# ROLES
# ============================================================================

resource "auth0_role" "admin" {
  name        = var.admin_role_name
  description = var.admin_role_description
}

# Assign permissions to admin role
resource "auth0_role_permissions" "admin_perms" {
  role_id = auth0_role.admin.id

  dynamic "permissions" {
    for_each = ["read:users", "write:users", "read:trigs", "write:trigs", "read:photos", "write:photos", "admin"]
    content {
      resource_server_identifier = auth0_resource_server.api.identifier
      name                       = permissions.value
    }
  }
}

# ============================================================================
# POST USER REGISTRATION ACTION
# ============================================================================

resource "auth0_action" "post_user_registration" {
  count = var.enable_post_registration_action ? 1 : 0

  name    = "${var.name_prefix}-post-user-registration"
  runtime = "node18"
  deploy  = true

  supported_triggers {
    id      = "post-user-registration"
    version = "v2"
  }

  code = templatefile("${path.module}/actions/post-user-registration.js.tpl", {
    environment = var.environment
  })

  dependencies {
    name    = "axios"
    version = "1.7.9"
  }

  secrets {
    name  = "FASTAPI_URL"
    value = var.fastapi_url
  }

  secrets {
    name  = "M2M_TOKEN"
    value = var.m2m_token
  }
}

# Bind Action to trigger
resource "auth0_trigger_actions" "post_user_registration" {
  count = var.enable_post_registration_action ? 1 : 0

  trigger = "post-user-registration"

  actions {
    id           = auth0_action.post_user_registration[0].id
    display_name = auth0_action.post_user_registration[0].name
  }
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "auth0_tenant" "current" {}

# Get M2M client credentials (includes secret)
data "auth0_client" "m2m_api" {
  client_id = auth0_client.m2m_api.id
}

# Get Cloudflare zone information
data "cloudflare_zones" "domain" {
  filter {
    name = var.cloudflare_zone_name
  }
}

# ============================================================================
# CUSTOM DOMAIN
# ============================================================================

# Configure Auth0 custom domain for branded authentication
resource "auth0_custom_domain" "main" {
  domain = var.auth0_custom_domain
  type   = "auth0_managed_certs" # Auth0 manages SSL certificates

  # Auth0 will automatically verify via CNAME once DNS is configured
}

# Create CNAME record in Cloudflare pointing to Auth0
# This is DNS-only (not proxied) as required by Auth0
resource "cloudflare_record" "auth0_custom_domain" {
  zone_id = data.cloudflare_zones.domain.zones[0].id
  name    = split(".", var.auth0_custom_domain)[0] # Extract subdomain (e.g., "auth" from "auth.trigpointing.me")
  content = auth0_custom_domain.main.verification[0].methods[0].record
  type    = "CNAME"
  proxied = false # MUST be false for Auth0 custom domains
  ttl     = 1     # Auto TTL

  comment = "Auth0 custom domain for ${var.environment} - managed by Terraform"
}
