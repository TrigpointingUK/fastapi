# SPA ECS Service for Staging Environment
# CloudWatch log group is created by the spa-ecs-service module

# Deploy SPA ECS Service
module "spa_ecs_service" {
  source = "../modules/spa-ecs-service"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  # Networking
  vpc_id             = data.terraform_remote_state.common.outputs.vpc_id
  private_subnet_ids = data.terraform_remote_state.common.outputs.private_subnet_ids

  # ECS Configuration
  ecs_cluster_id              = data.terraform_remote_state.common.outputs.ecs_cluster_id
  ecs_cluster_name            = data.terraform_remote_state.common.outputs.ecs_cluster_name
  ecs_task_execution_role_arn = data.terraform_remote_state.common.outputs.ecs_task_execution_role_arn
  ecs_task_role_arn           = data.terraform_remote_state.common.outputs.ecs_task_role_arn
  ecs_security_group_id       = module.cloudflare.ecs_security_group_id

  # ALB Configuration
  alb_listener_arn  = data.terraform_remote_state.common.outputs.https_listener_arn
  alb_rule_priority = 50 # High priority for /app/* testing route
  path_patterns     = ["/app/*"]

  # Container Configuration
  image_uri = var.spa_container_image

  # Resource Allocation
  cpu    = 256
  memory = 512

  # Scaling
  desired_count    = 1
  min_capacity     = 1
  max_capacity     = 4
  cpu_target_value = 70
}

