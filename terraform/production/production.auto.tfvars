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
auth0_spa_client_id = "<set-in-secrets-manager>"
auth0_m2m_client_id = "<set-in-secrets-manager>"
auth0_m2m_client_secret_arn = "arn:aws:secretsmanager:eu-west-1:ACCOUNT:secret:fastapi-production-app-secrets:auth0_m2m_client_secret::"

# Flattened config replacing Parameter Store
log_level       = "INFO"
cors_origins    = ["https://trigpointing.uk", "https://api.trigpointing.uk"]
db_pool_size    = 10
db_pool_recycle = 300
xray_enabled    = true
xray_service_name   = "trigpointing-api-production"
xray_sampling_rate  = 0.1
xray_daemon_address = null
