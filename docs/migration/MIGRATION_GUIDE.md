# Migration Guide: Old to New Infrastructure

This guide helps you migrate from the old Oregon-based infrastructure (`terraform-old/`) to the new consolidated Ireland-based infrastructure.

## Pre-Migration Checklist

- [ ] Ensure you have AWS CLI configured with appropriate permissions
- [ ] Have your CloudFlare origin certificates ready
- [ ] Backup any important data from the old infrastructure
- [ ] Note down current DNS settings and domain configurations
- [ ] Have your SSH key pair ready for bastion host access

## Migration Steps

### 1. Deploy New Infrastructure

```bash
# Navigate to the new terraform directory
cd terraform

# Deploy common infrastructure first
./deploy.sh common

# Deploy staging environment
./deploy.sh staging

# Deploy production environment
./deploy.sh production
```

### 2. Configure CloudFlare Certificates

Create certificate files for each environment:

```bash
# For staging
cp cloudflare-cert-example.tfvars cloudflare-cert-staging.tfvars
# Edit cloudflare-cert-staging.tfvars with your staging certificate

# For production
cp cloudflare-cert-example.tfvars cloudflare-cert-production.tfvars
# Edit cloudflare-cert-production.tfvars with your production certificate
```

Apply certificates:

```bash
# Staging
cd staging
terraform apply -var-file=../cloudflare-cert-staging.tfvars

# Production
cd production
terraform apply -var-file=../cloudflare-cert-production.tfvars
```

### 3. Update Application Secrets

Update the secrets in AWS Secrets Manager for each environment:

```bash
# Get the secret ARNs
cd staging && terraform output secrets_arn
cd ../production && terraform output secrets_arn

# Update secrets via AWS CLI or Console
aws secretsmanager update-secret \
  --secret-id <SECRET_ARN> \
  --secret-string '{
    "jwt_secret_key": "your-actual-jwt-secret",
    "database_url": "mysql+pymysql://username:password@rds-endpoint:3306/database",
    "auth0_client_id": "your-auth0-client-id",
    "auth0_client_secret": "your-auth0-client-secret"
  }'
```

### 4. Update Database Password

Connect to the new RDS instance and update the password:

```bash
# Get bastion IP
cd common && terraform output bastion_public_ip

# SSH to bastion host
ssh -i your-key.pem ec2-user@<bastion-ip>

# Connect to RDS and update password
mysql -h <rds-endpoint> -u fastapi_user -p
# Enter current password: temp-password-change-this
# Update password:
ALTER USER 'fastapi_user'@'%' IDENTIFIED BY 'your-new-secure-password';
FLUSH PRIVILEGES;
```

### 5. Test New Infrastructure

#### Test Staging
```bash
# Get staging ALB DNS name
cd staging && terraform output alb_dns_name

# Test health endpoint
curl -k https://<staging-alb-dns>/health

# Test with proper domain (if DNS is updated)
curl https://api.trigpointing.me/health
```

#### Test Production
```bash
# Get production ALB DNS name
cd production && terraform output alb_dns_name

# Test health endpoint
curl -k https://<production-alb-dns>/health

# Test with proper domain (if DNS is updated)
curl https://api.trigpointing.uk/health
```

### 6. Update DNS Records

Update your DNS records to point to the new ALB endpoints:

#### Staging
- **Record**: `api.trigpointing.me`
- **Type**: CNAME
- **Value**: `<staging-alb-dns-name>`

#### Production
- **Record**: `api.trigpointing.uk`
- **Type**: CNAME
- **Value**: `<production-alb-dns-name>`

### 7. Verify Application Functionality

- [ ] Health endpoints respond correctly
- [ ] Authentication works (if using Auth0)
- [ ] Database connections are working
- [ ] All API endpoints function as expected
- [ ] Monitoring and logging are working

### 8. Decommission Old Infrastructure

⚠️ **Only proceed after verifying new infrastructure is working correctly**

```bash
# Navigate to old infrastructure
cd terraform-old

# Plan destruction
terraform plan -destroy

# Apply destruction (be very careful!)
terraform destroy
```

## Rollback Plan

If issues arise, you can quickly rollback by:

1. **DNS Rollback**: Update DNS records back to old ALB endpoints
2. **Old Infrastructure**: Keep `terraform-old/` directory until migration is confirmed successful
3. **Database**: Old RDS instances should still be available if needed

## Cost Comparison

### Old Architecture (Oregon)
- 2 separate VPCs
- 2 separate ECS clusters
- 2 separate RDS instances (staging + production)
- 2 separate ALBs
- Higher costs due to duplication

### New Architecture (Ireland)
- 1 shared VPC
- 1 shared ECS cluster
- 1 shared RDS instance
- 2 ALBs (staging + production)
- Lower costs due to shared infrastructure

## Monitoring Migration

Monitor these metrics during migration:

- **Application Response Times**: Compare old vs new
- **Error Rates**: Watch for any increase in errors
- **Database Performance**: Monitor RDS metrics
- **Cost**: Track AWS costs during transition

## Troubleshooting

### Common Issues

1. **Certificate Errors**: Verify CloudFlare certificates are correctly formatted
2. **Database Connection**: Check security groups and RDS endpoint
3. **DNS Propagation**: Allow time for DNS changes to propagate
4. **Health Check Failures**: Verify application health endpoint is working

### Useful Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster trigpointing-cluster --services fastapi-staging-service

# View application logs
aws logs tail /ecs/fastapi-staging --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>

# Test database connection from bastion
ssh -i your-key.pem ec2-user@<bastion-ip>
mysql -h <rds-endpoint> -u fastapi_user -p
```

## Post-Migration Tasks

- [ ] Update CI/CD pipelines to use new infrastructure
- [ ] Update monitoring dashboards
- [ ] Update documentation
- [ ] Train team on new infrastructure
- [ ] Set up automated backups
- [ ] Configure alerting

## Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review Terraform logs: `terraform apply -auto-approve 2>&1 | tee migration.log`
3. Check AWS CloudWatch logs for application errors
4. Verify all security groups and network configurations
