variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "database_url" {
  description = "Database connection URL"
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
