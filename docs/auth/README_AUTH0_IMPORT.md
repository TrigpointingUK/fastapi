# Auth0 Production Tenant Import - Quick Start

This directory contains the Terraform configuration for importing and managing the existing `trigpointing` Auth0 tenant.

## Quick Start

### 1. Prerequisites (Manual Steps Required)

Before you can run the import, complete these manual steps:

#### a) Create Terraform M2M Application in Auth0

1. Log in to Auth0 Dashboard: https://manage.auth0.com/
2. Select the `trigpointing` tenant
3. Go to **Applications** → **Create Application**
4. Name: `Terraform Management`
5. Type: **Machine to Machine Application**
6. Authorise for: **Auth0 Management API**
7. Grant **all permissions** (or at minimum all read/write scopes)
8. Save the **Client ID** and **Client Secret**

#### b) Get Your Existing M2M Client Secret

You need the secret from your existing M2M client (e.g., `tuk-api`):

1. Go to **Applications** in Auth0 Dashboard
2. Find your existing M2M client
3. If you don't have the secret saved, rotate it and save the new one
4. Update it in AWS Secrets Manager for production if rotated

### 2. Extract Resource IDs

```bash
# From project root (matches staging naming convention)
export AUTH0_TENANT_DOMAIN="trigpointing.eu.auth0.com"  # Update with actual domain!
export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID="<terraform_provider_client_id>"
export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET="<terraform_provider_client_secret>"

./scripts/get-auth0-ids.sh > auth0-resource-ids.txt
cat auth0-resource-ids.txt
```

**Important**: Use the Terraform provider M2M credentials, NOT the FastAPI M2M credentials.

Review the output and note down all the IDs.

### 3. Configure Terraform

```bash
cd terraform/production

# Create tfvars from template
cp auth0.auto.tfvars.template auth0.auto.tfvars

# Edit with your actual values
nano auth0.auto.tfvars
```

Fill in (matches staging naming convention):
- `auth0_tenant_domain` - From Auth0 Dashboard Settings
- `auth0_custom_domain` - Should be `auth.trigpointing.uk`
- `auth0_terraform_client_id` - From the Terraform provider M2M app
- `auth0_terraform_client_secret` - From the Terraform provider M2M app
- `auth0_m2m_client_secret` - From your existing FastAPI M2M client (tuk-api)

### 4. Update Import Script

```bash
# Edit the import script
nano ../../scripts/import-auth0-production.sh
```

Fill in all the resource ID variables at the top with values from step 2.

### 5. Run Import

```bash
# From project root
./scripts/import-auth0-production.sh
```

This will import all Auth0 resources into Terraform state.

### 6. Verify

```bash
cd terraform/production
terraform plan
```

**Expected**: No changes, or only minor acceptable drift.

**Red flags**: 
- Resource deletions
- Connection recreations
- User-impacting changes

### 7. Backup & Apply

```bash
# Backup users (if auth0-cli installed)
auth0 users export --format ndjson > users-backup.ndjson

# Generate plan
terraform plan -out=tfplan

# Review carefully
terraform show tfplan

# Apply if safe
terraform apply tfplan
```

### 8. Test

- [ ] Existing user can log in
- [ ] Legacy login works: `api.trigpointing.uk/v1/legacy/login`
- [ ] New user registration works
- [ ] All clients authenticate (website, API, Swagger, Android)

## Detailed Documentation

See comprehensive guides in `/docs/auth/`:

- **AUTH0_IMPORT_GUIDE.md** - Complete step-by-step guide with troubleshooting
- **AUTH0_IMPORT_CHECKLIST.md** - Checklist for tracking your progress

## Helper Scripts

- **scripts/get-auth0-ids.sh** - Extract all resource IDs from Auth0 tenant
- **scripts/import-auth0-production.sh** - Automated import of all resources

## Common Issues

### "Resource not found" during import

**Fix**: Double-check resource IDs from `get-auth0-ids.sh` output

### "Already managed by Terraform"

**Fix**: This is fine! Resource was already imported. Continue.

### Plan shows connection replacement

**Fix**: DO NOT APPLY! Update `database_connection_name` in auth0.tf to match existing connection name.

### Can't authenticate to Management API

**Fix**: 
1. Verify tenant domain is correct
2. Check M2M client has Management API permissions
3. Verify client ID and secret are correct

## Environment Variables Alternative

Instead of `auth0.auto.tfvars`, you can use environment variables (matches staging):

```bash
# For Terraform provider
export AUTH0_TENANT_DOMAIN="trigpointing.eu.auth0.com"
export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID="<terraform_provider_client_id>"
export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET="<terraform_provider_client_secret>"

# For Terraform variables
export TF_VAR_auth0_tenant_domain="trigpointing.eu.auth0.com"
export TF_VAR_auth0_custom_domain="auth.trigpointing.uk"
export TF_VAR_auth0_terraform_client_id="<terraform_provider_client_id>"
export TF_VAR_auth0_terraform_client_secret="<terraform_provider_client_secret>"
export TF_VAR_auth0_m2m_client_secret="<fastapi_m2m_secret>"

cd terraform/production
terraform plan
```

## Files in This Directory

- `main.tf` - Main infrastructure (ECS, ALB, etc.)
- `auth0.tf` - Auth0 module configuration
- `providers.tf` - Provider configuration
- `variables.tf` - Variable definitions
- `outputs.tf` - Output values
- `production.auto.tfvars` - Production environment variables
- `auth0.auto.tfvars` - Auth0 credentials (gitignored, you create this)
- `auth0.auto.tfvars.template` - Template for auth0.auto.tfvars
- `backend.conf` - Terraform state backend configuration

## Security

⚠️ **Never commit these files:**
- `auth0.auto.tfvars` - Contains secrets
- `auth0-resource-ids.txt` - Contains sensitive IDs
- `*.tfplan` - May contain sensitive data
- User backup files

These are already in `.gitignore`, but be careful!

## Getting Help

1. Check `/docs/auth/AUTH0_IMPORT_GUIDE.md` for detailed troubleshooting
2. Review Auth0 Dashboard logs: **Monitoring** → **Logs**
3. Check Terraform state: `terraform show`
4. Review Auth0 provider docs: https://registry.terraform.io/providers/auth0/auth0/latest/docs

## Next Steps After Import

Once imported successfully:

1. All future Auth0 changes should be made via Terraform
2. Test changes in staging first
3. Always run `terraform plan` before `terraform apply`
4. Keep `auth0.auto.tfvars` secure and backed up
5. Rotate Terraform M2M credentials regularly

## Rollback

If something goes wrong:

1. Manual fixes in Auth0 Dashboard (emergency)
2. Restore Terraform state from backup
3. Re-import resources if needed
4. Contact Auth0 support for critical issues

