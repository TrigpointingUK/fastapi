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

# Note: All Auth0 configuration is stored in the secret and managed manually
# The secret includes: custom_domain, tenant_domain, SPA client ID, M2M client ID/secret, etc.
