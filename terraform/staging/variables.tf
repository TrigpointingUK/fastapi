variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "trigpointing"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "container_image" {
  description = "Docker image for the application"
  type        = string
  default     = "534526983272.dkr.ecr.eu-west-1.amazonaws.com/trigpointing-staging:latest"
}

variable "cpu" {
  description = "CPU units for the ECS task"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Memory for the ECS task"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of tasks in the ECS service"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum number of tasks for auto scaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks for auto scaling"
  type        = number
  default     = 10
}

variable "cpu_target_value" {
  description = "Target CPU utilization for auto scaling"
  type        = number
  default     = 70
}

variable "memory_target_value" {
  description = "Target memory utilization for auto scaling"
  type        = number
  default     = 80
}

# Domain Configuration
variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = "api-staging.trigpointing.uk"
}

variable "enable_cloudflare_ssl" {
  description = "Enable Cloudflare SSL termination"
  type        = bool
  default     = false
}

# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain (e.g., your-tenant.auth0.com)"
  type        = string
  default     = "trigpointing.auth0.com"
}

variable "auth0_connection" {
  description = "Auth0 connection name for user database"
  type        = string
  default     = "Username-Password-Authentication"
}

variable "auth0_api_audience" {
  description = "Auth0 API audience for token validation"
  type        = string
  default     = "https://api.trigpointing.me/api/v1/"
}

# Parameter Store Configuration - Clean Object-Based Approach
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
