variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., common, staging, production)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = number
}

variable "memory" {
  description = "Fargate task memory in MB"
  type        = number
}

variable "desired_count" {
  description = "Desired number of tasks"
  type        = number
}

variable "min_capacity" {
  description = "Minimum number of tasks for autoscaling"
  type        = number
}

variable "max_capacity" {
  description = "Maximum number of tasks for autoscaling"
  type        = number
}

variable "cpu_target_value" {
  description = "Target CPU utilisation percentage for autoscaling"
  type        = number
}

variable "memory_target_value" {
  description = "Target memory utilisation percentage for autoscaling"
  type        = number
}

variable "ecs_cluster_id" {
  description = "ECS cluster ID"
  type        = string
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of ECS task execution role"
  type        = string
}

variable "ecs_task_execution_role_name" {
  description = "Name of ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of ECS task role"
  type        = string
}

variable "ecs_task_role_name" {
  description = "Name of ECS task role"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "target_group_arn" {
  description = "ARN of target group for load balancer"
  type        = string
}

variable "cloudwatch_log_group_name" {
  description = "Name of CloudWatch log group"
  type        = string
}

variable "image_uri" {
  description = "Docker image URI for MediaWiki"
  type        = string
}

variable "mediawiki_db_credentials_arn" {
  description = "ARN of AWS Secrets Manager secret containing MediaWiki database credentials"
  type        = string
}

variable "mediawiki_app_secrets_arn" {
  description = "ARN of AWS Secrets Manager secret containing MediaWiki application secrets"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of S3 bucket for MediaWiki file uploads"
  type        = string
}

variable "cache_host" {
  description = "ElastiCache host endpoint"
  type        = string
}

variable "cache_port" {
  description = "ElastiCache port"
  type        = number
  default     = 6379
}
