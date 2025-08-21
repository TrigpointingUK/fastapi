# CloudFlare Integration
# This file contains resources for CloudFlare origin certificate and IP restrictions

# Data source for CloudFlare IP ranges (alternative to hardcoded list)
data "http" "cloudflare_ips_v4" {
  url = "https://www.cloudflare.com/ips-v4"
}

locals {
  # Parse CloudFlare IP ranges from their public API
  cloudflare_ips_v4 = split("\n", chomp(data.http.cloudflare_ips_v4.response_body))
  
  # CloudFlare IPv4 ranges (fallback if API fails)
  cloudflare_ips_fallback = [
    "103.21.244.0/22",
    "103.22.200.0/22", 
    "103.31.4.0/22",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "108.162.192.0/18",
    "131.0.72.0/22",
    "141.101.64.0/18",
    "162.158.0.0/15",
    "172.64.0.0/13",
    "173.245.48.0/20",
    "188.114.96.0/20",
    "190.93.240.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17"
  ]
}

# Output the domain for easy reference
output "api_domain" {
  value = var.domain_name
  description = "The domain name for the API"
}

# Output CloudFlare IPs for reference
output "cloudflare_ip_ranges" {
  value = local.cloudflare_ips_v4
  description = "CloudFlare IP ranges allowed to access ALB"
}
