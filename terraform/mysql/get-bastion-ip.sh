#!/bin/bash

# Helper script to get the current bastion IP from Terraform state
# This can be used to update the deploy.sh script automatically

set -e

echo "🔍 Getting bastion IP from Terraform state..."

# Check if we're in the common terraform directory
if [[ ! -f "terraform.tfstate" ]] && [[ ! -f "../common/terraform.tfstate" ]]; then
    echo "❌ Terraform state not found"
    echo "   Please run this from the terraform/common directory or ensure terraform state is available"
    exit 1
fi

# Get bastion IP from terraform state
if [[ -f "terraform.tfstate" ]]; then
    BASTION_IP=$(terraform output -raw bastion_public_ip 2>/dev/null || echo "")
elif [[ -f "../common/terraform.tfstate" ]]; then
    BASTION_IP=$(cd ../common && terraform output -raw bastion_public_ip 2>/dev/null || echo "")
fi

if [[ -z "$BASTION_IP" ]]; then
    echo "❌ Could not retrieve bastion IP from Terraform state"
    echo "   Please ensure the common infrastructure has been applied"
    exit 1
fi

echo "✅ Bastion IP: $BASTION_IP"

# Update deploy.sh if it exists
if [[ -f "deploy.sh" ]]; then
    echo "📝 Updating deploy.sh with current bastion IP..."
    sed -i "s/BASTION_IP=\"[^\"]*\"/BASTION_IP=\"$BASTION_IP\"/" deploy.sh
    echo "✅ deploy.sh updated with bastion IP: $BASTION_IP"
else
    echo "💡 To use this IP in deploy.sh, set:"
    echo "   BASTION_IP=\"$BASTION_IP\""
fi
