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
  zone_id         = data.cloudflare_zones.staging.zones[0].id
  name            = "api"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true  # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "API endpoint for staging environment - managed by Terraform"
}

# CNAME record for production domain
resource "cloudflare_record" "api_production" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "api"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true  # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "API endpoint for production environment - managed by Terraform"
}

# CNAME record for bastion
resource "cloudflare_record" "bastion" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "bastion"
  content         = aws_eip.bastion.public_ip
  type            = "A"
  proxied         = false # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "Bastion host for TrigpointingUK - managed by Terraform"
}


# CNAME record for bastion
resource "cloudflare_record" "webserver" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "webserver"
  content         = aws_instance.webserver.private_ip
  type            = "A"
  proxied         = false # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "Webserver host for TrigpointingUK - managed by Terraform"
}

# Test CNAMEs for ALB testing
resource "cloudflare_record" "test1" {
  zone_id         = data.cloudflare_zones.staging.zones[0].id
  name            = "test1"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true  # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "Test domain 1 for ALB testing - managed by Terraform"
}

resource "cloudflare_record" "test2" {
  zone_id         = data.cloudflare_zones.staging.zones[0].id
  name            = "test2"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true  # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true  # Allow overwriting existing records

  comment = "Test domain 2 for ALB testing - managed by Terraform"
}
