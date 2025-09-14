#!/bin/bash

# MySQL Database Deployment Script
# This script should be run on the bastion host

set -e

echo "🚀 Starting MySQL database deployment..."

# Check if we're on the bastion host
if [[ ! -f /etc/amazon-linux-release ]]; then
    echo "❌ This script should be run on the bastion host (Amazon Linux)"
    echo "   Please SSH into the bastion and run this script there"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured"
    echo "   Please copy your ~/.aws/credentials to this bastion host"
    exit 1
fi

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init -backend-config=backend.conf

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan

# Apply the deployment
echo "🔧 Applying deployment..."
terraform apply -auto-approve

echo "✅ MySQL database deployment completed successfully!"
echo ""
echo "📊 Database schemas created:"
echo "   - Production: $(terraform output -raw production_schema_name)"
echo "   - Staging: $(terraform output -raw staging_schema_name)"
echo ""
echo "🔐 Credentials are stored in AWS Secrets Manager:"
echo "   - Admin: $(terraform output -raw admin_credentials_arn)"
echo "   - Production: $(terraform output -raw production_credentials_arn)"
echo "   - Staging: $(terraform output -raw staging_credentials_arn)"
echo "   - Backups: $(terraform output -raw backups_credentials_arn)"
