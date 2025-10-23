# Valkey ECS Service Deployment
module "valkey" {
  source = "../modules/valkey"

  project_name                  = var.project_name
  environment                   = "common"
  aws_region                    = var.aws_region
  vpc_id                        = aws_vpc.main.id
  ecs_cluster_id                = aws_ecs_cluster.main.id
  ecs_cluster_name              = aws_ecs_cluster.main.name
  ecs_task_execution_role_arn   = aws_iam_role.ecs_task_execution_role.arn
  ecs_task_role_arn             = aws_iam_role.ecs_task_role.arn
  private_subnet_ids            = aws_subnet.private[*].id
  valkey_security_group_id      = aws_security_group.valkey_ecs.id
  service_discovery_service_arn = aws_service_discovery_service.valkey.arn

  # Resource allocation
  cpu               = 256
  memory            = 512
  valkey_cpu        = 128
  valkey_memory     = 256
  valkey_max_memory = "200mb"
  commander_cpu     = 128
  commander_memory  = 256

  # Scaling configuration
  desired_count    = 1
  min_capacity     = 1
  max_capacity     = 3
  cpu_target_value = 70

  # Logging
  log_retention_days = 7
}

# ALB Listener Rule for Redis Commander
resource "aws_lb_listener_rule" "valkey_commander" {
  count        = var.enable_cloudflare_ssl ? 1 : 0
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 150

  action {
    type             = "forward"
    target_group_arn = module.valkey.valkey_commander_target_group_arn
  }

  condition {
    host_header {
      values = ["cache.trigpointing.uk"]
    }
  }

  tags = {
    Name = "${var.project_name}-valkey-commander-rule"
  }
}