variable "aws_region" {
  description = "AWS region for monitoring resources (Ireland preferred)"
  type        = string
  default     = "eu-west-1" # Ireland
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "trigpointing"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "enable_slack_notifications" {
  description = "Enable Slack notifications via AWS Chatbot"
  type        = bool
  default     = false
}

variable "slack_workspace_id" {
  description = "Slack workspace ID for AWS Chatbot"
  type        = string
  default     = null
}

variable "slack_channel_id" {
  description = "Slack channel ID for AWS Chatbot"
  type        = string
  default     = null
}

variable "slack_configuration_name" {
  description = "Existing Chatbot Slack configuration_name (e.g., Teasel-TrigpointingUK)"
  type        = string
  default     = null
}


variable "tuk_guest_secret_name" {
  description = "Name of the existing Secrets Manager secret for guest credentials"
  type        = string
  default     = "tuk_guest_user"
}

variable "additional_allowed_secret_arns" {
  description = "Additional secret ARNs the canaries may access"
  type        = list(string)
  default     = []
}
