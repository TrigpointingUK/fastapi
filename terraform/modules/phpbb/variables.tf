variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "cpu" {
  description = "Task CPU"
  type        = number
}

variable "memory" {
  description = "Task memory"
  type        = number
}

variable "desired_count" {
  description = "Desired tasks"
  type        = number
}

variable "min_capacity" {
  description = "Min tasks"
  type        = number
}

variable "max_capacity" {
  description = "Max tasks"
  type        = number
}

variable "cpu_target_value" {
  description = "CPU target"
  type        = number
}

variable "memory_target_value" {
  description = "Memory target"
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
  description = "Task exec role ARN"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "Task role ARN"
  type        = string
}

variable "ecs_security_group_id" {
  description = "ECS SG ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "image_uri" {
  description = "Docker image URI"
  type        = string
}

variable "db_credentials_arn" {
  description = "DB credentials secret ARN"
  type        = string
}

variable "phpbb_secrets_arn" {
  description = "phpBB app secrets ARN"
  type        = string
}

variable "db_host" {
  description = "DB host"
  type        = string
}

variable "db_name" {
  description = "DB name"
  type        = string
}

variable "db_user" {
  description = "DB user"
  type        = string
}

variable "table_prefix" {
  description = "phpBB table prefix"
  type        = string
  default     = "phpbb_"
}

variable "efs_file_system_id" {
  description = "EFS File System ID"
  type        = string
}

variable "efs_access_point_id" {
  description = "EFS Access Point ID"
  type        = string
}
