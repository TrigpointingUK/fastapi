# FastAPI Terraform Infrastructure

This directory contains the consolidated Terraform infrastructure for the FastAPI project, now located in the Ireland (eu-west-1) region.

## Architecture

The infrastructure is organized into four main directories:

- **`common/`** - Shared infrastructure (VPC, ECS cluster, RDS, bastion, webserver)
- **`modules/`** - Reusable Terraform modules
- **`staging/`** - Staging environment configuration
- **`production/`** - Production environment configuration

## Key Changes from Previous Architecture

1. **Consolidated Infrastructure**: Both staging and production now share the same VPC, ECS cluster, and RDS instance
2. **Ireland Region**: Moved from Oregon (us-west-2) to Ireland (eu-west-1) for better UK performance
3. **Modular Design**: Reusable modules for ECS services, secrets, CloudFlare, and ALB
4. **Remote State**: Common infrastructure state is referenced by environment-specific configurations
5. **Shared State Storage**: Uses existing S3 bucket in Ireland (eu-west-1) for state storage

## Directory Structure

```
terraform/
├── common/                 # Shared infrastructure
│   ├── main.tf            # Provider, S3 state bucket, DynamoDB lock table
│   ├── vpc.tf             # VPC, subnets, NAT gateways, routing
│   ├── ecs.tf             # ECS cluster and IAM roles
│   ├── rds.tf             # RDS instance and parameter groups
│   ├── bastion.tf         # Bastion host for database access
│   ├── webserver.tf       # Web server in private subnet
│   ├── security.tf        # Security groups
│   ├── outputs.tf         # Outputs for remote state
│   └── backend.conf       # S3 backend configuration
├── modules/               # Reusable modules
│   ├── ecs-service/       # ECS service with auto-scaling
│   ├── secrets/           # AWS Secrets Manager
│   ├── cloudflare/        # CloudFlare SSL and security groups
│   └── alb/               # Application Load Balancer
├── staging/               # Staging environment
│   ├── main.tf            # Staging configuration using modules
│   ├── variables.tf       # Staging variables
│   ├── outputs.tf         # Staging outputs
│   ├── backend.conf       # S3 backend configuration
│   └── terraform.tfvars   # Staging values
└── production/            # Production environment
    ├── main.tf            # Production configuration using modules
    ├── variables.tf       # Production variables
    ├── outputs.tf         # Production outputs
    ├── backend.conf       # S3 backend configuration
    └── terraform.tfvars   # Production values
```

## Deployment Order

1. **Common Infrastructure** (first time only):
   ```bash
   cd common
   terraform init -backend-config=backend.conf
   terraform plan
   terraform apply
   ```

2. **Update State Bucket References**:
   After common infrastructure is created, update the `terraform_state_bucket` variable in both staging and production `terraform.tfvars` files with the actual bucket name from the common outputs.

3. **Staging Environment**:
   ```bash
   cd staging
   terraform init -backend-config=backend.conf
   terraform plan
   terraform apply
   ```

4. **Production Environment**:
   ```bash
   cd production
   terraform init -backend-config=backend.conf
   terraform plan
   terraform apply
   ```

## Key Features

### Security
- CloudFlare origin certificates for HTTPS
- Security groups restricting access to CloudFlare IPs only
- Bastion host for secure database access
- Private subnets for application servers

### High Availability
- Multi-AZ deployment
- Auto-scaling groups for ECS services
- Load balancer with health checks

### Monitoring
- CloudWatch logs for application logs
- RDS enhanced monitoring
- Container insights enabled

### Cost Optimization
- Shared infrastructure reduces costs
- Appropriate instance sizes for each environment
- Auto-scaling based on CPU and memory usage

## Environment-Specific Configuration

### Staging
- Smaller instance sizes (512 CPU, 1024 memory)
- 1-3 tasks auto-scaling
- 7-day log retention
- Domain: `api.trigpointing.me`

### Production
- Larger instance sizes (1024 CPU, 2048 memory)
- 2-10 tasks auto-scaling
- 30-day log retention
- Domain: `api.trigpointing.uk`

## Secrets Management

Application secrets are stored in AWS Secrets Manager and include:
- JWT secret key
- Database connection URL
- Auth0 client credentials (if enabled)

Secrets are automatically injected into ECS tasks as environment variables.

## Database Access

- **Bastion Host**: SSH access from admin IP for database administration
- **Web Server**: Private instance for application deployment and testing
- **ECS Tasks**: Direct access to RDS from private subnets

## Migration from Old Infrastructure

1. Keep `terraform-old/` directory until migration is complete
2. Deploy new infrastructure alongside existing
3. Update DNS records to point to new ALB
4. Verify application functionality
5. Decommission old infrastructure

## Troubleshooting

### Common Issues

1. **State Bucket Not Found**: Ensure common infrastructure is deployed first
2. **CloudFlare Certificate Issues**: Verify certificate and key are properly formatted
3. **Database Connection**: Check security groups and RDS endpoint
4. **ALB Health Checks**: Verify application health endpoint is responding

### Useful Commands

```bash
# View common infrastructure outputs
cd common && terraform output

# Check ECS service status
aws ecs describe-services --cluster trigpointing-cluster --services fastapi-staging-service

# View application logs
aws logs tail /ecs/fastapi-staging --follow

# Connect to bastion host
ssh -i your-key.pem ec2-user@<bastion-public-ip>
```
