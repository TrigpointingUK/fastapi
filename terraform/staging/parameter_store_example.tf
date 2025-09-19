# Example: How to enable Parameter Store configuration for ECS service
# This file shows how to add Parameter Store support to your existing ECS service

# Add these variables to your terraform.tfvars or pass them via command line
# enable_parameter_store = true
# xray_enabled = true
# xray_service_name = "trigpointing-api-staging"
# xray_sampling_rate = 0.2
# log_level = "DEBUG"
# cors_origins = "https://staging.trigpointing.uk,https://api-staging.trigpointing.uk"

# Then update your ECS service module call to include the new parameters:
/*
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
*/

# Add these variables to your staging/variables.tf:
/*
variable "enable_parameter_store" {
  description = "Enable AWS Systems Manager Parameter Store for configuration"
  type        = bool
  default     = false
}

variable "xray_enabled" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = false
}

variable "xray_service_name" {
  description = "X-Ray service name"
  type        = string
  default     = "trigpointing-api-staging"
}

variable "xray_sampling_rate" {
  description = "X-Ray sampling rate (0.0 to 1.0)"
  type        = number
  default     = 0.2
}

variable "xray_daemon_address" {
  description = "X-Ray daemon address (optional)"
  type        = string
  default     = null
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "DEBUG"
}

variable "cors_origins" {
  description = "CORS allowed origins (comma-separated)"
  type        = string
  default     = null
}

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
*/
