#!/bin/bash

# Script to connect to RDS master user using the managed secret
# This script should be run on the bastion host

set -e

AWS_REGION="eu-west-1"

echo "================================================"
echo "FastAPI RDS Master Database Connection"
echo "================================================"

# Get the master user secret ARN from Terraform state
echo "🔍 Getting RDS master user secret ARN from Terraform state..."

# Try to get the secret ARN from common terraform state
if [[ -f "/home/ec2-user/common-terraform/terraform.tfstate" ]]; then
    MASTER_SECRET=$(cd /home/ec2-user/common-terraform && terraform output -raw master_user_secret_arn 2>/dev/null || echo "")
elif [[ -f "/home/ec2-user/terraform/common/terraform.tfstate" ]]; then
    MASTER_SECRET=$(cd /home/ec2-user/terraform/common && terraform output -raw master_user_secret_arn 2>/dev/null || echo "")
else
    echo "❌ Could not find Terraform state file"
    echo "   Please ensure the common infrastructure has been applied"
    exit 1
fi

if [[ -z "$MASTER_SECRET" ]]; then
    echo "❌ Could not retrieve master user secret ARN from Terraform state"
    echo "   Please ensure the common infrastructure has been applied"
    exit 1
fi

echo "✅ Using master secret: ${MASTER_SECRET:0:50}..."

# Retrieve credentials from Secrets Manager
echo "🔐 Retrieving master credentials from AWS Secrets Manager..."
MASTER_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$MASTER_SECRET" \
  --region "$AWS_REGION" \
  --query SecretString \
  --output text)

if [[ $? -ne 0 ]]; then
    echo "❌ Failed to retrieve master credentials from AWS Secrets Manager"
    echo "   Make sure AWS CLI is configured and you have permissions to access the secret"
    exit 1
fi

# Parse master credentials from JSON
DB_HOST=$(echo "$MASTER_JSON" | jq -r '.host' | cut -d: -f1)
DB_PORT=$(echo "$MASTER_JSON" | jq -r '.port')
DB_USER=$(echo "$MASTER_JSON" | jq -r '.username')
DB_PASS=$(echo "$MASTER_JSON" | jq -r '.password')
DB_NAME=$(echo "$MASTER_JSON" | jq -r '.dbname')

echo "📊 Master connection details:"
echo "   Host: $DB_HOST"
echo "   Port: $DB_PORT"
echo "   Username: $DB_USER"
echo "   Database: $DB_NAME"
echo ""
echo "🔌 Connecting to database as master user..."
echo "================================================"

# Connect to database as master user
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"
