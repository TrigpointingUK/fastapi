# Common Infrastructure Configuration
# This file configures shared resources like VPC, ALB, and ECS cluster
# 
# Note: CloudFlare SSL certificates are in a separate cloudflare-cert.tfvars file
# for security reasons (contains private keys)

# Enable CloudFlare SSL for the shared ALB
enable_cloudflare_ssl = true
