variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "trigpointing"
}

# Note: terraform_state_bucket is hardcoded to "tuk-terraform-state" in eu-west-1

variable "container_image" {
  description = "Docker image for the application"
  type        = string
  default     = "ghcr.io/trigpointinguk/fastapi:main"
}

variable "cpu" {
  description = "CPU units for the ECS task"
  type        = number
  default     = 1024
}

variable "memory" {
  description = "Memory for the ECS task"
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Desired number of tasks in the ECS service"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum number of tasks for auto scaling"
  type        = number
  default     = 2
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

variable "enable_cloudflare_ssl" {
  description = "Enable HTTPS with CloudFlare origin certificate"
  type        = bool
  default     = true
}

variable "cloudflare_origin_cert" {
  description = "CloudFlare origin certificate (PEM format)"
  type        = string
  default     = null
  sensitive   = true
}

variable "cloudflare_origin_key" {
  description = "CloudFlare origin certificate private key"
  type        = string
  default     = null
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = "api.trigpointing.uk"
}

# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain (e.g., your-tenant.auth0.com)"
  type        = string
  default     = "trigpointing.eu.auth0.com"
}

variable "auth0_connection" {
  description = "Auth0 connection name for user database"
  type        = string
  default     = "tuk-users"
}

variable "auth0_api_audience" {
  description = "Auth0 API audience for token validation"
  type        = string
  default     = "https://api.trigpointing.uk/api/v1/"
}
