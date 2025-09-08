# CloudFlare SSL Configuration

## 🔒 Security Architecture

This infrastructure follows security best practices:

- **No HTTP (port 80)** on the origin server
- **HTTPS only (port 443)** with CloudFlare origin certificate
- **CloudFlare edge** handles HTTP→HTTPS redirects
- **End-to-end encryption**: Client → CloudFlare → ALB → ECS

## 🚀 Setup Instructions

### 1. Generate CloudFlare Origin Certificate

1. **CloudFlare Dashboard** → **SSL/TLS** → **Origin Server**
2. **Create Certificate** with:
   - **Hostnames**: `fastapi.trigpointing.me`, `*.trigpointing.me`
   - **Key Type**: RSA (2048)
   - **Validity**: 15 years

### 2. Configure Terraform

```bash
# Copy the template
cp cloudflare-cert-example.tfvars cloudflare-cert.tfvars

# Add your certificates (file is gitignored)
nano cloudflare-cert.tfvars
```

### 3. Apply Configuration

```bash
terraform apply -var-file="staging.tfvars" -var-file="cloudflare-cert.tfvars"
```

## ✅ Expected Results

- ✅ **https://fastapi.trigpointing.me** - Secure API access
- ❌ **http://fastapi.trigpointing.me** - CloudFlare redirects to HTTPS
- ❌ **Direct ALB access** - Blocked (CloudFlare IPs only)

## 🛡️ Security Features

1. **Origin Certificate**: Validates CloudFlare → ALB connection
2. **IP Restriction**: Only CloudFlare IPs can reach ALB
3. **No HTTP**: Origin server only accepts HTTPS
4. **Edge Redirects**: CloudFlare handles HTTP→HTTPS at edge

## 🔧 CloudFlare Settings

- **SSL/TLS Mode**: "Full (strict)" recommended
- **Always Use HTTPS**: On
- **HSTS**: Enabled
- **Minimum TLS**: 1.2+

This setup provides enterprise-grade security with zero-trust networking principles.

## 🗄️ Database Schema Configuration

The database schema is configurable to support migration from legacy systems:

- **Current**: `trigpoin_trigs` (legacy ISP naming convention)
- **Future**: Can be changed to `fastapi` or any preferred name
- **Configuration**: Set via `db_schema` variable in tfvars files

### Changing Schema (Future)

```bash
# Update terraform/staging.tfvars
db_schema = "fastapi"  # New clean schema name

# Update terraform/production.tfvars
db_schema = "fastapi"  # New clean schema name

# Apply changes
terraform apply -var-file="staging.tfvars"
```
