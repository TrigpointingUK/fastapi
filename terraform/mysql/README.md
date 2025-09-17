# MySQL Terraform Configuration

⚠️ **IMPORTANT: This Terraform configuration can ONLY be run from the bastion host!**

## Why Bastion Host Required

This directory contains MySQL Terraform configuration that:
- Creates MySQL databases and users
- Requires direct connection to RDS instance
- RDS is in private subnet, only accessible from bastion host
- Cannot be run locally due to network restrictions

## Usage

### Option 1: Automatic Deployment (Recommended)
```bash
# From your local machine
./deploy.sh
```

This will:
1. Copy all files to bastion host
2. Run terraform on bastion
3. Deploy MySQL databases and users

### Option 2: Manual SSH Deployment
```bash
# SSH to bastion
ssh -i ~/.ssh/trigpointing-bastion.pem ec2-user@63.32.182.69

# Navigate to terraform directory
cd /home/ec2-user/mysql-terraform

# Run terraform commands
terraform init -backend-config=backend.conf
terraform plan
terraform apply
```

## What This Creates

- **Databases**: `tuk_production`, `tuk_staging`
- **Users**: `fastapi_production`, `fastapi_staging`, `backups`
- **Secrets**: Stored in AWS Secrets Manager for each user

## Connecting to Database

### RDS Master User (for administration)
```bash
# On bastion host
./connect-to-rds-master.sh
```

### Application Users
Use the credentials stored in AWS Secrets Manager:
- `fastapi-production-credentials`
- `fastapi-staging-credentials`
- `fastapi-backups-credentials`

## Safety Features

- Local `terraform` command is blocked (use `./deploy.sh` instead)
- `.cursorrules` file enforces remote execution
- Clear error messages guide proper usage

## Troubleshooting

If you see "could not connect to server" errors:
1. Ensure you're running from bastion host
2. Check RDS security groups allow bastion access
3. Verify AWS credentials are configured on bastion
4. Use `./connect-to-rds-master.sh` to test RDS connectivity
