environment = "staging"
aws_region  = "us-west-2"

# Container image (built by GitHub Actions CI/CD)
container_image = "ghcr.io/trigpointinguk/fastapi:develop"

# Database credentials (use AWS Secrets Manager in production)
db_username = "fastapi_user"
db_password = "change-this-password-in-production"
db_schema = "trigpoin_trigs"  # Legacy schema name for migration compatibility

# JWT secret (use AWS Secrets Manager in production)
jwt_secret_key = "staging-jwt-secret-key-change-this"

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

# CloudFlare SSL Configuration (disabled for staging)
domain_name = "fastapi.trigpointing.me"
enable_cloudflare_ssl = false  # Disabled for staging - will use HTTP for testing
# For production, enable CloudFlare SSL and set:
# cloudflare_origin_cert = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
# cloudflare_origin_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# Auth0 Configuration
auth0_domain = "trigpointing.eu.auth0.com"
auth0_secret_name = "auth0-fastapi-tme"
auth0_connection = "tme-users"
