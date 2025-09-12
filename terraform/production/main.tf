terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Backend configuration will be provided via backend.conf
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "production"
      ManagedBy   = "terraform"
    }
  }
}

# Data source for common infrastructure
data "terraform_remote_state" "common" {
  backend = "s3"
  config = {
    bucket = "tuk-terraform-state"
    key    = "fastapi-common/terraform.tfstate"
    region = "eu-west-1"  # S3 bucket region
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}-production"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-production-logs"
    Environment = "production"
  }
}

# CloudFlare module for security groups and SSL
module "cloudflare" {
  source = "../modules/cloudflare"

  project_name           = var.project_name
  environment           = "production"
  vpc_id                = data.terraform_remote_state.common.outputs.vpc_id
  enable_cloudflare_ssl = var.enable_cloudflare_ssl
}

# Target Group module (for shared ALB)
module "target_group" {
  source = "../modules/target-group"

  project_name      = var.project_name
  environment       = "production"
  vpc_id           = data.terraform_remote_state.common.outputs.vpc_id
  alb_listener_arn = data.terraform_remote_state.common.outputs.alb_listener_arn
  domain_name      = var.domain_name
  priority         = 200  # Production gets priority 200
}

# Secrets module
module "secrets" {
  source = "../modules/secrets"

  project_name                    = var.project_name
  environment                    = "production"
  database_url                   = "mysql+pymysql://fastapi_user:temp-password-change-this@${data.terraform_remote_state.common.outputs.rds_endpoint}:${data.terraform_remote_state.common.outputs.rds_port}/fastapi_common"
  ecs_task_role_name            = data.terraform_remote_state.common.outputs.ecs_task_role_arn
  ecs_task_execution_role_name  = data.terraform_remote_state.common.outputs.ecs_task_execution_role_arn
  auth0_domain                  = var.auth0_domain
}

# ECS Service module
module "ecs_service" {
  source = "../modules/ecs-service"

  project_name                    = var.project_name
  environment                    = "production"
  aws_region                     = var.aws_region
  container_image                = var.container_image
  cpu                           = var.cpu
  memory                        = var.memory
  desired_count                 = var.desired_count
  min_capacity                  = var.min_capacity
  max_capacity                  = var.max_capacity
  cpu_target_value              = var.cpu_target_value
  memory_target_value           = var.memory_target_value
  ecs_cluster_id                = data.terraform_remote_state.common.outputs.ecs_cluster_id
  ecs_cluster_name              = data.terraform_remote_state.common.outputs.ecs_cluster_name
  ecs_task_execution_role_arn   = data.terraform_remote_state.common.outputs.ecs_task_execution_role_arn
  ecs_task_role_arn             = data.terraform_remote_state.common.outputs.ecs_task_role_arn
  ecs_security_group_id         = module.cloudflare.ecs_security_group_id
  private_subnet_ids            = data.terraform_remote_state.common.outputs.private_subnet_ids
  target_group_arn              = module.target_group.target_group_arn
  secrets_arn                   = module.secrets.secrets_arn
  cloudwatch_log_group_name     = aws_cloudwatch_log_group.app.name
  auth0_domain                  = var.auth0_domain
  auth0_connection              = var.auth0_connection
  auth0_api_audience            = var.auth0_api_audience
}
