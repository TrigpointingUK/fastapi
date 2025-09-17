# Fresh Deployment Plan: eu-west-1 (Ireland)

## Overview

This document outlines the plan to deploy fresh infrastructure in Ireland (eu-west-1). Since the staging database contains no important data, we'll deploy completely new infrastructure without complex migration procedures.

## Current State Analysis

### Existing Resources (eu-west-2)
Based on the codebase analysis, the following resources are currently deployed:

**Common Infrastructure:**
- VPC with 2 availability zones (eu-west-2a, eu-west-2b)
- ECS Cluster (`trigpointing-cluster`)
- RDS MySQL instance (`fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com`)
- Bastion host for database access
- Application Load Balancer
- DynamoDB tables for session/state management
- Lambda functions for password rotation
- CloudWatch logs and monitoring

**Environment-Specific:**
- **Staging**: ECS service (`fastapi-staging-service`), Target groups, Secrets
- **Production**: ECS service (`fastapi-production-service`), Target groups, Secrets

**External Dependencies:**
- CloudFlare SSL certificates
- Auth0 authentication service
- GitHub Actions CI/CD pipeline
- DNS records pointing to ALB endpoints

## Deployment Strategy: Fresh Infrastructure

### Phase 1: Deploy Infrastructure (1-2 hours)
**No downtime - completely new deployment**

1. **Configuration Updates** ✅ **(COMPLETED)**
   - All region references updated from eu-west-2 to eu-west-1
   - Availability zones updated to eu-west-1a, eu-west-1b
   - Terraform state configured for new deployment

2. **Deploy Infrastructure in eu-west-1**
   ```bash
   cd terraform/common
   terraform apply

   cd ../staging
   terraform init -backend-config=backend.conf
   terraform apply

   cd ../production
   terraform init -backend-config=backend.conf
   terraform apply
   ```

### Phase 2: Application Setup (30 minutes)
**Fresh setup - no migration needed**

1. **Create Secrets in eu-west-1**
   - Set up new secrets in AWS Secrets Manager
   - Configure database credentials
   - Set up Auth0 integration secrets

2. **Deploy Applications**
   - ECS services will start with fresh database
   - No data migration needed for staging
   - Production data can be imported separately if needed

### Phase 3: DNS Cutover (5-10 minutes downtime)
**Simple DNS change**

1. **Update DNS Records**
   - Point `api.trigpointing.me` to new staging ALB
   - Point `api.trigpointing.uk` to new production ALB
   - Monitor for proper resolution

### Phase 4: Cleanup (Optional)
**Clean up old resources when ready**

1. **eu-west-2 Resources**
   - Can be destroyed immediately for staging (no important data)
   - Keep production resources until data is migrated
   - No complex coordination needed

## Detailed Deployment Steps

### Pre-Deployment Checklist
- [ ] Ensure CloudFlare API token is configured
- [ ] Have SSH key pair ready for bastion access
- [ ] Prepare secrets for Secrets Manager
- [ ] Schedule brief DNS cutover window
- [ ] Prepare monitoring dashboards

### Step-by-Step Execution

#### 1. Deploy Common Infrastructure
```bash
# Activate Python virtual environment
source venv/bin/activate

# Deploy common infrastructure
cd terraform/common
terraform apply

# Deploy staging
cd ../staging
terraform init -backend-config=backend.conf
terraform apply

# Deploy production
cd ../production
terraform init -backend-config=backend.conf
terraform apply
```

#### 2. Set Up Secrets Manager
```bash
# Get RDS endpoint from terraform output
cd terraform/common
NEW_RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
ADMIN_PASSWORD=$(terraform output -raw admin_password)

# Create secrets for staging
aws secretsmanager create-secret \
    --name "fastapi-staging-credentials" \
    --description "FastAPI staging database credentials" \
    --secret-string "{\"host\":\"$NEW_RDS_ENDPOINT\",\"port\":3306,\"username\":\"fastapi_staging\",\"password\":\"staging_password_here\",\"dbname\":\"tuk_staging\"}" \
    --region eu-west-1

# Create secrets for production
aws secretsmanager create-secret \
    --name "fastapi-production-credentials" \
    --description "FastAPI production database credentials" \
    --secret-string "{\"host\":\"$NEW_RDS_ENDPOINT\",\"port\":3306,\"username\":\"fastapi_production\",\"password\":\"production_password_here\",\"dbname\":\"tuk_production\"}" \
    --region eu-west-1

# Create app secrets for staging
aws secretsmanager create-secret \
    --name "fastapi-staging-app-secrets" \
    --description "FastAPI staging application secrets" \
    --secret-string "{\"jwt_secret_key\":\"your-jwt-secret\",\"auth0_client_id\":\"your-auth0-client-id\",\"auth0_client_secret\":\"your-auth0-client-secret\"}" \
    --region eu-west-1

# Create app secrets for production
aws secretsmanager create-secret \
    --name "fastapi-production-app-secrets" \
    --description "FastAPI production application secrets" \
    --secret-string "{\"jwt_secret_key\":\"your-jwt-secret\",\"auth0_client_id\":\"your-auth0-client-id\",\"auth0_client_secret\":\"your-auth0-client-secret\"}" \
    --region eu-west-1
```

