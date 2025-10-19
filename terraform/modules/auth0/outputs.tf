# Auth0 Module Outputs

output "connection_id" {
  description = "Auth0 database connection ID"
  value       = auth0_connection.database.id
}

output "connection_name" {
  description = "Auth0 database connection name"
  value       = auth0_connection.database.name
}

output "api_id" {
  description = "Auth0 API resource server ID"
  value       = auth0_resource_server.api.id
}

output "api_identifier" {
  description = "Auth0 API identifier (audience)"
  value       = auth0_resource_server.api.identifier
}

output "m2m_client_id" {
  description = "M2M client ID"
  value       = auth0_client.m2m_api.id
  sensitive   = true
}

output "m2m_client_secret" {
  description = "M2M client secret"
  value       = data.auth0_client.m2m_api.client_secret
  sensitive   = true
}

output "swagger_client_id" {
  description = "Swagger client ID"
  value       = auth0_client.swagger.id
}

output "website_client_id" {
  description = "Website client ID"
  value       = auth0_client.website.id
  sensitive   = true
}

output "forum_client_id" {
  description = "Forum client ID"
  value       = var.enable_forum ? auth0_client.forum[0].id : null
  sensitive   = true
}

output "wiki_client_id" {
  description = "Wiki client ID"
  value       = var.enable_wiki ? auth0_client.wiki[0].id : null
  sensitive   = true
}

output "android_client_id" {
  description = "Android client ID"
  value       = auth0_client.android.id
  sensitive   = true
}

output "admin_role_id" {
  description = "Admin role ID"
  value       = auth0_role.admin.id
}

output "action_id" {
  description = "Post User Registration Action ID"
  value       = var.enable_post_registration_action ? auth0_action.post_user_registration[0].id : null
}

output "post_login_action_id" {
  description = "Post Login Action ID"
  value       = var.enable_post_login_action ? auth0_action.post_login[0].id : null
}

output "tenant_domain" {
  description = "Auth0 tenant domain"
  value       = data.auth0_tenant.current.domain
}

output "custom_domain" {
  description = "Auth0 custom domain for user-facing authentication"
  value       = var.auth0_custom_domain
}

output "custom_domain_id" {
  description = "Auth0 custom domain resource ID"
  value       = auth0_custom_domain.main.id
}

output "custom_domain_status" {
  description = "Auth0 custom domain verification status"
  value       = auth0_custom_domain.main.status
}

output "custom_domain_verification" {
  description = "Auth0 custom domain verification details"
  value       = auth0_custom_domain.main.verification
}

# SES SMTP User Outputs
output "smtp_user_name" {
  description = "IAM username for Auth0 SMTP access"
  value       = aws_iam_user.smtp_auth0.name
}

output "smtp_username" {
  description = "SMTP username (AWS Access Key ID)"
  value       = aws_iam_access_key.smtp_auth0_credentials.id
  sensitive   = true
}

output "smtp_password" {
  description = "SMTP password (AWS SES SMTP password)"
  value       = aws_iam_access_key.smtp_auth0_credentials.ses_smtp_password_v4
  sensitive   = true
}

