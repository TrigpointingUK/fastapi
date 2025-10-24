# Security Group for phpMyAdmin ECS tasks
resource "aws_security_group" "phpmyadmin_ecs" {
  name        = "${var.project_name}-phpmyadmin-ecs-tasks-sg"
  description = "Security group for phpMyAdmin ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-phpmyadmin-ecs-tasks-sg"
  }
}

# phpMyAdmin ECS Service
module "phpmyadmin" {
  source = "../modules/phpmyadmin"

  project_name                 = var.project_name
  environment                  = "common"
  aws_region                   = var.aws_region
  cpu                          = 256
  memory                       = 512
  desired_count                = 1
  min_capacity                 = 0
  max_capacity                 = 1
  cpu_target_value             = 70
  memory_target_value          = 80
  ecs_cluster_id               = aws_ecs_cluster.main.id
  ecs_cluster_name             = aws_ecs_cluster.main.name
  ecs_task_execution_role_arn  = aws_iam_role.ecs_task_execution_role.arn
  ecs_task_execution_role_name = aws_iam_role.ecs_task_execution_role.name
  ecs_task_role_arn            = aws_iam_role.ecs_task_role.arn
  ecs_task_role_name           = aws_iam_role.ecs_task_role.name
  ecs_security_group_id        = aws_security_group.phpmyadmin_ecs.id
  private_subnet_ids           = aws_subnet.private[*].id
  target_group_arn             = aws_lb_target_group.phpmyadmin.arn
  cloudwatch_log_group_name    = "/aws/ecs/${var.project_name}-phpmyadmin-common"

  depends_on = [aws_lb_listener_rule.phpmyadmin]
}

# Target Group for phpMyAdmin
resource "aws_lb_target_group" "phpmyadmin" {
  name        = "${var.project_name}-phpmyadmin-ecs-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.project_name}-phpmyadmin-ecs-tg"
  }
}

# Listener rule for phpMyAdmin with OIDC Authentication
resource "aws_lb_listener_rule" "phpmyadmin" {
  listener_arn = aws_lb_listener.app_https[0].arn
  priority     = 125

  # Action 1: Authenticate users via OIDC (Auth0)
  action {
    type  = "authenticate-oidc"
    order = 1

    authenticate_oidc {
      issuer                              = local.alb_oidc_config.issuer
      authorization_endpoint              = local.alb_oidc_config.authorization_endpoint
      token_endpoint                      = local.alb_oidc_config.token_endpoint
      user_info_endpoint                  = local.alb_oidc_config.user_info_endpoint
      client_id                           = local.alb_oidc_config.client_id
      client_secret                       = local.alb_oidc_config.client_secret
      session_cookie_name                 = "AWSELBAuthSessionCookie"
      session_timeout                     = 3600
      scope                               = "openid profile email"
      on_unauthenticated_request          = "authenticate"
      authentication_request_extra_params = {}
    }
  }

  # Action 2: Forward to target group
  action {
    type             = "forward"
    order            = 2
    target_group_arn = aws_lb_target_group.phpmyadmin.arn
  }

  condition {
    host_header {
      values = ["phpmyadmin.trigpointing.uk"]
    }
  }

  tags = {
    Name = "${var.project_name}-phpmyadmin-listener-rule"
  }

  depends_on = [aws_secretsmanager_secret_version.alb_oidc]
}
