output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = data.terraform_remote_state.common.outputs.alb_dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = data.terraform_remote_state.common.outputs.alb_zone_id
}

output "domain_name" {
  description = "Domain name for the API"
  value       = var.domain_name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs_service.ecs_service_name
}

output "secrets_arn" {
  description = "ARN of the secrets manager secret"
  value       = module.secrets.secrets_arn
}
