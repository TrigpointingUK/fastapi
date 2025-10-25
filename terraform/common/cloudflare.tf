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
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "API endpoint for staging environment - managed by Terraform"
}

# CNAME record for production domain
resource "cloudflare_record" "api_production" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "api"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "API endpoint for production environment - managed by Terraform"
}

# CNAME record for cache management interface
resource "cloudflare_record" "cache" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "cache"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Redis Commander cache management interface - managed by Terraform"
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
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Test domain 1 for ALB testing - managed by Terraform"
}

resource "cloudflare_record" "test2" {
  zone_id         = data.cloudflare_zones.staging.zones[0].id
  name            = "test2"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Test domain 2 for ALB testing - managed by Terraform"
}

# Production CNAMEs for trigpointing.uk domains
resource "cloudflare_record" "forum" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "forum"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Forum subdomain for TrigpointingUK - managed by Terraform"
}

resource "cloudflare_record" "phpmyadmin" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "phpmyadmin"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "phpMyAdmin subdomain for TrigpointingUK - managed by Terraform"
}

resource "cloudflare_record" "static" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "static"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Static content subdomain for TrigpointingUK - managed by Terraform"
}

resource "cloudflare_record" "wiki" {
  zone_id         = data.cloudflare_zones.production.zones[0].id
  name            = "wiki"
  content         = aws_lb.main.dns_name
  type            = "CNAME"
  proxied         = true # Enable CloudFlare proxy (orange cloud)
  allow_overwrite = true # Allow overwriting existing records

  comment = "Wiki subdomain for TrigpointingUK - managed by Terraform"
}

# Redirect wiki URLs on apex to wiki subdomain
resource "cloudflare_ruleset" "prod_redirect_wiki" {
  zone_id     = data.cloudflare_zones.production.zones[0].id
  name        = "Redirect wiki paths to wiki.trigpointing.uk"
  description = "Forward /w/* and /wiki* on apex to wiki subdomain, preserving path and query"
  kind        = "zone"
  phase       = "http_request_dynamic_redirect"

  # https://trigpointing.uk/w/* -> https://wiki.trigpointing.uk/w/* (preserve path + query)
  rules {
    enabled     = true
    description = "apex:/w/* -> wiki"
    expression  = "(http.host eq \"trigpointing.uk\" or http.host eq \"www.trigpointing.uk\") and starts_with(http.request.uri.path, \"/w/\")"
    action      = "redirect"
    action_parameters {
      from_value {
        status_code = 301
        target_url {
          expression = "concat(\"https://wiki.trigpointing.uk\", http.request.uri.path, if(len(http.request.uri.query) > 0, concat(\"?\", http.request.uri.query), \"\"))"
        }
      }
    }
  }

  # https://trigpointing.uk/wiki* -> https://wiki.trigpointing.uk/wiki* (preserve path + query)
  rules {
    enabled     = true
    description = "apex:/wiki* -> wiki"
    expression  = "(http.host eq \"trigpointing.uk\" or http.host eq \"www.trigpointing.uk\") and starts_with(http.request.uri.path, \"/wiki\")"
    action      = "redirect"
    action_parameters {
      from_value {
        status_code = 301
        target_url {
          expression = "concat(\"https://wiki.trigpointing.uk\", http.request.uri.path, if(len(http.request.uri.query) > 0, concat(\"?\", http.request.uri.query), \"\"))"
        }
      }
    }
  }
}
