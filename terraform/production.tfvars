environment = "production"
aws_region  = "us-west-2"

# Container image (update this with your actual image)
container_image = "ghcr.io/trigpointinguk/fastapi:main"

# External database configuration (MySQL 5.5 on EC2)
use_external_database        = true
external_database_secret_name = "fastapi-production-external-db"
db_schema = "trigpoin_trigs"  # Legacy schema name for migration compatibility

# Database credentials (not used when use_external_database = true)
# These are kept for staging/development environments
db_username = "fastapi_user"
db_password = "secure-production-password-change-this"

# JWT secret (use AWS Secrets Manager in production)
jwt_secret_key = "super-secure-production-jwt-secret-key"

# Scaling settings
desired_count = 2
min_capacity  = 2
max_capacity  = 10

# CloudFlare SSL Configuration (REQUIRED for production)
domain_name = "fastapi.trigpointing.uk"  # Replace with your actual production domain
enable_cloudflare_ssl = true  # REQUIRED for production security

# CloudFlare Origin Certificate (create these with: terraform apply -var-file=cloudflare-cert.tfvars)
# cloudflare_origin_cert = "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
# cloudflare_origin_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# Auth0 Configuration
auth0_domain = "trigpointing.eu.auth0.com"
auth0_secret_name = "auth0-fastapi-tuk"
auth0_connection = "tuk-users"
