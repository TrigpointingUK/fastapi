# CloudFlare Origin Certificate Configuration
# Copy this file to cloudflare-cert-staging.tfvars or cloudflare-cert-production.tfvars
# and fill in your actual certificate values
#
# For staging: api.trigpointing.me
# For production: api.trigpointing.uk

# CloudFlare Origin Certificate (PEM format)
# Get this from CloudFlare Dashboard > SSL/TLS > Origin Server > Create Certificate
cloudflare_origin_cert = <<EOF
-----BEGIN CERTIFICATE-----
YOUR_CLOUDFLARE_ORIGIN_CERTIFICATE_HERE
-----END CERTIFICATE-----
EOF

# CloudFlare Origin Certificate Private Key
cloudflare_origin_key = <<EOF
-----BEGIN PRIVATE KEY-----
YOUR_CLOUDFLARE_ORIGIN_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
EOF
