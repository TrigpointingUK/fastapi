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

# Admin access
admin_ip_address = "86.162.34.238"
key_pair_name = "fastapi-staging-bastion"

# DMS access
enable_dms_access = true
dms_replication_instance_sg_id = "sg-0439b939713d7c283"  # fastapi-staging-dms-sg for serverless DMS
# dms_cidr_block = "172.31.0.0/16"  # CIDR block for cross-VPC DMS access  
# dms_instance_ip = "10.0.11.50"  # Specific IP of fastapi-2 DMS instance (legacy)
