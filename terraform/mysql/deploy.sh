#!/bin/bash

# OBSOLETE: This script has been superseded by the main terraform/deploy.sh script
# Use: cd ../; ./deploy.sh mysql
#
# This file is kept for reference but should not be used for new deployments

echo "⚠️  This script is OBSOLETE!"
echo "   Please use the main deployment script instead:"
echo "   cd ../ && ./deploy.sh mysql"
echo ""
exit 1

# ===== OBSOLETE CODE BELOW - DO NOT USE =====

# MySQL Database Deployment Script
# This script can be run locally and will automatically deploy to the bastion host

set -e

# Configuration
BASTION_IP="63.32.182.69"  # Update this with the current bastion IP
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/trigpointing-bastion.pem}"  # Allow override via environment variable
BASTION_USER="ec2-user"
TERRAFORM_DIR="/home/ec2-user/mysql-terraform"

# Function definitions
function deploy_from_local() {
    # Expand tilde in SSH key path
    SSH_KEY_PATH_EXPANDED="${SSH_KEY_PATH/#\~/$HOME}"

    # Check if SSH key exists
    if [[ ! -f "${SSH_KEY_PATH_EXPANDED}" ]]; then
        echo "❌ SSH key not found at ${SSH_KEY_PATH_EXPANDED}"
        echo "   Please set SSH_KEY_PATH environment variable or ensure ~/.ssh/trigpointing-bastion.pem exists"
        exit 1
    fi

    # Check if we can connect to bastion
    echo "🔍 Testing connection to bastion host..."
    if ! ssh -i "${SSH_KEY_PATH_EXPANDED}" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "${BASTION_USER}@${BASTION_IP}" "echo 'Connection successful'" > /dev/null 2>&1; then
        echo "❌ Cannot connect to bastion host at ${BASTION_IP}"
        echo "   Please check:"
        echo "   - Bastion IP is correct"
        echo "   - SSH key path is correct: ${SSH_KEY_PATH_EXPANDED}"
        echo "   - SSH key has access to bastion"
        exit 1
    fi

    echo "📦 Copying Terraform files to bastion host..."

    # Create directory on bastion
    ssh -i "${SSH_KEY_PATH_EXPANDED}" "${BASTION_USER}@${BASTION_IP}" "mkdir -p ${TERRAFORM_DIR}"

    # Copy Terraform files (excluding .terraform directory)
    echo "   Excluding .terraform directory to avoid copying providers..."

    # Try rsync first (faster and more efficient)
    if command -v rsync > /dev/null 2>&1; then
        rsync -avz --exclude='.terraform/' --exclude='.terraform.lock.hcl' -e "ssh -i ${SSH_KEY_PATH_EXPANDED}" ./ "${BASTION_USER}@${BASTION_IP}:${TERRAFORM_DIR}/"
    else
        # Fallback to scp with tar for exclusions
        echo "   Using tar+scp fallback (rsync not available)..."
        tar --exclude='.terraform' --exclude='.terraform.lock.hcl' -czf - . | ssh -i "${SSH_KEY_PATH_EXPANDED}" "${BASTION_USER}@${BASTION_IP}" "cd ${TERRAFORM_DIR} && tar -xzf -"
    fi

    echo "🔧 Running deployment on bastion host..."

    # Execute the deployment script on bastion
    echo "🚀 Running MySQL Terraform on bastion host..."
    ssh -i "${SSH_KEY_PATH_EXPANDED}" "${BASTION_USER}@${BASTION_IP}" "cd ${TERRAFORM_DIR} && chmod +x deploy.sh && ./deploy.sh"

    echo "✅ Deployment completed successfully!"

}

function run_deployment_on_bastion() {
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
    echo "   - Production: $(terraform output -raw production_credentials_arn)"
    echo "   - Staging: $(terraform output -raw staging_credentials_arn)"
    echo "   - Backups: $(terraform output -raw backups_credentials_arn)"
    echo ""
    echo "💡 Note: Admin credentials are managed by RDS and available in common infrastructure"
}

# Main execution
echo "🚀 Starting MySQL database deployment..."

# Check if we're running locally or on bastion
if [[ -f /etc/amazon-linux-release ]]; then
    echo "📋 Running on bastion host - executing deployment..."
    run_deployment_on_bastion
else
    echo "📋 Running locally - copying files to bastion and executing remotely..."
    deploy_from_local
fi
