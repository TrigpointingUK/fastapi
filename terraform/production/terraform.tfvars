# Note: Using existing tuk-terraform-state bucket in eu-west-1

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:main"

# Scaling settings
desired_count = 2
min_capacity  = 2
max_capacity  = 10

# CloudFlare SSL Configuration (REQUIRED for production)
domain_name = "api.trigpointing.uk"
enable_cloudflare_ssl = false

# Auth0 Configuration
auth0_domain = "trigpointing.eu.auth0.com"
auth0_connection = "tuk-users"
auth0_api_audience = "https://api.trigpointing.uk/api/v1/"
