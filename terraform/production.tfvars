environment = "production"
aws_region  = "us-west-2"

# Container image (update this with your actual image)
container_image = "ghcr.io/trigpointinguk/fastapi:main"

# External database configuration (MySQL 5.5 on EC2)
use_external_database = true
db_schema = "trigpoin_trigs"  # Legacy schema name for migration compatibility

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
auth0_connection = "tuk-users"
auth0_api_audience = "https://api.trigpointing.uk/api/v1/"
