# AWS Systems Manager Parameter Store Integration

This document explains how to use AWS Systems Manager Parameter Store for managing application configuration in your ECS service.

## Overview

The ECS service module now supports a third group of configuration parameters sourced from AWS Systems Manager Parameter Store. This provides a clean separation between:

1. **Environment Variables**: Static configuration (JWT algorithm, ports, etc.)
2. **Secrets Manager**: Sensitive data (passwords, API keys, etc.)
3. **Parameter Store**: Application configuration (X-Ray settings, log levels, etc.)

## Benefits

- **Centralized Configuration**: Manage app config in one place
- **Environment-Specific**: Different values per environment
- **Version Control**: Track configuration changes
- **Cost-Effective**: Much cheaper than Secrets Manager for non-sensitive data
- **Easy Updates**: Change config without redeploying containers

## Configuration Parameters

### X-Ray Configuration
- `XRAY_ENABLED`: Enable/disable X-Ray tracing
- `XRAY_SERVICE_NAME`: Service name for X-Ray traces
- `XRAY_SAMPLING_RATE`: Sampling rate (0.0 to 1.0)
- `XRAY_DAEMON_ADDRESS`: Optional daemon address

### Application Configuration
- `LOG_LEVEL`: Application log level (DEBUG, INFO, WARNING, ERROR)
- `BACKEND_CORS_ORIGINS`: CORS allowed origins (comma-separated)

### Database Configuration
- `DB_POOL_SIZE`: Connection pool size
- `DB_POOL_RECYCLE`: Connection pool recycle time (seconds)

## Setup Instructions

### 1. Add Variables to Your Environment

Add these variables to your `terraform/staging/variables.tf` or `terraform/production/variables.tf`:

```hcl
# Parameter Store Configuration
variable "enable_parameter_store" {
  description = "Enable AWS Systems Manager Parameter Store for configuration"
  type        = bool
  default     = false
}

# X-Ray Configuration
variable "xray_enabled" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = false
}

variable "xray_service_name" {
  description = "X-Ray service name"
  type        = string
  default     = "trigpointing-api"
}

variable "xray_sampling_rate" {
  description = "X-Ray sampling rate (0.0 to 1.0)"
  type        = number
  default     = 0.1
}

variable "xray_daemon_address" {
  description = "X-Ray daemon address (optional)"
  type        = string
  default     = null
}

# Application Configuration
variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "cors_origins" {
  description = "CORS allowed origins (comma-separated)"
  type        = string
  default     = null
}

# Database Configuration
variable "db_pool_size" {
  description = "Database connection pool size"
  type        = number
  default     = 5
}

variable "db_pool_recycle" {
  description = "Database connection pool recycle time (seconds)"
  type        = number
  default     = 300
}
```

### 2. Update ECS Service Module Call

Update your ECS service module call in `terraform/staging/main.tf` or `terraform/production/main.tf`:

```hcl
module "ecs_service" {
  source = "../modules/ecs-service"

  # ... existing parameters ...

  # Add these new parameters for Parameter Store support
  enable_parameter_store = var.enable_parameter_store
  ecs_task_role_name     = data.terraform_remote_state.common.outputs.ecs_task_role_name

  # X-Ray Configuration
  xray_enabled        = var.xray_enabled
  xray_service_name   = var.xray_service_name
  xray_sampling_rate  = var.xray_sampling_rate
  xray_daemon_address = var.xray_daemon_address

  # Application Configuration
  log_level     = var.log_level
  cors_origins  = var.cors_origins

  # Database Configuration
  db_pool_size    = var.db_pool_size
  db_pool_recycle = var.db_pool_recycle
}
```

### 3. Set Values in terraform.tfvars

Add these values to your `terraform/staging/terraform.tfvars` or `terraform/production/terraform.tfvars`:

