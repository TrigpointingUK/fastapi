variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
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
