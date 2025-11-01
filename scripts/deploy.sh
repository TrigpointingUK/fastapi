#!/bin/bash

# Deployment script for Platform API
set -e

ENVIRONMENT=${1:-staging}
TERRAFORM_DIR="terraform"

echo "🚀 Deploying to $ENVIRONMENT environment..."

# Validate environment
if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is required but not installed."
        exit 1
    fi
}

echo "🔍 Checking required tools..."
check_tool terraform
check_tool aws
check_tool docker

# Check AWS credentials
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured or invalid."
    echo "Run 'aws configure' to set up your credentials."
    exit 1
fi

# Build and push Docker image
echo "🐳 Building Docker image..."
docker build -t platform-api .

# Tag and push to registry (adjust for your registry)
if [ "$ENVIRONMENT" = "production" ]; then
    IMAGE_TAG="ghcr.io/your-username/platform/api:main"
else
    IMAGE_TAG="ghcr.io/your-username/platform/api:develop"
fi

echo "🐳 Tagging image as $IMAGE_TAG..."
docker tag platform-api $IMAGE_TAG

echo "🐳 Pushing image to registry..."
docker push $IMAGE_TAG

# Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure..."
cd $TERRAFORM_DIR

# Initialize if needed
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
fi

# Plan deployment
echo "📋 Planning Terraform deployment..."
terraform plan -var-file="${ENVIRONMENT}.tfvars" -var="container_image=${IMAGE_TAG}"

# Ask for confirmation if production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "⚠️  You are about to deploy to PRODUCTION!"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "❌ Deployment cancelled."
        exit 1
    fi
fi

# Apply changes
echo "🚀 Applying Terraform changes..."
terraform apply -auto-approve -var-file="${ENVIRONMENT}.tfvars" -var="container_image=${IMAGE_TAG}"

# Get load balancer URL
ALB_DNS=$(terraform output -raw alb_dns_name)

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application URL: http://$ALB_DNS"
echo "📊 Health check: http://$ALB_DNS/health"
echo "📖 API docs: http://$ALB_DNS/docs"
echo ""

if [ "$ENVIRONMENT" = "staging" ]; then
    echo "💡 Test the deployment before promoting to production"
fi

echo "📊 You can monitor the deployment in the AWS Console:"
echo "   - ECS: https://console.aws.amazon.com/ecs/"
echo "   - RDS: https://console.aws.amazon.com/rds/"
echo "   - CloudWatch: https://console.aws.amazon.com/cloudwatch/"
