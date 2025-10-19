# Auth0 Module Variables

variable "environment" {
  description = "Environment name (staging or production)"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "name_prefix" {
  description = "Prefix for Auth0 resource names (e.g., tme, tuk)"
  type        = string
}

variable "auth0_custom_domain" {
  description = "Auth0 custom domain for user-facing authentication (e.g., auth.trigpointing.me)"
  type        = string
}

variable "cloudflare_zone_name" {
  description = "Cloudflare zone name for DNS records (e.g., trigpointing.me)"
  type        = string
}

variable "database_connection_name" {
  description = "Name of the Auth0 database connection"
  type        = string
}

variable "api_name" {
  description = "Name of the API resource server"
  type        = string
}

variable "api_identifier" {
  description = "API identifier (audience)"
  type        = string
}

variable "fastapi_url" {
  description = "FastAPI base URL for webhook"
  type        = string
}

variable "m2m_token" {
  description = "M2M token for post-registration Action webhook authentication"
  type        = string
  sensitive   = true
}

variable "swagger_callback_urls" {
  description = "List of Swagger OAuth2 callback URLs"
  type        = list(string)
  default     = []
}

variable "swagger_allowed_origins" {
  description = "List of allowed origins for Swagger UI"
  type        = list(string)
  default     = []
}

variable "web_app_callback_urls" {
  description = "List of web application callback URLs"
  type        = list(string)
  default     = []
}

variable "android_callback_urls" {
  description = "List of Android app callback URLs"
  type        = list(string)
  default     = []
}

variable "enable_post_registration_action" {
  description = "Whether to enable the post-registration Action"
  type        = bool
  default     = true
}

variable "admin_role_name" {
  description = "Name of the admin role"
  type        = string
}

variable "admin_role_description" {
  description = "Description of the admin role"
  type        = string
  default     = "Administrator"
}

