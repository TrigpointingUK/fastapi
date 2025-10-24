# Import Legacy Auth0 Client into Terraform

## Problem

The "legacy" Auth0 application keeps losing its connection to the `tuk-users` database because Terraform's `auth0_connection_clients` resource explicitly manages which clients are enabled. Every time Terraform runs, it sets the enabled clients to only those in its list, removing any manually-added clients.

## Solution

Import the legacy client into Terraform so it's included in the managed list.

## Steps

### Step 1: Find the Legacy Client in Auth0

1. Go to Auth0 Dashboard → Applications
2. Find the application named "legacy" (or similar - might be "tuk-legacy" or just "legacy")
3. Click on the application
4. Copy the **Client ID** (e.g., `AbC123...`)

### Step 2: Import the Client into Terraform

The Terraform configuration has already been updated to include a `auth0_client.legacy` resource. Now we need to import the existing client.

```bash
cd terraform/production

# Import the legacy client
# Replace CLIENT_ID_HERE with the actual client ID from Step 1
terraform import module.auth0.auth0_client.legacy CLIENT_ID_HERE
```

**Example:**
```bash
terraform import module.auth0.auth0_client.legacy AbC123XyZ789
```

### Step 3: Verify the Import

```bash
terraform state show module.auth0.auth0_client.legacy
```

This should show the imported client's details.

### Step 4: Plan and Apply

```bash
terraform plan

# Review the plan - should show:
# - auth0_connection_clients.database_clients will be updated (to add legacy client)
# - Possibly some changes to auth0_client.legacy if the name doesn't match exactly

terraform apply
```

### Step 5: Verify Connection

1. Go to Auth0 Dashboard → Authentication → Database → tuk-users
2. Click "Applications" tab
3. Verify that "legacy" (or your legacy app) is now in the list and enabled

## What Was Changed in Terraform

**File: `terraform/modules/auth0/main.tf`**

1. Added `auth0_client.legacy` resource (around line 308-320)
2. Added `auth0_client.legacy.id` to the `enabled_clients` list (line 102)

This ensures the legacy client:
- Is managed by Terraform (won't be accidentally deleted)
- Is always included in the database connection's enabled clients list
- Won't be removed when Terraform runs

## Troubleshooting

### Error: "resource already exists"

If you get an error that the resource already exists when importing:
```
Error: resource already managed by Terraform
```

This means it's already imported. Skip to Step 4.

### Error: "resource not found" during import

If you get this error:
```
Error: Cannot import non-existent remote object
```

Check that:
1. The Client ID is correct (no typos)
2. You're in the right Auth0 tenant (production vs staging)
3. The application actually exists in Auth0 Dashboard

### Wrong Application Name

If after import, Terraform wants to rename the application:

```hcl
# module.auth0.auth0_client.legacy will be updated in-place
~ name = "legacy" -> "tuk-legacy"
```

You have two options:

**Option A:** Let Terraform rename it (safer)
```bash
terraform apply
```

**Option B:** Update the Terraform resource to match the current name:

Edit `terraform/modules/auth0/main.tf` around line 311:
```hcl
resource "auth0_client" "legacy" {
  name        = "legacy"  # Remove the var.name_prefix
  description = "Legacy application (${var.environment})"
  app_type    = "regular_web"
  
  lifecycle {
    # If you want to prevent Terraform from changing the name
    ignore_changes = [name]
  }
}
```

## Repeat for Staging (if needed)

If you also have a legacy client in the staging environment:

```bash
cd terraform/staging
terraform import module.auth0.auth0_client.legacy STAGING_CLIENT_ID_HERE
terraform plan
terraform apply
```

## Preventing Future Issues

After this import, the legacy client will be permanently included in Terraform's management. It will:
- ✅ Always remain enabled on the database connection
- ✅ Be tracked in Terraform state
- ✅ Be included in terraform plans
- ✅ Not be accidentally removed

## Alternative: Use Data Source (Not Recommended)

If you don't want to fully manage the legacy client in Terraform (not recommended), you could use a data source instead:

```hcl
# In terraform/modules/auth0/main.tf
data "auth0_client" "legacy" {
  client_id = "YOUR_CLIENT_ID"
}

# Then in enabled_clients:
enabled_clients = concat(
  [
    # ... other clients ...
    data.auth0_client.legacy.id,
  ],
  # ...
)
```

However, this requires hardcoding the client ID and doesn't protect against the client being deleted. **Importing is the better approach.**

