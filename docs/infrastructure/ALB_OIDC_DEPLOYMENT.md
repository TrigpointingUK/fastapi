# ALB OIDC Deployment Steps

This document outlines the steps to deploy ALB OIDC authentication for admin tools.

## Overview

The Terraform configuration will:
1. Create Auth0 `aws-alb` application automatically
2. Create AWS Secrets Manager secret `trigpointing-alb-oidc-config` with placeholder values
3. Configure ALB listener rules with OIDC authentication
4. Deploy Auth0 Action to restrict access to api-admin users only

## Deployment Order

### Step 1: Apply Production Auth0 Configuration

```bash
cd terraform/production
terraform plan
# Review changes - should see:
# - auth0_client.alb (create)
# - auth0_action.alb_admin_only (create)
# - auth0_trigger_actions.post_login (update - add new action)
terraform apply
```

**Capture Client ID:**
```bash
CLIENT_ID=$(terraform output -raw auth0_alb_client_id)
echo "Client ID: $CLIENT_ID"
```

**Get Client Secret from Auth0 Dashboard:**
1. Go to Auth0 Dashboard → Applications
2. Find `tuk-aws-alb` application
3. Click "Settings" tab
4. Copy the "Client Secret" (click eye icon to reveal)
5. Save for next step

### Step 2: Apply Common Infrastructure

```bash
cd terraform/common
terraform plan
# Review changes - should see:
# - aws_secretsmanager_secret.alb_oidc (create)
# - aws_secretsmanager_secret_version.alb_oidc (create)
# - aws_lb_listener_rule.valkey_commander (update - add OIDC action)
# - aws_lb_listener_rule.phpmyadmin (update - add OIDC action)
terraform apply
```

### Step 3: Update Secrets Manager with Real Values

Get the Auth0 endpoints and credentials, then update the secret:

```bash
# Get client ID from terraform output
CLIENT_ID=$(cd ../production && terraform output -raw auth0_alb_client_id)

# Set client secret (from Auth0 dashboard - retrieved in Step 1)
read -s -p "Enter Auth0 Client Secret: " CLIENT_SECRET
echo

# Update the secret with real values
# IMPORTANT: Note the trailing slash on the issuer!
aws secretsmanager put-secret-value \
  --secret-id trigpointing-alb-oidc-config \
  --secret-string "{
    \"issuer\": \"https://auth.trigpointing.uk/\",
    \"authorization_endpoint\": \"https://auth.trigpointing.uk/authorize\",
    \"token_endpoint\": \"https://auth.trigpointing.uk/oauth/token\",
    \"user_info_endpoint\": \"https://auth.trigpointing.uk/userinfo\",
    \"client_id\": \"$CLIENT_ID\",
    \"client_secret\": \"$CLIENT_SECRET\"
  }" \
  --region eu-west-1
```

### Step 4: Verify Auth0 Configuration

1. Go to Auth0 Dashboard → Applications
2. Find `tuk-aws-alb` (production) application
3. Verify settings:
   - **Type**: Regular Web Application
   - **Allowed Callback URLs**:
     - `https://cache.trigpointing.uk/oauth2/idpresponse`
     - `https://phpmyadmin.trigpointing.uk/oauth2/idpresponse`
   - **Allowed Logout URLs**:
     - `https://cache.trigpointing.uk`
     - `https://phpmyadmin.trigpointing.uk`
   - **Grant Types**: Authorization Code, Refresh Token

### Step 5: Test Access

#### Test 1: Access Denied (Non-Admin User)

1. Create a test user or use existing non-admin user
2. Navigate to https://cache.trigpointing.uk
3. You'll be redirected to Auth0 login
4. After logging in, you should see: "Access denied: Access to admin tools requires api-admin role."

#### Test 2: Access Granted (Admin User)

1. Assign `api-admin` role to your user:
   ```bash
   # Via Auth0 Dashboard:
   # User Management → Users → Your User → Roles → Assign Roles → api-admin
   ```

2. Clear browser cookies or use incognito window
3. Navigate to https://cache.trigpointing.uk
4. You'll be redirected to Auth0 login
5. After logging in, you should see Redis Commander interface
6. Test https://phpmyadmin.trigpointing.uk similarly

### Step 6: (Optional) Deploy to Staging

Repeat the same process for staging:

