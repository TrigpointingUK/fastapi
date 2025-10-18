# Auth0 Configuration for FastAPI Project
#
# This file manages Auth0 resources for both T:ME and T:UK environments
# which share the same Auth0 tenant (trigpointing.eu.auth0.com)
#
# Resource naming convention:
# - tme_* : T:ME (trigpointing.me) resources
# - tuk_* : T:UK (trigpointing.uk) resources
#
# To import existing resources:
# 1. Run: terraform/common/scripts/fetch-auth0-ids.sh
# 2. Run: terraform/common/scripts/import-auth0.sh
# 3. Run: terraform plan

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

resource "auth0_connection" "tme_users" {
  name     = "tme-users"
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
    validation {
      # Username not required - use nickname/email
    }
  }

  enabled_clients = [
    auth0_client.api_tme.id,
    auth0_client.legacy.id,
    auth0_client.trigpointinguk.id,
    auth0_client.swagger_ui.id,
  ]
}

resource "auth0_connection" "tuk_users" {
  name     = "tuk-users"
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
    validation {
      # Username not required - use nickname/email
    }
  }

  enabled_clients = [
    auth0_client.api_tuk.id,
    auth0_client.fastapi_tuk.id,
    auth0_client.swagger_ui.id,
  ]
}

# ============================================================================
# RESOURCE SERVERS (APIs)
# ============================================================================

resource "auth0_resource_server" "api_tme" {
  name       = "api-tme"
  identifier = "https://api.trigpointing.me/"

  # Define scopes/permissions
  scopes {
    value       = "read:users"
    description = "Read user data"
  }
  scopes {
    value       = "write:users"
    description = "Write user data"
  }
  scopes {
    value       = "read:trigs"
    description = "Read trig data"
  }
  scopes {
    value       = "write:trigs"
    description = "Write trig data"
  }
  scopes {
    value       = "admin"
    description = "Administrator access"
  }

  # Token settings
  token_lifetime = 86400 # 24 hours
  signing_alg    = "RS256"

  # RBAC
  enforce_policies                                = true
  token_dialect                                   = "access_token_authz"
  skip_consent_for_verifiable_first_party_clients = true
}

resource "auth0_resource_server" "api_tuk" {
  name       = "api-tuk"
  identifier = "https://api.trigpointing.uk/"

  # Define scopes/permissions  
  scopes {
    value       = "read:users"
    description = "Read user data"
  }
  scopes {
    value       = "write:users"
    description = "Write user data"
  }
  scopes {
    value       = "read:trigs"
    description = "Read trig data"
  }
  scopes {
    value       = "write:trigs"
    description = "Write trig data"
  }
  scopes {
    value       = "admin"
    description = "Administrator access"
  }

  # Token settings
  token_lifetime = 86400 # 24 hours
  signing_alg    = "RS256"

  # RBAC
  enforce_policies                                = true
  token_dialect                                   = "access_token_authz"
  skip_consent_for_verifiable_first_party_clients = true
}

resource "auth0_resource_server" "fastapi_tuk" {
  name       = "fastapi-tuk"
  identifier = "https://fastapi.trigpointing.uk/api/v1/"

  # Define scopes/permissions
  scopes {
    value       = "read:users"
    description = "Read user data"
  }
  scopes {
    value       = "write:users"
    description = "Write user data"
  }
  scopes {
    value       = "read:trigs"
    description = "Read trig data"
  }
  scopes {
    value       = "write:trigs"
    description = "Write trig data"
  }
  scopes {
    value       = "admin"
    description = "Administrator access"
  }

  # Token settings
  token_lifetime = 86400 # 24 hours
  signing_alg    = "RS256"

  # RBAC
  enforce_policies                                = true
  token_dialect                                   = "access_token_authz"
  skip_consent_for_verifiable_first_party_clients = true
}

# ============================================================================
# APPLICATIONS (CLIENTS)
# ============================================================================

# M2M Applications
resource "auth0_client" "api_tme" {
  name        = "api-tme"
  description = "Machine to Machine application for T:ME API"
  app_type    = "non_interactive"

  # Grant types
  grant_types = [
    "client_credentials",
  ]

  # JWT Configuration
  jwt_configuration {
    alg = "RS256"
  }

  # Client credentials
  # Note: client_secret will be stored in Terraform state
  # Consider using AWS Secrets Manager for production
}

