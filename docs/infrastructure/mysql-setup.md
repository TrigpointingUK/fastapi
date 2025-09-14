# MySQL Database Management

This directory contains Terraform configuration for managing MySQL databases, users, and schemas. This must be run from the bastion host as it requires direct network access to the RDS instance.

## Prerequisites

1. **Bastion Host Access**: SSH access to the bastion host
2. **AWS Credentials**: Copy your `~/.aws/credentials` to the bastion
3. **Common Infrastructure**: The `common` infrastructure must be deployed first

## Quick Start

1. **Copy files to bastion:**
   ```bash
   # From your laptop
   scp -r mysql/ ec2-user@<bastion-ip>:~/
   ```

2. **SSH into bastion:**
   ```bash
   ssh -i ~/.ssh/trigpointing-bastion.pem ec2-user@<bastion-ip>
   ```

3. **Deploy:**
   ```bash
   # On the bastion
   cd ~/mysql
   ./deploy.sh
   ```

## What This Creates

- **Database Schemas:**
  - `tuk_production` - Production database
  - `tuk_staging` - Staging database

- **Database Users:**
  - `admin` - Full admin access (auto-rotating password)
  - `fastapi_production` - Full access to production schema
  - `fastapi_staging` - Full access to staging schema
  - `backups` - SELECT-only access to both schemas

- **AWS Secrets Manager:**
  - All user credentials stored securely
  - Admin password auto-rotates every 30 days
  - Application passwords are static (manual rotation)

## Manual Operations

To run individual Terraform commands on the bastion:

```bash
# Initialize
terraform init -backend-config=backend.conf

# Plan changes
terraform plan

# Apply changes
terraform apply

# Destroy (be careful!)
terraform destroy
```

## Security Notes

- All database access is restricted to the private subnet
- Credentials are stored in AWS Secrets Manager
- Admin password rotates automatically
- Application passwords require manual rotation
