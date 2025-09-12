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

# Database Schemas
output "production_schema_name" {
  description = "Name of the production database schema"
  value       = mysql_database.production.name
}

output "staging_schema_name" {
  description = "Name of the staging database schema"
  value       = mysql_database.staging.name
}

# DynamoDB Table
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_state_lock.name
}

# Note: S3 bucket is managed externally
# Bucket: tuk-terraform-state (in eu-west-1)
