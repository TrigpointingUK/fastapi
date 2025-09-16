#!/bin/bash

# Helper script to copy AWS credentials to bastion host
# This makes it easier to set up credentials for Terraform deployment

set -e

# Configuration
BASTION_IP="63.32.182.69"  # Update this with the current bastion IP
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/id_rsa}"  # Allow override via environment variable
BASTION_USER="ec2-user"

echo "🔐 Setting up AWS credentials on bastion host..."

# Check if SSH key exists
if [[ ! -f "${SSH_KEY_PATH/#\~/$HOME}" ]]; then
    echo "❌ SSH key not found at ${SSH_KEY_PATH}"
    echo "   Please set SSH_KEY_PATH environment variable or ensure ~/.ssh/id_rsa exists"
    exit 1
fi

# Check if AWS credentials exist locally
if [[ ! -f "${HOME}/.aws/credentials" ]]; then
    echo "❌ AWS credentials not found at ~/.aws/credentials"
    echo "   Please configure AWS CLI locally first: aws configure"
    exit 1
fi

# Create .aws directory on bastion
echo "📁 Creating .aws directory on bastion..."
ssh -i "${SSH_KEY_PATH}" "${BASTION_USER}@${BASTION_IP}" "mkdir -p ~/.aws"

# Copy credentials
echo "📋 Copying AWS credentials to bastion..."
scp -i "${SSH_KEY_PATH}" "${HOME}/.aws/credentials" "${BASTION_USER}@${BASTION_IP}:~/.aws/"

# Copy config if it exists
if [[ -f "${HOME}/.aws/config" ]]; then
    echo "📋 Copying AWS config to bastion..."
    scp -i "${SSH_KEY_PATH}" "${HOME}/.aws/config" "${BASTION_USER}@${BASTION_IP}:~/.aws/"
fi

# Test credentials on bastion
echo "🧪 Testing AWS credentials on bastion..."
if ssh -i "${SSH_KEY_PATH}" "${BASTION_USER}@${BASTION_IP}" "aws sts get-caller-identity" > /dev/null 2>&1; then
    echo "✅ AWS credentials configured successfully on bastion!"
    echo ""
    echo "💡 You can now run the MySQL Terraform deployment:"
    echo "   ./deploy.sh"
else
    echo "❌ AWS credentials test failed on bastion"
    echo "   Please check the credentials and try again"
    exit 1
fi
