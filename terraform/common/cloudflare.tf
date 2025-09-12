# CloudFlare DNS Records
# Creates CNAME records for both staging and production domains

# Data source to get zone information
data "cloudflare_zones" "staging" {
  filter {
    name = "trigpointing.me"
  }
}

data "cloudflare_zones" "production" {
  filter {
    name = "trigpointing.uk"
  }
}

# CNAME record for staging domain
resource "cloudflare_record" "api_staging" {
  zone_id = data.cloudflare_zones.staging.zones[0].id
  name    = "api"
  content = aws_lb.main.dns_name
  type    = "CNAME"
  proxied = true  # Enable CloudFlare proxy (orange cloud)

  comment = "API endpoint for staging environment - managed by Terraform"

  tags = {
    Environment = "staging"
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

# CNAME record for production domain
resource "cloudflare_record" "api_production" {
  zone_id = data.cloudflare_zones.production.zones[0].id
  name    = "api"
  content = aws_lb.main.dns_name
  type    = "CNAME"
  proxied = true  # Enable CloudFlare proxy (orange cloud)

  comment = "API endpoint for production environment - managed by Terraform"

  tags = {
    Environment = "production"
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}