```hcl
# Enable Parameter Store
enable_parameter_store = true

# X-Ray Configuration
xray_enabled        = true
xray_service_name   = "trigpointing-api-staging"  # or "trigpointing-api" for production
xray_sampling_rate  = 0.2  # 20% sampling for staging, 0.1 for production
xray_daemon_address = null  # Optional

# Application Configuration
log_level    = "DEBUG"  # DEBUG for staging, INFO for production
cors_origins = "https://staging.trigpointing.uk,https://api-staging.trigpointing.uk"

# Database Configuration
db_pool_size    = 5
db_pool_recycle = 300
```

### 4. Deploy the Changes

```bash
cd terraform/staging
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Parameter Store Structure

Parameters are stored with the following hierarchy:

```
/trigpointing/staging/xray/enabled
/trigpointing/staging/xray/service_name
/trigpointing/staging/xray/sampling_rate
/trigpointing/staging/xray/daemon_address
/trigpointing/staging/app/log_level
/trigpointing/staging/app/cors_origins
/trigpointing/staging/database/pool_size
/trigpointing/staging/database/pool_recycle
```

## Viewing Parameters

You can view the created parameters in the AWS Console:

1. Go to AWS Systems Manager
2. Navigate to Parameter Store
3. Look for parameters under `/trigpointing/staging/` or `/trigpointing/production/`

Or via AWS CLI:

```bash
# List all parameters for staging
aws ssm get-parameters-by-path --path "/trigpointing/staging/" --recursive

# Get a specific parameter
aws ssm get-parameter --name "/trigpointing/staging/xray/enabled"
```

## Updating Parameters

You can update parameters in several ways:

### 1. Via Terraform (Recommended)
Change the values in your `terraform.tfvars` and run `terraform apply`.

### 2. Via AWS Console
1. Go to Parameter Store in AWS Console
2. Select the parameter
3. Click "Edit"
4. Update the value
5. The ECS service will pick up the new value on the next deployment

### 3. Via AWS CLI
```bash
aws ssm put-parameter --name "/trigpointing/staging/xray/sampling_rate" --value "0.5" --overwrite
```

## Cost Considerations

Parameter Store pricing (as of 2024):
- **Standard parameters**: $0.05 per 10,000 requests
- **Advanced parameters**: $0.05 per 10,000 requests + $0.05 per parameter per month

For typical usage, this is much cheaper than Secrets Manager ($0.40 per secret per month).

## Security

- Parameters are encrypted at rest using AWS KMS
- Access is controlled via IAM policies
- Parameters are not logged in CloudTrail by default
- Use Advanced parameters for sensitive data if needed

## Troubleshooting

### Parameter Not Found
If you see "Parameter not found" errors:
1. Check that `enable_parameter_store = true`
2. Verify the parameter exists in Parameter Store
3. Check IAM permissions for the ECS task role

### Parameter Not Updating
If parameter changes aren't reflected:
1. ECS tasks cache parameters at startup
2. Redeploy the ECS service to pick up new values
3. Or restart the ECS tasks

### IAM Permission Issues
Ensure the ECS task role has these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:region:account:parameter/trigpointing/environment/*"
    }
  ]
}
```

## Migration from Environment Variables

To migrate existing environment variables to Parameter Store:

1. **Identify candidates**: Look for variables that change between environments
2. **Add to Parameter Store**: Create the parameters via Terraform
3. **Update application**: Modify your app to read from Parameter Store
4. **Test thoroughly**: Ensure the application works with Parameter Store
5. **Remove old variables**: Clean up the old environment variables

## Best Practices

1. **Use meaningful names**: Make parameter names self-documenting
2. **Group related parameters**: Use hierarchical naming
3. **Document parameters**: Add descriptions in Terraform
4. **Version control**: Track parameter changes in Git
5. **Test changes**: Always test parameter changes in staging first
6. **Monitor costs**: Keep an eye on Parameter Store usage
7. **Use tags**: Tag parameters for better organization
