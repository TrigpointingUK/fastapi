variable "user_name" {
  description = "Name of the IAM user for SES SMTP access"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "allowed_from_addresses" {
  description = "List of email addresses this SMTP user is allowed to send from"
  type        = list(string)
  default     = []
}
