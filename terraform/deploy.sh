#!/bin/bash

# FastAPI Terraform Deployment Script
# This script helps deploy the consolidated infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if terraform is installed
check_terraform() {
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform first."
        exit 1
    fi
    print_success "Terraform is installed: $(terraform version -json | jq -r '.terraform_version')"
}

# Function to check if AWS CLI is configured
check_aws() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi

    print_success "AWS CLI is configured: $(aws sts get-caller-identity --query 'Account' --output text)"
}

# Function to deploy common infrastructure
deploy_common() {
    print_status "Deploying common infrastructure..."

    cd common

    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init -backend-config=backend.conf

    # Plan deployment
    print_status "Planning deployment..."
    terraform plan

    # Ask for confirmation
    read -p "Do you want to apply the common infrastructure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply -auto-approve
        print_success "Common infrastructure deployed successfully!"

        # Note: Using existing tuk-terraform-state bucket in eu-west-1
        print_status "Using existing tuk-terraform-state bucket in eu-west-1"
    else
        print_warning "Common infrastructure deployment cancelled."
        exit 1
    fi

    cd ..
}

# Function to deploy staging
deploy_staging() {
    print_status "Deploying staging environment..."

    cd staging

    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init -backend-config=backend.conf

    # Check if certificate file exists
    if [ ! -f "cloudflare-cert.tfvars" ]; then
        print_error "cloudflare-cert.tfvars not found in staging directory!"
        print_error "Please ensure the CloudFlare certificate file exists."
        exit 1
    fi

    # Plan deployment
    print_status "Planning deployment..."
    terraform plan -var-file=terraform.tfvars -var-file=cloudflare-cert.tfvars

    # Ask for confirmation
    read -p "Do you want to apply the staging infrastructure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply -auto-approve -var-file=terraform.tfvars -var-file=cloudflare-cert.tfvars
        print_success "Staging infrastructure deployed successfully!"

        # Show outputs
        print_status "Staging outputs:"
        terraform output
    else
        print_warning "Staging infrastructure deployment cancelled."
    fi

    cd ..
}

# Function to deploy production
deploy_production() {
    print_status "Deploying production environment..."

    cd production

    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init -backend-config=backend.conf

    # Check if certificate file exists
    if [ ! -f "cloudflare-cert.tfvars" ]; then
        print_error "cloudflare-cert.tfvars not found in production directory!"
        print_error "Please ensure the CloudFlare certificate file exists."
        exit 1
    fi

    # Plan deployment
    print_status "Planning deployment..."
    terraform plan -var-file=terraform.tfvars -var-file=cloudflare-cert.tfvars

    # Ask for confirmation
    read -p "Do you want to apply the production infrastructure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply -auto-approve -var-file=terraform.tfvars -var-file=cloudflare-cert.tfvars
        print_success "Production infrastructure deployed successfully!"

        # Show outputs
        print_status "Production outputs:"
        terraform output
    else
        print_warning "Production infrastructure deployment cancelled."
    fi

    cd ..
}

# Function to show status
show_status() {
    print_status "Infrastructure Status:"
    echo

    # Check common infrastructure
    if [ -d "common" ] && [ -f "common/terraform.tfstate" ]; then
        print_success "Common infrastructure: Deployed"
        cd common
        echo "  State bucket: tuk-terraform-state (eu-west-1)"
        echo "  VPC ID: $(terraform output -raw vpc_id 2>/dev/null || echo 'Not available')"
        echo "  Bastion IP: $(terraform output -raw bastion_public_ip 2>/dev/null || echo 'Not available')"
        cd ..
    else
        print_warning "Common infrastructure: Not deployed"
    fi

    # Check staging
    if [ -d "staging" ] && [ -f "staging/terraform.tfstate" ]; then
        print_success "Staging environment: Deployed"
        cd staging
        echo "  ALB DNS: $(terraform output -raw alb_dns_name 2>/dev/null || echo 'Not available')"
        cd ..
    else
        print_warning "Staging environment: Not deployed"
    fi

    # Check production
    if [ -d "production" ] && [ -f "production/terraform.tfstate" ]; then
        print_success "Production environment: Deployed"
        cd production
        echo "  ALB DNS: $(terraform output -raw alb_dns_name 2>/dev/null || echo 'Not available')"
        cd ..
    else
        print_warning "Production environment: Not deployed"
    fi
}

# Main script
main() {
    echo "FastAPI Terraform Deployment Script"
    echo "==================================="
    echo

    # Check prerequisites
    check_terraform
    check_aws
    echo

    # Parse command line arguments
    case "${1:-}" in
        "common")
            deploy_common
            ;;
        "staging")
            deploy_staging
            ;;
        "production")
            deploy_production
            ;;
        "all")
            deploy_common
            echo
            deploy_staging
            echo
            deploy_production
            ;;
        "status")
            show_status
            ;;
        *)
            echo "Usage: $0 {common|staging|production|all|status}"
            echo
            echo "Commands:"
            echo "  common     - Deploy common infrastructure (VPC, ECS, RDS, etc.)"
            echo "  staging    - Deploy staging environment"
            echo "  production - Deploy production environment"
            echo "  all        - Deploy all infrastructure in order"
            echo "  status     - Show current deployment status"
            echo
            echo "Deployment order:"
            echo "  1. common (first time only)"
            echo "  2. staging"
            echo "  3. production"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
