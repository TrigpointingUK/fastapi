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

variable "enable_cloudflare_ssl" {
  description = "Enable HTTPS with CloudFlare origin certificate"
  type        = bool
  default     = true
}
