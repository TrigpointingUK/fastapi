#!/bin/bash

# MySQL Database Deployment Script for Bastion Host
# This script runs ON the bastion host to deploy MySQL databases

set -e

# Colour codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# Output formatting functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🚀 Starting MySQL database deployment on bastion host..."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS credentials not configured"
    print_error "Please copy your ~/.aws/credentials to this bastion host"
    exit 1
fi

# Initialize Terraform
print_status "Initializing Terraform..."
terraform init -backend-config=backend.conf

# Plan the deployment
print_status "Planning deployment..."
terraform plan

echo ""
print_warning "⚠️  CAUTION: You are about to modify MySQL database schemas and users"
print_warning "This will affect: database schemas, user accounts, and credentials"
echo ""

# Ask for confirmation
read -p "Do you want to apply the MySQL database changes? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply the deployment
    print_status "Applying deployment..."
    terraform apply -auto-approve
    print_success "MySQL database deployment completed successfully!"
else
    print_warning "MySQL deployment cancelled."
    exit 1
fi
echo ""
print_status "📊 Database schemas created:"
echo "   - Production: $(terraform output -raw production_schema_name)"
echo "   - Staging: $(terraform output -raw staging_schema_name)"
if terraform output -raw mediawiki_schema_name > /dev/null 2>&1; then
    echo "   - MediaWiki: $(terraform output -raw mediawiki_schema_name)"
fi
echo ""
print_status "🔐 Credentials are stored in AWS Secrets Manager:"
echo "   - Production: $(terraform output -raw production_credentials_arn)"
echo "   - Staging: $(terraform output -raw staging_credentials_arn)"
echo "   - Backups: $(terraform output -raw backups_credentials_arn)"
if terraform output -raw mediawiki_credentials_arn > /dev/null 2>&1; then
    echo "   - MediaWiki: $(terraform output -raw mediawiki_credentials_arn)"
fi
echo ""
print_status "💡 Note: Admin credentials are managed by RDS and available in common infrastructure"
