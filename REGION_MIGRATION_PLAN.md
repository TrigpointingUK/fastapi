# Region Migration Plan: eu-west-2 to eu-west-1

## Overview

This document outlines the plan to migrate from London (eu-west-2) back to Ireland (eu-west-1) with minimal downtime. The migration involves moving infrastructure resources whilst maintaining service availability.

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

## Migration Strategy: Blue-Green with Staged Rollover

### Phase 1: Infrastructure Preparation (No Downtime)
**Estimated Time: 2-3 hours**

1. **Update Configuration Files** ✅ **(COMPLETED)**
   - All region references updated from eu-west-2 to eu-west-1
   - Availability zones updated to eu-west-1a, eu-west-1b
   - Application configuration updated

2. **Deploy New Infrastructure in eu-west-1**
   ```bash
   cd terraform

   # Deploy common infrastructure
   ./deploy.sh common

   # Deploy staging environment
   ./deploy.sh staging

   # Deploy production environment
   ./deploy.sh production
   ```

3. **Database Migration Setup**
   - Create DMS (Database Migration Service) replication instance in eu-west-1
   - Set up ongoing replication from eu-west-2 RDS to new eu-west-1 RDS
   - This allows real-time data sync during migration

### Phase 2: Application Deployment (No Downtime)
**Estimated Time: 1 hour**

1. **Deploy Applications to New Region**
   - ECS services will start in eu-west-1
   - Applications will initially connect to eu-west-2 database via DMS endpoint
   - Verify health checks pass

2. **Update Secrets Manager**
   - Copy all secrets from eu-west-2 to eu-west-1
   - Update connection strings to point to new RDS instance
   - Test secret retrieval

### Phase 3: Traffic Migration (Minimal Downtime)
**Estimated Downtime: 5-10 minutes per environment**

#### Staging Migration First
1. **DNS Update** (5 minutes downtime)
   - Update DNS record for `api.trigpointing.me`
   - Point from eu-west-2 ALB to eu-west-1 ALB
   - Monitor for 15-30 minutes

2. **Database Cutover** (2-3 minutes downtime)
   - Stop DMS replication
   - Update application to use eu-west-1 RDS directly
   - Restart ECS tasks
   - Verify functionality

#### Production Migration (After Staging Success)
1. **Scheduled Maintenance Window**
   - Announce 10-minute maintenance window
   - Follow same process as staging
   - Monitor closely for any issues

### Phase 4: Cleanup and Verification
**Estimated Time: 1 hour**

1. **Resource Cleanup**
   - Keep eu-west-2 resources running for 24-48 hours
   - Monitor for any issues
   - Once confirmed stable, destroy eu-west-2 resources

2. **Update CI/CD Pipeline**
   - GitHub Actions already updated to use eu-west-1
   - Test deployment pipeline
   - Update any remaining scripts or documentation

## Detailed Migration Steps

### Pre-Migration Checklist
- [ ] Backup all databases
- [ ] Document current DNS settings
- [ ] Prepare rollback plan
- [ ] Schedule maintenance window
- [ ] Notify stakeholders
- [ ] Prepare monitoring dashboards

### Step-by-Step Execution

#### 1. Deploy New Infrastructure
```bash
# Activate Python virtual environment
source venv/bin/activate

# Deploy common infrastructure
cd terraform
./deploy.sh common

# Deploy staging
./deploy.sh staging

# Deploy production
./deploy.sh production
```

#### 2. Set Up Database Migration
```bash
# Create DMS replication instance
aws dms create-replication-instance \
    --replication-instance-identifier trigpointing-migration \
    --replication-instance-class dms.t3.micro \
    --allocated-storage 20 \
    --availability-zone eu-west-1a

# Create source endpoint (eu-west-2)
aws dms create-endpoint \
    --endpoint-identifier source-mysql \
    --endpoint-type source \
    --engine-name mysql \
    --server-name fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com \
    --port 3306 \
    --username fastapi_admin \
    --password $(aws secretsmanager get-secret-value --secret-id fastapi-admin-credentials --region eu-west-2 --query SecretString --output text | jq -r '.password')

# Create target endpoint (eu-west-1)
# Get new RDS endpoint from terraform output
NEW_RDS_ENDPOINT=$(cd terraform/common && terraform output -raw rds_endpoint)
aws dms create-endpoint \
    --endpoint-identifier target-mysql \
    --endpoint-type target \
    --engine-name mysql \
    --server-name $NEW_RDS_ENDPOINT \
    --port 3306 \
    --username fastapi_admin \
    --password $(aws secretsmanager get-secret-value --secret-id fastapi-admin-credentials --region eu-west-1 --query SecretString --output text | jq -r '.password')

# Create replication task
aws dms create-replication-task \
    --replication-task-identifier trigpointing-full-load-cdc \
    --source-endpoint-arn $(aws dms describe-endpoints --filters Name=endpoint-id,Values=source-mysql --query 'Endpoints[0].EndpointArn' --output text) \
    --target-endpoint-arn $(aws dms describe-endpoints --filters Name=endpoint-id,Values=target-mysql --query 'Endpoints[0].EndpointArn' --output text) \
    --replication-instance-arn $(aws dms describe-replication-instances --filters Name=replication-instance-id,Values=trigpointing-migration --query 'ReplicationInstances[0].ReplicationInstanceArn' --output text) \
    --migration-type full-load-and-cdc \
    --table-mappings file://dms-table-mappings.json
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
