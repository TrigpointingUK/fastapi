environment = "production"

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:main"

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 10

# Resource allocation
cpu    = 256
memory = 512

# CloudFlare SSL Configuration (REQUIRED for production)
domain_name           = "api.trigpointing.uk"
enable_cloudflare_ssl = true

# Auth0 Configuration
auth0_domain       = "trigpointing.eu.auth0.com"
auth0_connection   = "tuk-users"
auth0_api_audience = "https://api.trigpointing.uk/v1/"

# Parameter Store Configuration
parameter_store_config = {
  enabled = true
  parameters = {
    xray = {
      enabled        = true
      service_name   = "trigpointing-api-production"
      sampling_rate  = 0.1
      daemon_address = null
    }
    app = {
      log_level    = "INFO"
      cors_origins = "https://trigpointing.uk,https://api.trigpointing.uk"
    }
    database = {
      pool_size    = 10 # Higher pool size for production
      pool_recycle = 300
    }
  }
}
