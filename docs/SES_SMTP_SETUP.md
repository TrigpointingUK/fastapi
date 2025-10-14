# SES SMTP Setup Instructions

## Overview

This document describes the SES SMTP user setup for MediaWiki and phpBB email sending.

## What Was Created

1. **Terraform Module**: `terraform/modules/ses-smtp-user/`
   - Reusable module for creating SES SMTP users
   - Generates IAM user with SES sending permissions
   - Creates access keys and derives SMTP password

2. **SES Resources** in `terraform/common/ses.tf`:
   - Email identity verification for `noreply@trigpointing.uk`
   - Email identity verification for `admin@trigpointing.uk`
   - SMTP user: `smtp-mediawiki` (new)
   - SMTP user: `smtp-phpbb` (to be imported)

3. **Terraform Outputs** in `terraform/common/outputs.tf`:
   - `mediawiki_smtp_username` (sensitive)
   - `mediawiki_smtp_password` (sensitive)
   - `phpbb_smtp_username` (sensitive)
   - `phpbb_smtp_password` (sensitive)

4. **MediaWiki Configuration**:
   - Updated `terraform/modules/mediawiki/main.tf` to read SMTP credentials from app secrets
   - Updated `wiki/LocalSettings.php` to use SMTP for email sending
   - SMTP credentials stored in existing `trigpointing-mediawiki-app-secrets` secret

## Import Existing phpBB SMTP User

The `smtp-phpbb` user already exists and needs to be imported into Terraform state:

```bash
cd /home/ianh/dev/fastapi/terraform/common

# Import the IAM user
terraform import 'module.smtp_phpbb.aws_iam_user.smtp_user' smtp-phpbb

# Import the IAM policy (you may need to find the policy name first)
# List policies for the user to get the exact name:
aws iam list-user-policies --user-name smtp-phpbb --region eu-west-1

# Then import using the format: user_name:policy_name
terraform import 'module.smtp_phpbb.aws_iam_user_policy.smtp_user_policy' smtp-phpbb:smtp-phpbb-ses-policy

# Import the access key (you'll need the access key ID)
# List access keys to get the ID:
aws iam list-access-keys --user-name smtp-phpbb --region eu-west-1

# Then import using the format: username:access_key_id
terraform import 'module.smtp_phpbb.aws_iam_access_key.smtp_credentials' smtp-phpbb:AKIAXXXXXXXXXXXXXXXX
```

**Note**: If the phpBB user has different policy name or multiple access keys, adjust accordingly.

## Deployment Steps

### 1. Apply Terraform Changes

```bash
cd /home/ianh/dev/fastapi/terraform/common

# Initialize and plan
terraform init
terraform plan

# Apply (this will create smtp-mediawiki user and email identities)
terraform apply
```

### 2. Verify SES Email Addresses

After applying, AWS will send verification emails to:
- noreply@trigpointing.uk
- admin@trigpointing.uk

**Action Required**: Click the verification links in these emails.

Alternatively, if using SES sandbox mode, verify via AWS Console:
```bash
# Check verification status
aws ses get-identity-verification-attributes \
  --identities noreply@trigpointing.uk admin@trigpointing.uk \
  --region eu-west-1
```

### 3. Get SMTP Credentials from Terraform Outputs

```bash
cd /home/ianh/dev/fastapi/terraform/common

# Get MediaWiki SMTP credentials
terraform output -raw mediawiki_smtp_username
terraform output -raw mediawiki_smtp_password
```

### 4. Update MediaWiki App Secrets

Update the existing `trigpointing-mediawiki-app-secrets` secret with the SMTP credentials:

```bash
# Get current secret value
aws secretsmanager get-secret-value \
  --secret-id trigpointing-mediawiki-app-secrets \
  --region eu-west-1 \
  --query SecretString \
  --output text > /tmp/mediawiki-secrets.json

# Edit /tmp/mediawiki-secrets.json and add:
# "SMTP_USERNAME": "<value from terraform output>",
# "SMTP_PASSWORD": "<value from terraform output>"

# Update the secret
aws secretsmanager update-secret \
  --secret-id trigpointing-mediawiki-app-secrets \
  --secret-string file:///tmp/mediawiki-secrets.json \
  --region eu-west-1

# Clean up
rm /tmp/mediawiki-secrets.json
```

### 5. Restart MediaWiki ECS Service

```bash
aws ecs update-service \
  --cluster trigpointing-cluster \
  --service trigpointing-mediawiki-common \
  --force-new-deployment \
  --region eu-west-1
```

### 6. Test Email Sending

Log in to MediaWiki and:
1. Go to Special:EmailUser
2. Send a test email to yourself
3. Check CloudWatch logs for any SMTP errors

## SES Production Access

If you need to move out of SES sandbox mode (to send to unverified addresses):

```bash
# Request production access via AWS Console
# Or use AWS CLI to check current status:
aws sesv2 get-account --region eu-west-1
```

Production access requires:
- Justification for sending volume
- Description of email types
- Process for handling bounces/complaints
- SPF/DKIM records configured

## Troubleshooting

### SMTP Authentication Errors

Check that credentials are correctly populated:
```bash
aws ecs execute-command \
  --cluster trigpointing-cluster \
  --task <task-id> \
  --container trigpointing-mediawiki \
  --interactive \
  --command "/bin/bash"

# Inside container:
echo $SMTP_USERNAME
echo $SMTP_PASSWORD  # Should be set but value hidden
```

### Email Not Sending

1. Check CloudWatch logs: `/aws/ecs/trigpointing-mediawiki-common`
2. Verify email identities are verified in SES
3. Check SES sending statistics:
   ```bash
   aws ses get-send-statistics --region eu-west-1
   ```

### IAM Permission Errors

Ensure the IAM user policy allows SES sending:
```bash
aws iam get-user-policy \
  --user-name smtp-mediawiki \
  --policy-name smtp-mediawiki-ses-policy \
  --region eu-west-1
```

## Security Notes

- SMTP credentials are sensitive and stored securely in AWS Secrets Manager
- Credentials have `lifecycle.ignore_changes` to prevent accidental exposure
- Use `terraform output` with care - outputs are sensitive
- Consider rotating SMTP credentials periodically

## Cost Implications

- SES: $0.10 per 1,000 emails (first 62,000/month free on EC2/Lambda/ECS)
- IAM users: Free
- Secrets Manager: $0.40/month per secret (existing secret, no additional cost)
