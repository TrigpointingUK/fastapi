# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}

# Cloudflare module
module "cloudflare" {
  source = "../modules/cloudflare"

  project_name          = var.project_name
  environment           = "staging"
  vpc_id                = data.terraform_remote_state.common.outputs.vpc_id
  alb_security_group_id = data.terraform_remote_state.common.outputs.alb_security_group_id
}

# Target Group module
module "target_group" {
  source = "../modules/target-group"

  project_name      = var.project_name
  environment       = "staging"
  vpc_id            = data.terraform_remote_state.common.outputs.vpc_id
  alb_listener_arn  = data.terraform_remote_state.common.outputs.https_listener_arn
  domain_name       = "api.trigpointing.me"
  priority          = 100
  health_check_path = "/health"
}

# Secrets module
module "secrets" {
  source = "../modules/secrets"

  project_name                 = var.project_name
  environment                  = "staging"
  ecs_task_role_name           = data.terraform_remote_state.common.outputs.ecs_task_role_name
  ecs_task_execution_role_name = data.terraform_remote_state.common.outputs.ecs_task_execution_role_arn
  auth0_domain                 = var.auth0_domain
}

# ECS Service module
module "ecs_service" {
  source = "../modules/ecs-service"

  project_name                 = var.project_name
  environment                  = "staging"
  service_name                 = "fastapi-staging-service" # Keep the original service name
  aws_region                   = var.aws_region
  container_image              = var.container_image
  cpu                          = var.cpu
  memory                       = var.memory
  desired_count                = var.desired_count
  min_capacity                 = var.min_capacity
  max_capacity                 = var.max_capacity
  cpu_target_value             = var.cpu_target_value
  memory_target_value          = var.memory_target_value
  ecs_cluster_id               = data.terraform_remote_state.common.outputs.ecs_cluster_id
  ecs_cluster_name             = data.terraform_remote_state.common.outputs.ecs_cluster_name
  ecs_task_execution_role_arn  = data.terraform_remote_state.common.outputs.ecs_task_execution_role_arn
  ecs_task_execution_role_name = data.terraform_remote_state.common.outputs.ecs_task_execution_role_name
  ecs_task_role_arn            = data.terraform_remote_state.common.outputs.ecs_task_role_arn
  ecs_task_role_name           = data.terraform_remote_state.common.outputs.ecs_task_role_name
  ecs_security_group_id        = module.cloudflare.ecs_security_group_id
  private_subnet_ids           = data.terraform_remote_state.common.outputs.private_subnet_ids
  target_group_arn             = module.target_group.target_group_arn
  alb_listener_arn             = data.terraform_remote_state.common.outputs.https_listener_arn
  alb_rule_priority            = 101
  secrets_arn                  = module.secrets.secrets_arn
  credentials_secret_arn       = "arn:aws:secretsmanager:eu-west-1:534526983272:secret:fastapi-staging-credentials-udrQoU"
  cloudwatch_log_group_name    = aws_cloudwatch_log_group.app.name
  auth0_domain                 = var.auth0_domain
  auth0_connection             = var.auth0_connection
  auth0_api_audience           = var.auth0_api_audience

  # New Parameter Store configuration
  parameter_store_config = var.parameter_store_config
}

# Monitoring module for X-Ray groups and sampling rules
module "monitoring" {
  source = "../monitoring"

  project_name            = var.project_name
  environment             = "staging"
  aws_region              = var.aws_region
  xray_sampling_rate      = var.parameter_store_config.parameters.xray.sampling_rate
  enable_xray_daemon_role = false # Not needed for Fargate
  enable_xray_daemon_logs = false # Not needed for Fargate
  log_retention_days      = 14
}
