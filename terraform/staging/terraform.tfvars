# Note: Using existing tuk-terraform-state bucket in eu-west-1

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:develop"

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 3

# Resource allocation (matching production)
cpu = 1024
memory = 2048

# CloudFlare SSL Configuration (enabled for staging)
domain_name = "api.trigpointing.me"
enable_cloudflare_ssl = false

# Auth0 Configuration
auth0_domain = "trigpointing.eu.auth0.com"
auth0_connection = "tme-users"
auth0_api_audience = "https://api.trigpointing.me/api/v1/"
