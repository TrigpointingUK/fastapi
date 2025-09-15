# Infrastructure Configuration Explanation

This document explains how environment configuration works in this FastAPI project and clarifies the role of different configuration files.

## 🏗️ **How Configuration Actually Works**

### **Production & Staging Environments (AWS ECS)**
- **Configuration Source**: Terraform `.tfvars` files
- **Deployment**: AWS ECS Task Definition sets environment variables
- **Secrets**: AWS Secrets Manager for sensitive data
- **Files Used**: `terraform/staging.tfvars`, `terraform/production.tfvars`

### **Local Development**
- **Configuration Source**: `.env` files (created from `env.example`)
- **Deployment**: Local Python process
- **Secrets**: Local environment variables
- **Files Used**: `env.example`, `setup.sh` script

## 📁 **File Roles Explained**

### **`env.example`**
- **Purpose**: Template for local development
- **Used By**: `scripts/setup.sh` (local development only)
- **NOT Used In**: Staging or production environments
- **Contains**: Example environment variables for local setup

### **`terraform/*.tfvars`**
- **Purpose**: Environment-specific configuration for AWS
- **Used By**: Terraform for infrastructure deployment
- **Contains**: All environment variables, secrets references, infrastructure settings

### **`terraform/ecs.tf`**
- **Purpose**: ECS Task Definition that sets environment variables
- **How It Works**: Reads from `.tfvars` files and sets container environment variables
- **Secrets**: References AWS Secrets Manager for sensitive data

## 🔧 **Auth0 Configuration Flow**

### **Before (Single Audience)**
```
Terraform .tfvars → ECS Task Definition → Container Environment
AWS Secrets Manager → AUTH0_AUDIENCE (single audience)
```

### **After (Separate Audiences)**
```
Terraform .tfvars → ECS Task Definition → Container Environment
├── AUTH0_MANAGEMENT_API_AUDIENCE (from Terraform variable)
└── AUTH0_API_AUDIENCE (from Terraform variable)

AWS Secrets Manager → AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET
```

## 🚀 **Deployment Process**

### **1. Code Changes**
- Update application code (already done)
- Update Terraform configuration (done in this PR)

### **2. Terraform Apply**
```bash
# Staging
terraform apply -var-file=staging.tfvars

# Production
terraform apply -var-file=production.tfvars
```

### **3. ECS Update**
- Terraform updates ECS Task Definition
- ECS automatically deploys new configuration
- No manual intervention needed

## 📋 **What You Need to Do**

### **1. Update Your Auth0 Secrets**
The AWS Secrets Manager secrets no longer need the `audience` field. Update them to:

**Staging Secret (`auth0-fastapi-tme`):**
```json
{
  "client_id": "your-staging-client-id",
  "client_secret": "your-staging-client-secret",
  "domain": "trigpointing.eu.auth0.com"
}
```

**Production Secret (`auth0-fastapi-tuk`):**
```json
{
  "client_id": "your-production-client-id",
  "client_secret": "your-production-client-secret",
  "domain": "trigpointing.eu.auth0.com"
}
```

### **2. Deploy Infrastructure Changes**
```bash
# Deploy to staging
terraform apply -var-file=staging.tfvars

# Deploy to production
terraform apply -var-file=production.tfvars
```

### **3. Verify Configuration**
Check that your ECS tasks have the new environment variables:
- `AUTH0_MANAGEMENT_API_AUDIENCE=https://trigpointing.eu.auth0.com/api/v2/`
- `AUTH0_API_AUDIENCE=https://api.trigpointing.me/api/v1/` (staging)
- `AUTH0_API_AUDIENCE=https://api.trigpointing.uk/api/v1/` (production)

## 🔍 **Why This Approach?**

### **Advantages**
1. **Environment-Specific**: Different audiences for staging vs production
2. **Secure**: Sensitive data in AWS Secrets Manager
3. **Maintainable**: Clear separation of concerns
4. **Infrastructure as Code**: All configuration in version control

### **vs. env.example**
- `env.example` is only for local development
- Production uses Terraform + AWS Secrets Manager
- No overlap or confusion between environments

## 🛠️ **Local Development**

For local development, you can still use `env.example`:

```bash
# Copy example to actual env file
cp env.example .env

# Edit .env with your local values
# Run setup script
./scripts/setup.sh
```

But remember: this is **only for local development**. Staging and production use the Terraform configuration.

## ✅ **Summary**

- **`env.example`**: Local development only
- **`.tfvars` files**: Staging/production configuration
- **AWS Secrets Manager**: Sensitive data storage
- **ECS Task Definition**: Environment variable injection
- **No overlap**: Each environment uses its own configuration method
