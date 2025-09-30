environment = "staging"

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:develop"

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 3

# Resource allocation
cpu    = 256
memory = 512

# CloudFlare SSL Configuration (enabled for staging)
domain_name           = "api.trigpointing.me"
enable_cloudflare_ssl = true

log_level       = "DEBUG"
cors_origins    = ["https://trigpointing.me", "https://api.trigpointing.me"]
db_pool_size    = 5
db_pool_recycle = 300
xray_enabled    = false
