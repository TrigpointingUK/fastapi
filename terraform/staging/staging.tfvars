environment  = "staging"

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:develop"

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 3

# Resource allocation
cpu    = 1024
memory = 2048

# CloudFlare SSL Configuration (enabled for staging)
domain_name           = "api.trigpointing.me"
enable_cloudflare_ssl = true

# Auth0 Configuration
auth0_domain       = "trigpointing.eu.auth0.com"
auth0_connection   = "tme-users"
auth0_api_audience = "https://api.trigpointing.me/api/v1/"


parameter_store_config = {
  enabled = true
  parameters = {
    xray = {
      enabled        = true
      service_name   = "trigpointing-api-staging"
      sampling_rate  = 0.2
      daemon_address = null
    }
    app = {
      log_level    = "DEBUG"
      cors_origins = "https://trigpointing.me,https://api.trigpointing.me"
    }
    database = {
      pool_size    = 5
      pool_recycle = 300
    }
  }
}
