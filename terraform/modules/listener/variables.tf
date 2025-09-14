variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (staging/production)"
  type        = string
}

variable "alb_arn" {
  description = "ARN of the Application Load Balancer"
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
