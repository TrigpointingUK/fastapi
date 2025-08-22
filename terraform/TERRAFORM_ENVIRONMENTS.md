# Terraform Environment Management

This document explains how to manage staging and production environments with separate Terraform state and CloudFlare certificates.

## Overview

- **Staging**: Uses RDS MySQL 8.0, HTTP access, `.trigpointing.me` domain
- **Production**: Uses external MySQL 5.5, HTTPS-only, `.trigpointing.uk` domain
- **Separate state**: Each environment has its own Terraform state file
- **CloudFlare SSL**: Environment-specific origin certificates

## File Structure

```
terraform/
├── backend-staging.conf         # Staging state config
├── backend-production.conf      # Production state config  
├── staging.tfvars              # Staging variables
├── production.tfvars           # Production variables
├── cloudflare-cert-trigpointing-me.tfvars    # Staging SSL cert
└── cloudflare-cert-trigpointing-uk.tfvars    # Production SSL cert
```

## Quick Start

### 1. Initialize Environment

```bash
# For staging
make tf-init env=staging

# For production  
make tf-init env=production
```

### 2. Plan Changes

```bash
# For staging (with CloudFlare SSL)
make tf-plan env=staging

# For production (with CloudFlare SSL)
make tf-plan env=production
```

### 3. Apply Changes

```bash
# For staging
make tf-apply env=staging

# For production
make tf-apply env=production
```

## Environment Details

### Staging Environment

**Backend State**: `fastapi/staging/terraform.tfstate`
**Main Config**: `staging.tfvars`
**SSL Config**: `cloudflare-cert-trigpointing-me.tfvars`

```bash
# Initialize staging
make tf-init env=staging

# Plan staging changes
make tf-plan env=staging

# Apply staging changes
make tf-apply env=staging
```

**Staging Features**:
- ✅ RDS MySQL 8.0 (managed)
- ✅ Bastion host for database access
- ✅ HTTP access (CloudFlare SSL optional)
- ✅ DMS support for replication testing
- 🔗 Domain: `fastapi.trigpointing.me`

### Production Environment

**Backend State**: `fastapi/production/terraform.tfstate`
**Main Config**: `production.tfvars`
**SSL Config**: `cloudflare-cert-trigpointing-uk.tfvars`

```bash
# Initialize production
make tf-init env=production

# Plan production changes
make tf-plan env=production

# Apply production changes
make tf-apply env=production
```

**Production Features**:
- ✅ External MySQL 5.5 (your existing database)
- ✅ AWS Secrets Manager for database URL
- ✅ HTTPS-only with CloudFlare origin certificates
- ✅ Enhanced monitoring and security
- 🔗 Domain: `api.trigpointing.uk`

## CloudFlare Certificate Management

### Certificate Files

Each environment uses its own CloudFlare origin certificate:

- **Staging**: `cloudflare-cert-trigpointing-me.tfvars`
- **Production**: `cloudflare-cert-trigpointing-uk.tfvars`

### Setting Up Certificates

1. **Create CloudFlare Origin Certificate**:
   - Go to CloudFlare Dashboard → SSL/TLS → Origin Server
   - Click "Create Certificate"
   - Choose hostnames: `*.trigpointing.me, trigpointing.me` (staging)
   - Choose hostnames: `*.trigpointing.uk, trigpointing.uk` (production)
   - Download certificate and private key

2. **Update Certificate Files**:
   ```bash
   # Edit the appropriate file
   nano terraform/cloudflare-cert-trigpointing-me.tfvars    # For staging
   nano terraform/cloudflare-cert-trigpointing-uk.tfvars   # For production
   ```

3. **Certificate Format**:
   ```hcl
   cloudflare_origin_cert = <<EOF
   -----BEGIN CERTIFICATE-----
   MIIEwzCCA6ugAwIBAgIUYi...
   -----END CERTIFICATE-----
   EOF

   cloudflare_origin_key = <<EOF
   -----BEGIN PRIVATE KEY-----
   MIIEvgIBADANBgkqhkiG9w...
   -----END PRIVATE KEY-----
   EOF
   ```

## State Migration

If you need to migrate from the old shared state to environment-specific state:

### For Staging (if currently deployed)

```bash
# 1. Back up current state
cd terraform
terraform state pull > staging-backup.tfstate

# 2. Re-initialize with staging backend
make tf-init env=staging

# 3. Import existing resources (if needed)
# terraform import aws_vpc.main vpc-xxxxxx
# ... (repeat for other resources)
```

### For Production (first deployment)

```bash
# 1. Initialize production state
make tf-init env=production

# 2. Plan production deployment
make tf-plan env=production

# 3. Apply production infrastructure
make tf-apply env=production

# 4. Configure external database secret
SECRET_ARN=$(terraform output -raw external_database_secret_arn)
aws secretsmanager update-secret \
  --secret-id "$SECRET_ARN" \
  --secret-string '{"database_url": "mysql+pymysql://user:pass@host:3306/trigpoin_trigs"}'
```

## Troubleshooting

### Common Issues

1. **State File Conflicts**:
   ```bash
   # Error: workspace already exists
   # Solution: Use proper backend config
   make tf-init env=staging  # Not just 'terraform init'
   ```

2. **Missing CloudFlare Certificates**:
   ```bash
   # Error: cloudflare_origin_cert is required
   # Solution: Check certificate file exists and has valid content
   ls -la terraform/cloudflare-cert-trigpointing-*.tfvars
   ```

3. **Backend Access Issues**:
   ```bash
   # Error: Unable to list provider registration status
   # Solution: Check AWS credentials and S3 bucket access
   aws s3 ls s3://tuk-terraform-state/fastapi/
   ```

### Validation Commands

```bash
# Validate Terraform configuration
make tf-validate

# Format Terraform files
make tf-fmt

# Check current workspace and state
cd terraform && terraform workspace list
cd terraform && terraform state list
```

## Security Notes

- **State Files**: Contain sensitive data, stored encrypted in S3
- **Certificate Files**: Contain private keys, excluded from git
- **Secrets**: Database URLs stored in AWS Secrets Manager
- **Access**: Use IAM roles with minimal required permissions

## Best Practices

1. **Always specify environment**: `make tf-plan env=staging`
2. **Validate before apply**: `make tf-validate && make tf-plan env=production`
3. **Review plans carefully**: Especially for production changes
4. **Backup state**: Before major changes
5. **Test in staging**: Before production deployment
