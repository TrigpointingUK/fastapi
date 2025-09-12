environment = "staging"
aws_region  = "us-west-2"

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:develop"

# Database configuration
db_schema = "trigpoin_trigs"  # Legacy schema name for migration compatibility

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 3

# Admin access
admin_ip_address = "86.162.34.238"
key_pair_name = "fastapi-staging-bastion"

# DMS access
enable_dms_access = true
dms_replication_instance_sg_id = "sg-0439b939713d7c283"  # fastapi-staging-dms-sg for serverless DMS
# dms_cidr_block = "172.31.0.0/16"  # CIDR block for cross-VPC DMS access
# dms_instance_ip = "10.0.11.50"  # Specific IP of fastapi-2 DMS instance (legacy)

# CloudFlare SSL Configuration (enabled for staging)
domain_name = "fastapi.trigpointing.me"
enable_cloudflare_ssl = true  # Enabled for staging with CloudFlare certificates

# Auth0 Configuration
auth0_domain = "trigpointing.eu.auth0.com"
auth0_connection = "tme-users"
auth0_api_audience = "https://fastapi.trigpointing.me/api/v1/"
