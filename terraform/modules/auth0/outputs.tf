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
  description = "Swagger UI client ID"
  value       = auth0_client.swagger_ui.id
}

output "web_app_client_id" {
  description = "Web application client ID"
  value       = auth0_client.web_app.id
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

output "tenant_domain" {
  description = "Auth0 tenant domain"
  value       = data.auth0_tenant.current.domain
}

output "custom_domain" {
  description = "Auth0 custom domain for user-facing authentication"
  value       = var.auth0_custom_domain
}

