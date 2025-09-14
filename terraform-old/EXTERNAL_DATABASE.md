# External Database Configuration for Production

This document explains how to configure FastAPI production environment to use an external MySQL 5.5 database instead of provisioning a new RDS instance.

## Overview

The production environment is configured to use your existing MySQL 5.5 database running on an EC2 instance. This is achieved through:

1. **Conditional RDS provisioning** - RDS resources are skipped when `use_external_database = true`
2. **AWS Secrets Manager** - Database connection details stored securely
3. **ECS integration** - Container reads database URL from Secrets Manager

## Configuration

### 1. Terraform Variables

In `production.tfvars`:

```hcl
# External database configuration (MySQL 5.5 on EC2)
use_external_database        = true
external_database_secret_name = "fastapi-production-external-db"
```

### 2. AWS Secrets Manager Setup

The Terraform will create a secret with a placeholder value. You need to update it manually:

#### After `terraform apply`, update the secret:

```bash
# Get the secret ARN from Terraform output
SECRET_ARN=$(terraform output -raw external_database_secret_arn)

# Update with your actual database URL
aws secretsmanager update-secret \
  --secret-id "$SECRET_ARN" \
  --secret-string '{
    "database_url": "mysql+pymysql://username:password@your-mysql-host:3306/trigpoin_trigs"
  }'
```

### 3. Database URL Format

The database URL should follow this format:

```
mysql+pymysql://USERNAME:PASSWORD@HOSTNAME:PORT/DATABASE_NAME
```

**Example:**
```
mysql+pymysql://fastapi_user:secure_password@mysql.trigpointing.me:3306/trigpoin_trigs
```

### 4. Required Database Permissions

Ensure your MySQL user has the following permissions on the `trigpoin_trigs` database:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON trigpoin_trigs.* TO 'fastapi_user'@'%';
FLUSH PRIVILEGES;
```

## Security Considerations

### 1. Network Access

Since you're using an external database, ensure:

- Your MySQL 5.5 instance accepts connections from AWS
- Proper firewall rules are in place
- Consider using SSL/TLS for database connections

### 2. Secrets Management

- The database URL is stored encrypted in AWS Secrets Manager
- ECS tasks have minimal IAM permissions to read only this specific secret
- The secret value is ignored by Terraform after creation (manual updates won't be overwritten)

### 3. Connection String Security

Include all security parameters in your connection string:

```
mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4&ssl_disabled=false
```

## Deployment Process

### 1. Initial Deployment

```bash
# 1. Deploy infrastructure
terraform apply -var-file=production.tfvars

# 2. Update the database secret (see step 2 above)
aws secretsmanager update-secret ...

# 3. Restart ECS service to pick up new secret
aws ecs update-service \
  --cluster fastapi-production-cluster \
  --service fastapi-production-service \
  --force-new-deployment
```

### 2. Updating Database Connection

To change database credentials or host:

```bash
# Update secret
aws secretsmanager update-secret \
  --secret-id "fastapi-production-external-db" \
  --secret-string '{"database_url": "mysql+pymysql://new_user:new_pass@new_host:3306/trigpoin_trigs"}'

# Force ECS deployment to pick up changes
aws ecs update-service \
  --cluster fastapi-production-cluster \
  --service fastapi-production-service \
  --force-new-deployment
```

## Monitoring

### 1. Database Connection Health

Monitor ECS task logs for database connection issues:

```bash
aws logs tail /aws/ecs/fastapi-production --follow
```

### 2. Secrets Manager Access

Check CloudTrail for secrets access:

```bash
aws logs filter-log-events \
  --log-group-name CloudTrail/SecretManagerAccess \
  --filter-pattern "secretsmanager"
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check MySQL server is running and accessible
   - Verify firewall rules allow connections from AWS
   - Confirm the hostname/IP is correct

2. **Authentication Failed**
   - Verify username/password in secret
   - Check MySQL user permissions
   - Ensure user can connect from AWS IP ranges

3. **Database Not Found**
   - Confirm `trigpoin_trigs` database exists
   - Check user has access to the specific database
   - Verify database name spelling

4. **ECS Tasks Failing**
   - Check ECS task logs for specific error messages
   - Verify IAM permissions for secrets access
   - Confirm secret ARN is correct in task definition

### Validation Commands

```bash
# Test secret retrieval
aws secretsmanager get-secret-value \
  --secret-id "fastapi-production-external-db"

# Check ECS task status
aws ecs describe-services \
  --cluster fastapi-production-cluster \
  --services fastapi-production-service

# View recent task logs
aws logs tail /aws/ecs/fastapi-production --since 10m
```

## Migration Notes

- This setup maintains compatibility with your existing MySQL 5.5 schema
- The FastAPI application uses the same `trigpoin_trigs` database/schema name
- Connection pooling and retry logic are handled by SQLAlchemy
- Future migration to RDS can be done by changing `use_external_database = false`
