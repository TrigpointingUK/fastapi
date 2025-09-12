# CloudFlare Origin Certificate Configuration
# Copy this file to cloudflare-cert.tfvars and add your actual certificates

# Enable CloudFlare SSL
enable_cloudflare_ssl = true

# CloudFlare Origin Certificate (PEM format)
# Replace with your actual certificate from CloudFlare dashboard
cloudflare_origin_cert = <<EOF
-----BEGIN CERTIFICATE-----
PASTE_YOUR_CLOUDFLARE_ORIGIN_CERTIFICATE_HERE
-----END CERTIFICATE-----
EOF

# CloudFlare Origin Private Key
# Replace with your actual private key from CloudFlare dashboard
cloudflare_origin_key = <<EOF
-----BEGIN PRIVATE KEY-----
PASTE_YOUR_CLOUDFLARE_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
EOF
