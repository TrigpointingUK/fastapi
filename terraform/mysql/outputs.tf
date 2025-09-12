# Database Schemas
output "production_schema_name" {
  description = "Name of the production database schema"
  value       = mysql_database.production.name
}

output "staging_schema_name" {
  description = "Name of the staging database schema"
  value       = mysql_database.staging.name
}

# RDS User Credentials
output "admin_credentials_arn" {
  description = "ARN of the admin credentials secret"
  value       = data.terraform_remote_state.common.outputs.admin_credentials_arn
  sensitive   = true
}

output "production_credentials_arn" {
  description = "ARN of the production credentials secret"
  value       = data.terraform_remote_state.common.outputs.production_credentials_arn
  sensitive   = true
}

output "staging_credentials_arn" {
  description = "ARN of the staging credentials secret"
  value       = data.terraform_remote_state.common.outputs.staging_credentials_arn
  sensitive   = true
}

output "backups_credentials_arn" {
  description = "ARN of the backups credentials secret"
  value       = data.terraform_remote_state.common.outputs.backups_credentials_arn
  sensitive   = true
}
