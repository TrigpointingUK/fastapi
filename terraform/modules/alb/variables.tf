variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "ID of the ALB security group"
  type        = string
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
  description = "Domain name for the certificate"
  type        = string
  default     = null
}
