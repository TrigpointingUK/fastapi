#!/bin/bash

# MySQL Database Deployment Script for Bastion Host
# This script runs ON the bastion host to deploy MySQL databases

set -e

echo "🚀 Starting MySQL database deployment on bastion host..."

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

# Ask for confirmation
read -p "Do you want to apply the MySQL database changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply the deployment
    echo "🔧 Applying deployment..."
    terraform apply -auto-approve
else
    echo "❌ MySQL deployment cancelled."
    exit 1
fi

echo "✅ MySQL database deployment completed successfully!"
echo ""
echo "📊 Database schemas created:"
echo "   - Production: $(terraform output -raw production_schema_name)"
echo "   - Staging: $(terraform output -raw staging_schema_name)"
echo ""
echo "🔐 Credentials are stored in AWS Secrets Manager:"
echo "   - Production: $(terraform output -raw production_credentials_arn)"
echo "   - Staging: $(terraform output -raw staging_credentials_arn)"
echo "   - Backups: $(terraform output -raw backups_credentials_arn)"
echo ""
echo "💡 Note: Admin credentials are managed by RDS and available in common infrastructure"
