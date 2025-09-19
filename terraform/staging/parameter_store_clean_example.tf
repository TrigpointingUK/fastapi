# Clean Parameter Store Configuration Example
# This shows how to use the new object-based approach

# Add this variable to your terraform/staging/variables.tf:
/*
variable "parameter_store_config" {
  description = "Parameter Store configuration for the application"
  type = object({
    enabled = optional(bool, false)
    parameters = optional(object({
      xray = optional(object({
        enabled        = optional(bool, false)
        service_name   = optional(string, "trigpointing-api")
        sampling_rate  = optional(number, 0.1)
        daemon_address = optional(string, null)
      }), {})
      app = optional(object({
        log_level    = optional(string, "INFO")
        cors_origins = optional(string, null)
      }), {})
      database = optional(object({
        pool_size    = optional(number, 5)
        pool_recycle = optional(number, 300)
      }), {})
    }), {})
  })
  default = {}
}
*/

# Add this to your terraform/staging/terraform.tfvars:
/*
# Enable Parameter Store
parameter_store_config = {
  enabled = true
  parameters = {
    xray = {
      enabled        = true
      service_name   = "trigpointing-api-staging"
      sampling_rate  = 0.2
      daemon_address = null
    }
    app = {
      log_level    = "DEBUG"
      cors_origins = "https://staging.trigpointing.uk,https://api-staging.trigpointing.uk"
    }
    database = {
      pool_size    = 5
      pool_recycle = 300
    }
  }
}
*/

# Update your ECS service module call in terraform/staging/main.tf:
/*
module "ecs_service" {
  source = "../modules/ecs-service"

  # ... existing parameters ...

  # Add the new parameter store configuration
  parameter_store_config = var.parameter_store_config
}
*/

# The module will automatically create these Parameter Store parameters:
# /trigpointing/staging/xray/enabled = "true"
# /trigpointing/staging/xray/service_name = "trigpointing-api-staging"
# /trigpointing/staging/xray/sampling_rate = "0.2"
# /trigpointing/staging/app/log_level = "DEBUG"
# /trigpointing/staging/app/cors_origins = "https://staging.trigpointing.uk,https://api-staging.trigpointing.uk"
# /trigpointing/staging/database/pool_size = "5"
# /trigpointing/staging/database/pool_recycle = "300"

# And these environment variables will be available in your ECS container:
# XRAY_ENABLED = "true"
# XRAY_SERVICE_NAME = "trigpointing-api-staging"
# XRAY_SAMPLING_RATE = "0.2"
# APP_LOG_LEVEL = "DEBUG"
# APP_CORS_ORIGINS = "https://staging.trigpointing.uk,https://api-staging.trigpointing.uk"
# DATABASE_POOL_SIZE = "5"
# DATABASE_POOL_RECYCLE = "300"
