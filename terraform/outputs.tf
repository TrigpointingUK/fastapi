output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "rds_endpoint" {
  description = "RDS instance endpoint (only for managed RDS)"
  value       = var.use_external_database ? null : aws_db_instance.main[0].endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port (only for managed RDS)"
  value       = var.use_external_database ? null : aws_db_instance.main[0].port
}

output "external_database_secret_arn" {
  description = "ARN of the external database secret"
  value       = var.use_external_database ? aws_secretsmanager_secret.external_database[0].arn : null
  sensitive   = true
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app.name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "bastion_host_ip" {
  description = "Elastic IP address of the bastion host"
  value       = var.environment == "staging" && var.admin_ip_address != null ? aws_eip.bastion[0].public_ip : null
}

output "bastion_host_dns" {
  description = "Public DNS name of the bastion host (via Elastic IP)"
  value       = var.environment == "staging" && var.admin_ip_address != null ? aws_eip.bastion[0].public_dns : null
}

output "dms_security_group_id" {
  description = "Security group ID for DMS replication instances"
  value       = var.enable_dms_access ? aws_security_group.dms[0].id : null
}
