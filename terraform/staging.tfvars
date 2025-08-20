environment = "staging"
aws_region  = "us-west-2"

# Container image (update this with your actual image)
container_image = "ghcr.io/your-username/fastapi:develop"

# Database credentials (use AWS Secrets Manager in production)
db_username = "fastapi_user"
db_password = "change-this-password-in-production"

# JWT secret (use AWS Secrets Manager in production)
jwt_secret_key = "staging-jwt-secret-key-change-this"

# Scaling settings
desired_count = 1
min_capacity  = 1
max_capacity  = 3
