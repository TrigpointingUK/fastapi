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
## Bulk Redirects for wiki paths (account-level)
# List holding the redirects
resource "cloudflare_list" "wiki_redirects" {
  account_id  = var.cloudflare_account_id
  name        = "wiki-redirects"
  description = "Redirect /w/* and /wiki* on trigpointing.uk to wiki.trigpointing.uk"
  kind        = "redirect"
}

# Redirect: https://trigpointing.uk/w -> https://wiki.trigpointing.uk/w (preserve subpath + query)
resource "cloudflare_list_item" "wiki_redirect_w" {
  account_id = var.cloudflare_account_id
  list_id    = cloudflare_list.wiki_redirects.id

  redirect {
    source_url            = "https://trigpointing.uk/w"
    target_url            = "https://wiki.trigpointing.uk/w"
    status_code           = 301
    include_subdomains    = true # covers www.trigpointing.uk
    subpath_matching      = true # preserve path after /w
    preserve_query_string = true # preserve ?query
  }
}

# Redirect: https://trigpointing.uk/wiki -> https://wiki.trigpointing.uk/wiki (preserve subpath + query)
resource "cloudflare_list_item" "wiki_redirect_wiki" {
  account_id = var.cloudflare_account_id
  list_id    = cloudflare_list.wiki_redirects.id

  redirect {
    source_url            = "https://trigpointing.uk/wiki"
    target_url            = "https://wiki.trigpointing.uk/wiki"
    status_code           = 301
    include_subdomains    = true # covers www.trigpointing.uk
    subpath_matching      = true
    preserve_query_string = true
  }
}

# Activate the list via an account-level redirect ruleset
resource "cloudflare_ruleset" "wiki_bulk_redirects" {
  account_id  = var.cloudflare_account_id
  name        = "wiki-bulk-redirects"
  description = "Activate wiki redirects list"
  kind        = "root"
  phase       = "http_request_redirect"

  rules {
    enabled     = true
    description = "Apply wiki redirects from list"
    action      = "redirect"
    action_parameters {
      from_list {
        name = cloudflare_list.wiki_redirects.name
        key  = "http.request.full_uri"
      }
    }
    expression = "true"
  }
}
