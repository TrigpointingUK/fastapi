variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}


variable "ecs_task_role_name" {
  description = "Name of the ECS task role"
  type        = string
}

variable "ecs_task_execution_role_name" {
  description = "Name of the ECS task execution role"
  type        = string
}

# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain (e.g., your-tenant.auth0.com)"
  type        = string
  default     = null
}

# Note: SPA and M2M client IDs are stored in this module's secret
# The M2M client secret should be stored as a separate key in the same secret
