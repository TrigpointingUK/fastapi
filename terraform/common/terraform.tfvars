# Common Infrastructure Configuration
# This file configures shared resources like VPC, ALB, and ECS cluster
#
# Note: CloudFlare SSL certificates are managed by individual environment modules
# (staging and production) for their respective HTTPS listeners

# Enable CloudFlare SSL for the shared ALB
enable_cloudflare_ssl = true
