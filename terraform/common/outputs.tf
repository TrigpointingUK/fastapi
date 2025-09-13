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

output "admin_password" {
  description = "RDS admin password"
  value       = random_password.admin_password.result
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

# DMS Endpoints
output "dms_staging_endpoint_arn" {
  description = "ARN of the DMS staging user endpoint"
  value       = aws_dms_endpoint.staging_user.endpoint_arn
}

output "dms_production_endpoint_arn" {
  description = "ARN of the DMS production user endpoint"
  value       = aws_dms_endpoint.production_user.endpoint_arn
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

output "alb_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.app_http.arn
}

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
