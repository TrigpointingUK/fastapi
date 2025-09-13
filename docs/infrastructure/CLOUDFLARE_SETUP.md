# CloudFlare Setup for Terraform

This directory uses the CloudFlare Terraform provider to manage DNS records for the API endpoints.

## Required CloudFlare API Token

You need a CloudFlare API token with the following permissions:
- **Zone:Read** - To read zone information
- **DNS:Edit** - To create and manage DNS records

### Option 1: Environment Variable (Recommended)

Set the `CLOUDFLARE_API_TOKEN` environment variable:

```bash
export CLOUDFLARE_API_TOKEN="your-api-token-here"
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it persistent:

```bash
echo 'export CLOUDFLARE_API_TOKEN="your-api-token-here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Credentials File

Create a credentials file at `~/.cloudflare/credentials`:

```bash
mkdir -p ~/.cloudflare
cat > ~/.cloudflare/credentials << EOF
api_token = your-api-token-here
EOF
chmod 600 ~/.cloudflare/credentials
```

## Creating the API Token

1. Go to [CloudFlare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Click "Create Token"
3. Use "Custom token" template
4. Set permissions:
   - **Zone:Read** for all zones
   - **DNS:Edit** for all zones
5. Set zone resources to "Include - All zones" (or specific zones: trigpointing.me, trigpointing.uk)
6. Click "Continue to summary" and create the token
7. Copy the token and set it using one of the methods above

## What This Creates

The CloudFlare configuration will create:

- **api.trigpointing.me** (staging) → ALB DNS name (proxied)
- **api.trigpointing.uk** (production) → ALB DNS name (proxied)

Both records will be proxied through CloudFlare (orange cloud) for DDoS protection and performance benefits.

## Testing

After deployment, you can test the DNS resolution:

```bash
# Test staging
nslookup api.trigpointing.me

# Test production
nslookup api.trigpointing.uk
```

Both should resolve to the same ALB endpoint but with CloudFlare's IP addresses.
