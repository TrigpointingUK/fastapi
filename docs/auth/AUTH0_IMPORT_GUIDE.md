# Auth0 Tenant Import Guide

This guide walks you through importing an existing Auth0 tenant into Terraform management.

## Overview

We're importing the existing `trigpointing` Auth0 tenant (which has real production users) into Terraform state, allowing us to manage it alongside our staging tenant while preserving all existing users, passwords, and configurations.

## Why Import Instead of Creating New?

- **Password Migration**: Auth0 doesn't export password hashes, so creating a new tenant would require all users to reset passwords
- **User Disruption**: Existing sessions, integrations, and the legacy login system remain intact
- **Data Preservation**: All user metadata, photos, logs, etc. stay in place
- **Lower Risk**: No data migration = fewer things that can go wrong

## Prerequisites

### 1. Create Terraform M2M Application

1. Log in to the Auth0 Dashboard for the `trigpointing` tenant
2. Go to **Applications** → **Create Application**
3. Name: `Terraform Management`
4. Type: `Machine to Machine Application`
5. Click **Create**
6. Authorise for **Auth0 Management API**
7. Grant **ALL** permissions (or at minimum: read/write for all resource types)
8. Save the **Client ID** and **Client Secret** - you'll need these

### 2. Verify Tenant Domain

1. In Auth0 Dashboard, go to **Settings** → **General**
2. Note your tenant domain (e.g., `trigpointing.eu.auth0.com` or `trigpointing.us.auth0.com`)
3. Verify the region (.eu, .us, .au, etc.)

### 3. Get Existing M2M Client Secret

You'll need the client secret from your existing `tuk-api` M2M application:

1. Go to **Applications** in Auth0 Dashboard
2. Find your existing M2M client (probably named something like `tuk-api`)
3. If you don't have the secret saved:
   - Rotate the client secret
   - Save the new secret immediately
   - Update it in AWS Secrets Manager for your production environment

## Import Process

### Step 1: Extract Resource IDs

Run the helper script to get all resource IDs from your tenant:

```bash
# Set credentials (matches staging naming convention)
export AUTH0_TENANT_DOMAIN="trigpointing.eu.auth0.com"  # Update with your actual domain
export AUTH0_TERRAFORM_PROVIDER_CLIENT_ID="<terraform_provider_client_id>"
export AUTH0_TERRAFORM_PROVIDER_CLIENT_SECRET="<terraform_provider_client_secret>"

# Run the extraction script
./scripts/get-auth0-ids.sh > auth0-resource-ids.txt

# Review the output
cat auth0-resource-ids.txt
```

**Important**: Use the Terraform provider M2M credentials, NOT the FastAPI M2M credentials.

This will show you all:
- Connection IDs
- Client IDs
- API identifiers
- Role IDs
- Action IDs
- Custom domain IDs
- Client grant IDs

### Step 2: Configure Terraform Variables

```bash
# Create the tfvars file from template
cd terraform/production
cp auth0.auto.tfvars.template auth0.auto.tfvars

# Edit with your actual values
nano auth0.auto.tfvars
```

Fill in:
- `auth0_tenant_domain`: From Step 1 above
- `auth0_custom_domain`: Should be `auth.trigpointing.uk`
- `auth0_terraform_client_id`: From the Terraform M2M app you created
- `auth0_terraform_client_secret`: From the Terraform M2M app you created
- `auth0_m2m_client_secret`: From your existing M2M client

**IMPORTANT**: The `auth0.auto.tfvars` file is gitignored. Never commit it!

### Step 3: Update Import Script with Resource IDs

Edit `scripts/import-auth0-production.sh` and fill in the resource ID variables at the top of the file with values from Step 1.

```bash
nano scripts/import-auth0-production.sh
```

Update these variables:
```bash
CONNECTION_ID="con_abc123"  # From get-auth0-ids.sh output
API_IDENTIFIER="https://api.trigpointing.uk/"
M2M_CLIENT_ID="..."
SWAGGER_CLIENT_ID="..."
# ... etc
```

### Step 4: Run the Import

```bash
./scripts/import-auth0-production.sh
```

This will:
1. Initialize Terraform in the production directory
2. Import all Auth0 resources into Terraform state
3. Import AWS resources (SES SMTP user, if configured)
4. Report success or any errors

### Step 5: Review the Plan

After import, check what Terraform wants to change:

```bash
cd terraform/production
terraform plan
```

**Expected outcomes:**

✅ **Best case**: "No changes. Infrastructure is up-to-date."

✅ **Acceptable**: Minor differences in non-critical fields:
- Action code formatting differences
- Email template customisation
- Tenant flag differences
- Connection option details (if they match your desired config)

