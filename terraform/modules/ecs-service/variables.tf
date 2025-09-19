variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "service_name" {
  description = "Name of the ECS service (defaults to project_name-environment if not specified)"
  type        = string
  default     = null
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "container_image" {
  description = "Docker image for the application"
  type        = string
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

variable "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecs_task_role_name" {
  description = "Name of the ECS task role (for policy attachment)"
  type        = string
}

variable "ecs_security_group_id" {
  description = "ID of the ECS security group"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "target_group_arn" {
  description = "ARN of the target group"
  type        = string
}

variable "alb_listener_arn" {
  description = "ARN of the ALB listener"
  type        = string
}

variable "alb_rule_priority" {
  description = "Priority for the ALB listener rule"
  type        = number
  default     = 100
}

variable "secrets_arn" {
  description = "ARN of the secrets manager secret"
  type        = string
}

variable "credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  type        = string
}

variable "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  type        = string
}

# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain (e.g., your-tenant.auth0.com)"
  type        = string
  default     = null
}

variable "auth0_connection" {
  description = "Auth0 connection name for user database"
  type        = string
  default     = "Username-Password-Authentication"
}

variable "auth0_api_audience" {
  description = "Auth0 API audience for token validation"
  type        = string
  default     = null
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
