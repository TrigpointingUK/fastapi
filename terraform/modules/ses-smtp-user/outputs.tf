output "user_name" {
  description = "Name of the IAM user"
  value       = aws_iam_user.smtp_user.name
}

output "user_arn" {
  description = "ARN of the IAM user"
  value       = aws_iam_user.smtp_user.arn
}

output "smtp_username" {
  description = "SMTP username (AWS Access Key ID)"
  value       = aws_iam_access_key.smtp_credentials.id
  sensitive   = true
}

output "smtp_password" {
  description = "SMTP password (derived from AWS Secret Access Key)"
  value       = aws_iam_access_key.smtp_credentials.ses_smtp_password_v4
  sensitive   = true
}

output "access_key_id" {
  description = "AWS Access Key ID"
  value       = aws_iam_access_key.smtp_credentials.id
  sensitive   = true
}

output "secret_access_key" {
  description = "AWS Secret Access Key"
  value       = aws_iam_access_key.smtp_credentials.secret
  sensitive   = true
}