resource "auth0_client" "api_tuk" {
  name        = "api-tuk"
  description = "Machine to Machine application for T:UK API"
  app_type    = "non_interactive"

  grant_types = [
    "client_credentials",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

resource "auth0_client" "fastapi_tuk" {
  name        = "fastapi-tuk"
  description = "Machine to Machine application for FastAPI T:UK"
  app_type    = "non_interactive"

  grant_types = [
    "client_credentials",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

# Single Page Application
resource "auth0_client" "swagger_ui" {
  name        = "Swagger UI"
  description = "SPA for Swagger/OpenAPI documentation OAuth2 authentication"
  app_type    = "spa"

  # Callbacks and origins
  callbacks = [
    "https://api.trigpointing.me/docs/oauth2-redirect",
    "https://api-staging.trigpointing.me/docs/oauth2-redirect",
    "https://api.trigpointing.uk/docs/oauth2-redirect",
    "http://localhost:8000/docs/oauth2-redirect",
  ]

  allowed_origins = [
    "https://api.trigpointing.me",
    "https://api-staging.trigpointing.me",
    "https://api.trigpointing.uk",
    "http://localhost:8000",
  ]

  web_origins = [
    "https://api.trigpointing.me",
    "https://api-staging.trigpointing.me",
    "https://api.trigpointing.uk",
    "http://localhost:8000",
  ]

  allowed_logout_urls = [
    "https://api.trigpointing.me/docs",
    "https://api-staging.trigpointing.me/docs",
    "https://api.trigpointing.uk/docs",
    "http://localhost:8000/docs",
  ]

  # Grant types for SPA
  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  # PKCE required for SPA
  jwt_configuration {
    alg = "RS256"
  }

  # Token settings
  oidc_conformant = true
}

# Regular Web Applications
resource "auth0_client" "legacy" {
  name        = "legacy"
  description = "Legacy web application for phpBB and other legacy systems"
  app_type    = "regular_web"

  # Callbacks - TODO: Update with actual URLs
  callbacks = [
    "https://www.trigpointing.uk/forum/ucp.php?mode=login",
    "https://www.trigpointing.me/forum/ucp.php?mode=login",
  ]

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

resource "auth0_client" "trigpointinguk" {
  name        = "TrigpointingUK"
  description = "Main web application for TrigpointingUK"
  app_type    = "regular_web"

  # Callbacks - TODO: Update with actual URLs
  callbacks = [
    "https://www.trigpointing.uk/auth/callback",
    "https://www.trigpointing.me/auth/callback",
  ]

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }
}

# Native Application
resource "auth0_client" "android" {
  name        = "android"
  description = "Android mobile application"
  app_type    = "native"

  # Mobile app callbacks
  callbacks = [
    "uk.trigpointing.android://callback",
    "me.trigpointing.android://callback",
  ]

  grant_types = [
    "authorization_code",
    "refresh_token",
  ]

  jwt_configuration {
    alg = "RS256"
  }

  # Native app settings
  oidc_conformant = true
}

# ============================================================================
# CLIENT GRANTS (M2M Authorizations)
# ============================================================================

# Grant api-tme access to T:ME API
resource "auth0_client_grant" "api_tme_to_api_tme" {
  client_id = auth0_client.api_tme.id
  audience  = auth0_resource_server.api_tme.identifier

  scopes = [
    "read:users",
    "write:users",
    "read:trigs",
    "write:trigs",
  ]
}

# Grant api-tuk access to T:UK API
resource "auth0_client_grant" "api_tuk_to_api_tuk" {
  client_id = auth0_client.api_tuk.id
  audience  = auth0_resource_server.api_tuk.identifier

  scopes = [
    "read:users",
    "write:users",
    "read:trigs",
    "write:trigs",
  ]
}

# Grant fastapi-tuk access to FastAPI T:UK API
resource "auth0_client_grant" "fastapi_tuk_to_fastapi_tuk" {
  client_id = auth0_client.fastapi_tuk.id
  audience  = auth0_resource_server.fastapi_tuk.identifier

  scopes = [
    "read:users",
    "write:users",
    "read:trigs",
    "write:trigs",
  ]
}

# Grant M2M clients access to Management API for user provisioning
resource "auth0_client_grant" "api_tme_to_mgmt_api" {
  client_id = auth0_client.api_tme.id
  audience  = "https://${var.auth0_domain}/api/v2/"

  scopes = [
    "read:users",
    "update:users",
    "create:users",
  ]
}

resource "auth0_client_grant" "api_tuk_to_mgmt_api" {
  client_id = auth0_client.api_tuk.id
  audience  = "https://${var.auth0_domain}/api/v2/"

  scopes = [
    "read:users",
    "update:users",
    "create:users",
  ]
}

# ============================================================================
# ROLES
# ============================================================================

resource "auth0_role" "tme_admin" {
  name        = "tme-admin"
  description = "T:ME Administrators"
}

resource "auth0_role" "tuk_admin" {
  name        = "tuk-admin"
  description = "T:UK Administrators"
}

# Assign permissions to roles
resource "auth0_role_permissions" "tme_admin_perms" {
  role_id = auth0_role.tme_admin.id

  dynamic "permissions" {
    for_each = ["read:users", "write:users", "read:trigs", "write:trigs", "admin"]
    content {
      name                       = permissions.value
      resource_server_identifier = auth0_resource_server.api_tme.identifier
    }
  }
}

resource "auth0_role_permissions" "tuk_admin_perms" {
  role_id = auth0_role.tuk_admin.id

  dynamic "permissions" {
    for_each = ["read:users", "write:users", "read:trigs", "write:trigs", "admin"]
    content {
      name                       = permissions.value
      resource_server_identifier = auth0_resource_server.api_tuk.identifier
    }
  }
}

# ============================================================================
# ACTIONS - Post User Registration
# ============================================================================

# T:ME Post Registration Action
resource "auth0_action" "tme_post_user_registration" {
  name    = "tme-post-user-registration"
  runtime = "node18"
  deploy  = true

  supported_triggers {
    id      = "post-user-registration"
    version = "v3"
  }

  code = file("${path.module}/actions/tme-post-user-registration.js")

  dependencies {
    name    = "axios"
    version = "latest"
  }

  secrets {
    name  = "FASTAPI_URL"
    value = var.tme_fastapi_url
  }

  secrets {
    name  = "M2M_TOKEN"
    value = var.tme_m2m_token
  }
}

# T:UK Post Registration Action  
resource "auth0_action" "tuk_post_user_registration" {
  name    = "tuk-post-user-registration"
  runtime = "node18"
  deploy  = true

  supported_triggers {
    id      = "post-user-registration"
    version = "v3"
  }

  code = file("${path.module}/actions/tuk-post-user-registration.js")

  dependencies {
    name    = "axios"
    version = "latest"
  }

  secrets {
    name  = "FASTAPI_URL"
    value = var.tuk_fastapi_url
  }

  secrets {
    name  = "M2M_TOKEN"
    value = var.tuk_m2m_token
  }
}

# Bind Actions to trigger
resource "auth0_trigger_actions" "post_user_registration" {
  trigger = "post-user-registration"

  actions {
    id           = auth0_action.tme_post_user_registration.id
    display_name = auth0_action.tme_post_user_registration.name
  }

  actions {
    id           = auth0_action.tuk_post_user_registration.id
    display_name = auth0_action.tuk_post_user_registration.name
  }
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "auth0_connections" {
  description = "Auth0 database connection IDs"
  value = {
    tme_users = auth0_connection.tme_users.id
    tuk_users = auth0_connection.tuk_users.id
  }
}

output "auth0_apis" {
  description = "Auth0 API resource server IDs"
  value = {
    api_tme     = auth0_resource_server.api_tme.id
    api_tuk     = auth0_resource_server.api_tuk.id
    fastapi_tuk = auth0_resource_server.fastapi_tuk.id
  }
}

output "auth0_clients" {
  description = "Auth0 client IDs"
  value = {
    api_tme        = auth0_client.api_tme.id
    api_tuk        = auth0_client.api_tuk.id
    fastapi_tuk    = auth0_client.fastapi_tuk.id
    swagger_ui     = auth0_client.swagger_ui.id
    legacy         = auth0_client.legacy.id
    trigpointinguk = auth0_client.trigpointinguk.id
    android        = auth0_client.android.id
  }
  sensitive = true
}

output "auth0_roles" {
  description = "Auth0 role IDs"
  value = {
    tme_admin = auth0_role.tme_admin.id
    tuk_admin = auth0_role.tuk_admin.id
  }
}

