environment = "production"
aws_region  = "us-west-2"

# Container image (update this with your actual image)
container_image = "ghcr.io/your-username/fastapi:main"

# Database credentials (use AWS Secrets Manager in production)
db_username = "fastapi_user"
db_password = "secure-production-password-change-this"
db_schema = "trigpoin_trigs"  # Legacy schema name for migration compatibility

# JWT secret (use AWS Secrets Manager in production)
jwt_secret_key = "super-secure-production-jwt-secret-key"

# Scaling settings
desired_count = 2
min_capacity  = 2
max_capacity  = 10
