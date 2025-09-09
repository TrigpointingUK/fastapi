variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "fastapi"
}

variable "container_image" {
  description = "Docker image for the application"
  type        = string
}

variable "db_schema" {
  description = "Database schema name (legacy: trigpoin_trigs)"
  type        = string
  default     = "trigpoin_trigs"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
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

variable "admin_ip_address" {
  description = "IP address allowed to connect directly to RDS (for admin access)"
  type        = string
  default     = null
}

variable "key_pair_name" {
  description = "AWS key pair name for bastion host access"
  type        = string
  default     = null
}

variable "enable_dms_access" {
  description = "Enable DMS replication instance access to RDS"
  type        = bool
  default     = false
}

variable "dms_replication_instance_sg_id" {
  description = "Security group ID of DMS replication instance (if known)"
  type        = string
  default     = null
}

variable "dms_cidr_block" {
  description = "CIDR block for DMS replication instance (if in different VPC)"
  type        = string
  default     = null
}

variable "dms_instance_ip" {
  description = "Specific IP address of DMS replication instance"
  type        = string
  default     = null
}

# CloudFlare SSL Configuration
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

variable "enable_cloudflare_ssl" {
  description = "Enable HTTPS with CloudFlare origin certificate (REQUIRED for security - no HTTP listener)"
  type        = bool
  default     = true  # Required for production security
}

variable "domain_name" {
  description = "Domain name for the API (e.g., fastapi.trigpointing.me)"
  type        = string
  default     = null
}

variable "use_external_database" {
  description = "Use external database instead of provisioning RDS (for production with existing MySQL 5.5)"
  type        = bool
  default     = false
}


# Auth0 Configuration
variable "auth0_domain" {
  description = "Auth0 domain (e.g., your-tenant.auth0.com)"
  type        = string
  default     = null
}


variable "auth0_connection" {
  description = "Auth0 connection name for user database (e.g., tme-users, Username-Password-Authentication)"
  type        = string
  default     = "Username-Password-Authentication"
}

variable "auth0_api_audience" {
  description = "Auth0 API audience for token validation (e.g., https://api.yourdomain.com/api/v1/)"
  type        = string
  default     = null
}
