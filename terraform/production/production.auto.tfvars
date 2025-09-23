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

auth0_enabled       = true
log_level           = "INFO"
cors_origins        = ["https://trigpointing.uk", "https://api.trigpointing.uk"]
db_pool_size        = 10
db_pool_recycle     = 300
xray_enabled        = true
xray_service_name   = "trigpointing-api-production"
xray_sampling_rate  = 0.1
xray_daemon_address = null
