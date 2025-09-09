# Security Configuration Guide

This document explains the new security configuration that moves all sensitive data to AWS Secrets Manager.

## 🔒 **Security Principles**

### **Before (Insecure)**
- JWT secrets in Terraform `.tfvars` files
- Database credentials in Terraform `.tfvars` files
- Auth0 credentials in separate secrets
- Sensitive data in version control

### **After (Secure)**
- All sensitive data in AWS Secrets Manager
- No secrets in Terraform files
- Unified app secrets for easier management
- No sensitive data in version control

## 🏗️ **New Architecture**

### **Unified App Secrets**
All sensitive configuration is now stored in a single AWS Secrets Manager secret:
- **Staging**: `fastapi-staging-app-secrets`
- **Production**: `fastapi-production-app-secrets`

### **Secret Structure**
```json
{
  "jwt_secret_key": "your-jwt-secret-key",
  "database_url": "mysql+pymysql://user:pass@host:3306/db",
  "auth0_client_id": "your-auth0-client-id",
  "auth0_client_secret": "your-auth0-client-secret",
  "auth0_domain": "trigpointing.eu.auth0.com"
}
```

## 📁 **File Changes**

### **Removed from .tfvars files:**
- `jwt_secret_key`
- `db_username`
- `db_password`
- `auth0_secret_name`
- `external_database_secret_name`

### **Removed from variables.tf:**
- `jwt_secret_key` variable
- `db_username` variable
- `db_password` variable
- `auth0_secret_name` variable
- `external_database_secret_name` variable

### **Updated in ECS Task Definition:**
- All secrets now come from `aws_secretsmanager_secret.app_secrets`
- Added `ENVIRONMENT` variable for secret name resolution

## 🚀 **Deployment Process**

### **1. Create AWS Secrets**
You need to create the app secrets in AWS Secrets Manager:

**Staging Secret (`fastapi-staging-app-secrets`):**
```json
{
  "jwt_secret_key": "your-staging-jwt-secret",
  "database_url": "mysql+pymysql://user:pass@staging-db:3306/trigpoin_trigs",
  "auth0_client_id": "your-staging-auth0-client-id",
  "auth0_client_secret": "your-staging-auth0-client-secret",
  "auth0_domain": "trigpointing.eu.auth0.com"
}
```

**Production Secret (`fastapi-production-app-secrets`):**
```json
{
  "jwt_secret_key": "your-production-jwt-secret",
  "database_url": "mysql+pymysql://user:pass@production-db:3306/trigpoin_trigs",
  "auth0_client_id": "your-production-auth0-client-id",
  "auth0_client_secret": "your-production-auth0-client-secret",
  "auth0_domain": "trigpointing.eu.auth0.com"
}
```

### **2. Deploy Infrastructure**
```bash
# Deploy to staging
terraform apply -var-file=staging.tfvars

# Deploy to production
terraform apply -var-file=production.tfvars
```

### **3. Verify Configuration**
Check that your ECS tasks have the correct environment variables:
- `JWT_SECRET_KEY` (from secrets)
- `DATABASE_URL` (from secrets)
- `AUTH0_CLIENT_ID` (from secrets)
- `AUTH0_CLIENT_SECRET` (from secrets)
- `AUTH0_DOMAIN` (from environment)
- `AUTH0_MANAGEMENT_API_AUDIENCE` (from environment)
- `AUTH0_API_AUDIENCE` (from environment)

## 🔧 **Application Changes**

### **Auth0 Service Updates**
- Now uses unified app secrets instead of separate Auth0 secret
- Automatically constructs secret name from environment
- Extracts Auth0 credentials from unified secret

### **Configuration Updates**
- Added `ENVIRONMENT` setting for secret name resolution
- Removed `AUTH0_SECRET_NAME` dependency
- All sensitive data now comes from AWS Secrets Manager

## 🛡️ **Security Benefits**

### **1. No Secrets in Version Control**
- All sensitive data removed from `.tfvars` files
- No accidental commits of secrets
- Clean git history

### **2. Centralized Secret Management**
- Single place to manage all app secrets
- Easy rotation and updates
- Consistent across environments

### **3. Environment Isolation**
- Separate secrets for staging and production
- No cross-environment contamination
- Clear separation of concerns

### **4. Audit Trail**
- AWS CloudTrail logs secret access
- IAM policies control access
- Detailed logging for troubleshooting

## 📋 **Migration Checklist**

### **Before Deployment:**
- [ ] Create staging app secret in AWS Secrets Manager
- [ ] Create production app secret in AWS Secrets Manager
- [ ] Verify all required fields are present in secrets
- [ ] Test secret access with AWS CLI

### **After Deployment:**
- [ ] Verify ECS tasks start successfully
- [ ] Check application logs for secret retrieval
- [ ] Test Auth0 token validation
- [ ] Test database connectivity
- [ ] Verify JWT token generation

## 🔍 **Troubleshooting**

### **Common Issues:**

1. **Secret Not Found**
   - Check secret name format: `fastapi-{environment}-app-secrets`
   - Verify secret exists in correct AWS region
   - Check IAM permissions for ECS tasks

2. **Missing Fields in Secret**
   - Verify all required fields are present
   - Check JSON format is valid
   - Ensure no trailing commas

3. **Auth0 Issues**
   - Verify `auth0_domain` matches secret
   - Check client credentials are correct
   - Verify audience configuration

### **Debug Commands:**
```bash
# Check secret exists
aws secretsmanager describe-secret --secret-id fastapi-staging-app-secrets

# Get secret value (for debugging)
aws secretsmanager get-secret-value --secret-id fastapi-staging-app-secrets

# Check ECS task environment variables
aws ecs describe-task-definition --task-definition fastapi-staging
```

## ✅ **Summary**

This security configuration provides:
- **Zero secrets in version control**
- **Centralized secret management**
- **Environment isolation**
- **Audit trail and monitoring**
- **Easy secret rotation**

All sensitive data is now properly secured in AWS Secrets Manager, with no differences between staging and production security practices.
