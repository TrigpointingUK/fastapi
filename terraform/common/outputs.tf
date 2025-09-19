# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

# ECS Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_task_role_name" {
  description = "Name of the ECS task role"
  value       = aws_iam_role.ecs_task_role.name
}

output "ecs_task_execution_role_name" {
  description = "Name of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.name
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "rds_db_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.identifier
}

output "rds_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

# Note: admin_password output removed - use master_user_secret_arn instead

output "master_user_secret_arn" {
  description = "ARN of the RDS master user secret (for password rotation)"
  value       = length(aws_db_instance.main.master_user_secret) > 0 ? aws_db_instance.main.master_user_secret[0].secret_arn : null
  sensitive   = true
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}


# Bastion Outputs
output "bastion_public_ip" {
  description = "Public IP of the bastion host"
  value       = aws_eip.bastion.public_ip
}

output "bastion_security_group_id" {
  description = "ID of the bastion security group"
  value       = aws_security_group.bastion.id
}

# Web Server Outputs
output "webserver_private_ip" {
  description = "Private IP of the web server"
  value       = aws_instance.webserver.private_ip
}

output "webserver_security_group_id" {
  description = "ID of the web server security group"
  value       = aws_security_group.webserver.id
}

# DMS Endpoints - Disabled for initial deployment
# output "dms_staging_endpoint_arn" {
#   description = "ARN of the DMS staging user endpoint"
#   value       = aws_dms_endpoint.staging_user.endpoint_arn
# }

# output "dms_production_endpoint_arn" {
#   description = "ARN of the DMS production user endpoint"
#   value       = aws_dms_endpoint.production_user.endpoint_arn
# }

# DMS Replication Configs - Disabled for initial deployment
# output "dms_staging_config_arn" {
#   description = "ARN of the DMS staging replication config"
#   value       = aws_dms_replication_config.staging.arn
# }

# output "dms_production_config_arn" {
#   description = "ARN of the DMS production replication config"
#   value       = aws_dms_replication_config.production.arn
# }

# DMS Target Endpoints
output "dms_staging_target_arn" {
  description = "ARN of the DMS staging target endpoint"
  value       = aws_dms_endpoint.staging_target.endpoint_arn
}

output "dms_production_target_arn" {
  description = "ARN of the DMS production target endpoint"
  value       = aws_dms_endpoint.production_target.endpoint_arn
}

output "dms_service_role_arn" {
  description = "ARN of the DMS service role"
  value       = aws_iam_role.dms_service_role.arn
}

output "dms_security_group_id" {
  description = "ID of the DMS security group"
  value       = aws_security_group.dms.id
}

output "dms_replication_subnet_group_id" {
  description = "ID of the DMS replication subnet group"
  value       = aws_dms_replication_subnet_group.main.id
}

# DMS Serverless Migration Tasks
output "dms_staging_migration_arn" {
  description = "ARN of the DMS staging migration task"
  value       = aws_dms_replication_config.staging_migration.arn
}

output "dms_production_migration_arn" {
  description = "ARN of the DMS production migration task"
  value       = aws_dms_replication_config.production_migration.arn
}

# ALB Outputs
output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "alb_security_group_id" {
  description = "Security group ID of the ALB"
  value       = aws_security_group.alb.id
}

# Note: ALB listener ARNs are now managed by individual environment modules
# (staging and production) for their respective HTTPS listeners

# Note: RDS user credentials and database schemas are now managed in the mysql/ directory

# DynamoDB Table
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_state_lock.name
}

# CloudFlare DNS Records
output "api_staging_domain" {
  description = "Staging API domain (api.trigpointing.me)"
  value       = "api.trigpointing.me"
}

output "api_production_domain" {
  description = "Production API domain (api.trigpointing.uk)"
  value       = "api.trigpointing.uk"
}

output "api_staging_record_id" {
  description = "CloudFlare record ID for staging API"
  value       = cloudflare_record.api_staging.id
}

output "api_production_record_id" {
  description = "CloudFlare record ID for production API"
  value       = cloudflare_record.api_production.id
}

# Note: S3 bucket is managed externally
# Bucket: tuk-terraform-state (in eu-west-1)

# HTTPS Listener ARN for environments to use
output "https_listener_arn" {
  description = "ARN of the shared HTTPS listener"
  value       = var.enable_cloudflare_ssl ? aws_lb_listener.app_https[0].arn : null
}