#### 3. Application Deployment
```bash
# Force new deployment in new region
aws ecs update-service \
    --cluster trigpointing-cluster \
    --service fastapi-staging-service \
    --force-new-deployment \
    --region eu-west-1

aws ecs update-service \
    --cluster trigpointing-cluster \
    --service fastapi-production-service \
    --force-new-deployment \
    --region eu-west-1

# Monitor deployment
aws ecs wait services-stable \
    --cluster trigpointing-cluster \
    --services fastapi-staging-service \
    --region eu-west-1
```

#### 4. DNS Migration (Staging First)
```bash
# Get new ALB DNS names
STAGING_ALB=$(cd terraform/staging && terraform output -raw alb_dns_name)
PRODUCTION_ALB=$(cd terraform/production && terraform output -raw alb_dns_name)

# Update DNS records (via CloudFlare API or manually)
# api.trigpointing.me -> $STAGING_ALB
# api.trigpointing.uk -> $PRODUCTION_ALB
```

#### 5. Database Cutover
```bash
# Stop DMS task
aws dms stop-replication-task \
    --replication-task-arn $(aws dms describe-replication-tasks --filters Name=replication-task-id,Values=trigpointing-full-load-cdc --query 'ReplicationTasks[0].ReplicationTaskArn' --output text)

# Update application secrets to use new RDS endpoint
# This will trigger ECS task restart
aws secretsmanager update-secret \
    --secret-id fastapi-staging-credentials \
    --region eu-west-1 \
    --secret-string "{\"host\":\"$NEW_RDS_ENDPOINT\",\"port\":3306,...}"
```

## Rollback Plan

### Immediate Rollback (if issues within first hour)
1. **DNS Rollback**: Update DNS records back to eu-west-2 ALB endpoints
2. **Database**: Applications can continue using eu-west-2 RDS
3. **Time to rollback**: 5-10 minutes

### Extended Rollback (if issues discovered later)
1. **Keep eu-west-2 resources**: Don't destroy for 48 hours
2. **Reverse DMS**: Set up replication from eu-west-1 back to eu-west-2
3. **Full rollback**: Complete reversal possible within 2 hours

## Risk Mitigation

### High Risk Items
1. **Database Migration**: Use DMS for zero-downtime replication
2. **DNS Propagation**: Plan for up to 15 minutes propagation time
3. **SSL Certificates**: Ensure CloudFlare certs are properly configured

### Monitoring During Migration
- **Application Health**: Monitor `/health` endpoints
- **Database Connections**: Watch for connection errors
- **Response Times**: Compare eu-west-1 vs eu-west-2 performance
- **Error Rates**: Monitor application logs and CloudWatch metrics

## Success Criteria

### Technical Validation
- [ ] All health checks passing in eu-west-1
- [ ] Database queries executing successfully
- [ ] Authentication working (Auth0 integration)
- [ ] All API endpoints responding correctly
- [ ] CI/CD pipeline deploying to eu-west-1

### Performance Validation
- [ ] Response times comparable to eu-west-2
- [ ] No increase in error rates
- [ ] Database performance metrics stable
- [ ] Memory and CPU usage within expected ranges

### Business Validation
- [ ] User login/registration working
- [ ] Data integrity maintained
- [ ] All application features functional
- [ ] No user-reported issues

## Timeline

### Total Migration Time: 4-6 hours
- **Phase 1** (Infrastructure): 2-3 hours
- **Phase 2** (Applications): 1 hour
- **Phase 3** (Traffic): 30 minutes (5-10 min downtime per environment)
- **Phase 4** (Verification): 1 hour

### Recommended Schedule
- **Start**: Early morning (e.g., 6:00 AM UTC) for minimal user impact
- **Staging Migration**: 8:00 AM UTC
- **Production Migration**: 10:00 AM UTC (after staging validation)
- **Full Verification**: 12:00 PM UTC

## Cost Impact

### Migration Costs
- **DMS Instance**: ~£20/day during migration
- **Dual Infrastructure**: ~2x costs for 24-48 hours
- **Data Transfer**: Minimal (within AWS)

### Long-term Savings
- **Latency**: Better performance for UK users
- **Existing Resources**: Leverage existing eu-west-1 resources
- **Operational**: Simplified management in single region

## Post-Migration Tasks

### Immediate (Within 24 hours)
- [ ] Monitor all application metrics
- [ ] Verify backup procedures working
- [ ] Update monitoring dashboards
- [ ] Test disaster recovery procedures

### Within 1 Week
- [ ] Clean up DMS resources
- [ ] Destroy eu-west-2 infrastructure
- [ ] Update all documentation
- [ ] Conduct post-migration review

### Within 1 Month
- [ ] Optimise new infrastructure based on usage patterns
- [ ] Review and adjust auto-scaling policies
- [ ] Update disaster recovery procedures
- [ ] Train team on new infrastructure

## Contact Information

### Key Personnel
- **Migration Lead**: [Your Name]
- **Database Admin**: [DBA Name]
- **DevOps Engineer**: [DevOps Name]
- **Application Owner**: [App Owner Name]

### Emergency Contacts
- **AWS Support**: [Support Case Number]
- **CloudFlare Support**: [Support Details]
- **On-call Engineer**: [Contact Details]

---

**Note**: This migration plan should be reviewed and tested in a staging environment before executing in production. All stakeholders should be notified of the planned maintenance window.