⚠️ **Review carefully**:
- Changes to existing resources (make sure they're intentional)
- Any resource replacements (these should be rare)

❌ **Red flags** (DO NOT APPLY):
- Deleting the database connection
- Removing users
- Destroying and recreating clients (breaks existing integrations)

### Step 6: Resolve Drift

If Terraform shows changes, you have two options:

**Option A: Update Terraform to match reality**
- If the current Auth0 config is correct, update your Terraform code to match
- Example: Connection name, password policies, branding colours

**Option B: Accept Terraform's changes**
- If your Terraform config represents the desired state
- Review carefully before applying
- Test in staging first if possible

Common drift scenarios:

1. **Action Code**: Actions may have been manually edited in the dashboard
   - Copy the current code from Auth0 dashboard
   - Update `terraform/modules/auth0/actions/*.js.tpl` to match

2. **Connection Name**: If your connection isn't named `tuk-users`
   - Update `database_connection_name` in `terraform/production/auth0.tf`

3. **Password Policies**: May differ from Terraform defaults
   - Review and update `auth0_connection.database.options` in module

4. **Email Provider**: May not exist yet
   - Skip import if you're not using custom SMTP yet
   - Configure SES separately if needed

### Step 7: Backup Users

Before applying any changes:

```bash
# Export users as backup (requires auth0-cli)
auth0 users export --format ndjson > users-backup-$(date +%Y%m%d).ndjson

# Or use the API
./scripts/get-auth0-ids.sh  # (add user export to this script if needed)
```

### Step 8: Apply Changes (if safe)

Only apply if the plan looks safe:

```bash
cd terraform/production

# Create an execution plan
terraform plan -out=tfplan

# Review one more time
terraform show tfplan

# Apply if everything looks good
terraform apply tfplan
```

### Step 9: Test Everything

After applying:

1. **Test existing users**:
   - Try logging in with an existing user account
   - Verify no password reset required
   - Check user metadata is intact

2. **Test legacy integration**:
   - Verify `api.trigpointing.uk/v1/legacy/login` still works
   - Check user creation flow

3. **Test new user registration**:
   - Create a new test user
   - Verify post-registration action fires (if configured)
   - Check webhook hits FastAPI

4. **Test all clients**:
   - Website login: `www.trigpointing.uk`
   - API M2M tokens: Test with your FastAPI
   - Swagger OAuth2: `api.trigpointing.uk/docs`
   - Android app (if available)
   - Forum/Wiki (if configured)

## Troubleshooting

### Import Fails: "Resource not found"

**Problem**: Resource ID is incorrect or doesn't exist

**Solution**:
1. Re-run `./scripts/get-auth0-ids.sh` to verify IDs
2. Check the resource exists in Auth0 dashboard
3. Verify you're using the correct tenant domain

### Import Fails: "Already managed by Terraform"

**Problem**: Resource is already imported

**Solution**: This is fine! The script will continue. Just means you've already imported that resource.

### Plan Shows Connection Replacement

**Problem**: Terraform wants to destroy and recreate the database connection

**Solution**: 
1. **DO NOT APPLY** - this would delete all users!
2. Check the connection name matches between Terraform config and actual tenant
3. Update `database_connection_name` variable to match existing connection
4. Re-import if necessary

### Plan Shows Many Changes

**Problem**: Significant drift between Terraform config and actual state

**Solution**:
1. Review each change carefully
2. For each difference, decide: update Terraform or accept the change?
3. Test in staging first if possible
4. Consider doing a gradual rollout (apply small batches of changes)

### Users Can't Log In After Apply

**Problem**: Something broke authentication

**Solution**:
1. Check Auth0 Dashboard for errors
2. Verify callback URLs are correct
3. Check client IDs haven't changed
4. Review connection settings
5. If critical: revert Terraform changes with `terraform apply` using previous state

### M2M Client Secret Wrong

**Problem**: Can't authenticate to Management API

**Solution**:
1. Rotate the secret in Auth0 Dashboard
2. Update `auth0_m2m_client_secret` in `auth0.auto.tfvars`
3. Update in AWS Secrets Manager for production environment
4. Re-run terraform plan/apply

## Post-Import Workflow

After successful import, your workflow changes:

### Making Auth0 Changes

**Before**: Manual changes in Auth0 Dashboard

**After**:
1. Update Terraform code
2. Run `terraform plan` in staging
3. Test in staging environment
4. Apply to staging
5. Run `terraform plan` in production
6. Review carefully
7. Apply to production

### Rotating Secrets

Client secrets should still be rotated manually:
1. Rotate in Auth0 Dashboard
2. Update `auth0.auto.tfvars`
3. Update AWS Secrets Manager
4. Optionally update in Terraform state (not required)

### Adding New Clients

1. Add to `terraform/modules/auth0/main.tf`
2. Update `terraform/production/auth0.tf` with callbacks
3. Apply to staging first, test
4. Apply to production

## Success Criteria

✅ All resources imported without errors
✅ `terraform plan` shows no changes (or only acceptable drift)
✅ Existing users can log in successfully
✅ No password resets required
✅ Legacy login integration still works
✅ All clients authenticate correctly
✅ Post-registration webhooks work (if configured)

## Rollback Plan

If something goes wrong:

1. **Emergency**: Manually revert changes in Auth0 Dashboard
2. **Terraform state**: Restore from backup if you made one before applying
3. **Users**: Restore from NDJSON backup (requires manual re-import)

## Resources

- [Auth0 Terraform Provider Docs](https://registry.terraform.io/providers/auth0/auth0/latest/docs)
- [Auth0 Management API](https://auth0.com/docs/api/management/v2)
- [Terraform Import Command](https://www.terraform.io/docs/cli/commands/import.html)
- Auth0 Dashboard: https://manage.auth0.com/

## Getting Help

If you encounter issues:

1. Check Auth0 Dashboard logs: **Monitoring** → **Logs**
2. Review Terraform state: `terraform show`
3. Check this repository's issues for similar problems
4. Auth0 support documentation
5. Auth0 community forums

## Security Notes

- ⚠️ Never commit `auth0.auto.tfvars` - it contains secrets
- ⚠️ Never commit the output of `get-auth0-ids.sh` - it may contain sensitive IDs
- ⚠️ Rotate Terraform M2M credentials regularly
- ⚠️ Use MFA on your Auth0 dashboard account
- ⚠️ Review Auth0 logs regularly for suspicious activity