```bash
cd terraform/staging
terraform plan
terraform apply

# Get staging outputs
CLIENT_ID=$(terraform output -raw auth0_alb_client_id)
CLIENT_SECRET=$(terraform output -raw auth0_alb_client_secret)

# Update staging secret (if separate)
aws secretsmanager put-secret-value \
  --secret-id trigpointing-staging-alb-oidc-config \
  --secret-string "{
    \"issuer\": \"https://auth.trigpointing.me\",
    \"authorization_endpoint\": \"https://auth.trigpointing.me/authorize\",
    \"token_endpoint\": \"https://auth.trigpointing.me/oauth/token\",
    \"user_info_endpoint\": \"https://auth.trigpointing.me/userinfo\",
    \"client_id\": \"$CLIENT_ID\",
    \"client_secret\": \"$CLIENT_SECRET\"
  }" \
  --region eu-west-1
```

## Verifying the Deployment

### Check Auth0 Action

1. Auth0 Dashboard → Actions → Library
2. Find `tuk-alb-admin-only`
3. Click to view code
4. Verify it references the correct client_id
5. Check it's deployed (green status)

### Check Auth0 Action Binding

1. Auth0 Dashboard → Actions → Flows → Login
2. Verify both actions are present:
   - `tuk-post-login` (adds roles to tokens)
   - `tuk-alb-admin-only` (blocks non-admin from ALB app)
3. Verify order: post-login first, then alb-admin-only

### Check ALB Listener Rules

```bash
aws elbv2 describe-rules \
  --listener-arn $(aws elbv2 describe-listeners \
    --load-balancer-arn $(aws elbv2 describe-load-balancers \
      --names trigpointing-alb \
      --query 'LoadBalancers[0].LoadBalancerArn' \
      --output text) \
    --query 'Listeners[?Port==`443`].ListenerArn' \
    --output text) \
  --region eu-west-1 \
  --query 'Rules[?Priority==`150` || Priority==`125`]'
```

Should show rules with `authenticate-oidc` action.

### Check Secrets Manager

```bash
aws secretsmanager get-secret-value \
  --secret-id trigpointing-alb-oidc-config \
  --region eu-west-1 \
  --query 'SecretString' \
  --output text | jq .
```

Should show non-placeholder values.

## Troubleshooting

### Issue: Auth0 application not created

**Symptom**: `terraform plan` shows no changes for auth0_client.alb

**Solution**: Check you're in the correct directory (production or staging) and terraform has initialized properly:
```bash
terraform init
terraform plan
```

### Issue: Secret not updating

**Symptom**: ALB returns 500 error after deployment

**Solution**: Verify secret was updated:
```bash
aws secretsmanager get-secret-value --secret-id trigpointing-alb-oidc-config --region eu-west-1
```

If still showing placeholders, manually update via console or re-run the `put-secret-value` command.

### Issue: Circular dependency error

**Symptom**: Terraform fails with circular dependency between action and client

**Solution**: This shouldn't happen with current config, but if it does:
1. First apply without the action: set `enable_alb_admin_only_action = false`
2. Apply terraform
3. Set `enable_alb_admin_only_action = true`
4. Apply terraform again

### Issue: Access denied for admin user

**Symptom**: User with api-admin role still gets "access denied"

**Solution**: 
1. Check role assignment in Auth0 Dashboard
2. Clear browser cookies
3. Log out and log back in to get fresh token
4. Check Auth0 logs for action execution

## Rollback Procedure

If you need to rollback:

### Option 1: Disable OIDC (Quick)

```bash
cd terraform/common
# Comment out the authenticate-oidc actions in:
# - valkey.tf
# - phpmyadmin.tf
terraform apply
```

### Option 2: Restore HTTP Auth to Redis Commander

```bash
cd terraform/modules/valkey
# Add back password to command in main.tf
terraform apply
```

### Option 3: Full Rollback

```bash
# Remove the action
cd terraform/production
# Set enable_alb_admin_only_action = false
terraform apply

# Remove ALB authentication
cd terraform/common
# Revert changes to listener rules
terraform apply
```

## Security Notes

- Client secrets are stored in Terraform state (encrypted at rest if using S3 backend)
- Secrets Manager secret is ignored after creation, allowing manual rotation without Terraform changes
- Auth0 Action checks roles on every login (can't bypass by caching old token)
- ALB validates OIDC tokens on every request
- Session timeout is 1 hour (configurable in listener rule)

## Next Steps

After successful deployment:

1. Assign `api-admin` role to all administrators who need access
2. Test access for each admin user
3. Remove any test users created during setup
4. Update runbooks to document admin tool access procedure
5. Set up monitoring for failed authentication attempts (Auth0 logs)
6. Document credential rotation procedure for team

