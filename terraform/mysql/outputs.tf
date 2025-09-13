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
  value       = aws_secretsmanager_secret.admin_credentials.arn
  sensitive   = true
}

output "production_credentials_arn" {
  description = "ARN of the production credentials secret"
  value       = aws_secretsmanager_secret.production_credentials.arn
  sensitive   = true
}

output "staging_credentials_arn" {
  description = "ARN of the staging credentials secret"
  value       = aws_secretsmanager_secret.staging_credentials.arn
  sensitive   = true
}

output "backups_credentials_arn" {
  description = "ARN of the backups credentials secret"
  value       = aws_secretsmanager_secret.backups_credentials.arn
  sensitive   = true
}
