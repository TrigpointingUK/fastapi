# CloudWatch Log Group for MediaWiki
resource "aws_cloudwatch_log_group" "mediawiki" {
  name              = "/aws/ecs/${var.project_name}-mediawiki-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-mediawiki-${var.environment}-logs"
  }
}

# ECS Task Definition for MediaWiki
resource "aws_ecs_task_definition" "mediawiki" {
  family                   = "${var.project_name}-mediawiki-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "${var.project_name}-mediawiki"
      image = var.image_uri
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      secrets = [
        # Database credentials from trigpointing-mediawiki-credentials
        {
          name      = "MEDIAWIKI_DB_HOST"
          valueFrom = "${var.mediawiki_db_credentials_arn}:host::"
        },
        {
          name      = "MEDIAWIKI_DB_NAME"
          valueFrom = "${var.mediawiki_db_credentials_arn}:dbname::"
        },
        {
          name      = "MEDIAWIKI_DB_USER"
          valueFrom = "${var.mediawiki_db_credentials_arn}:username::"
        },
        {
          name      = "MEDIAWIKI_DB_PASSWORD"
          valueFrom = "${var.mediawiki_db_credentials_arn}:password::"
        },
        # Application secrets from trigpointing-mediawiki-app-secrets
        {
          name      = "MW_SITENAME"
          valueFrom = "${var.mediawiki_app_secrets_arn}:MW_SITENAME::"
        },
        {
          name      = "MW_SERVER"
          valueFrom = "${var.mediawiki_app_secrets_arn}:MW_SERVER::"
        },
        {
          name      = "MW_SECRET_KEY"
          valueFrom = "${var.mediawiki_app_secrets_arn}:MW_SECRET_KEY::"
        },
        {
          name      = "MW_UPGRADE_KEY"
          valueFrom = "${var.mediawiki_app_secrets_arn}:MW_UPGRADE_KEY::"
        },
        {
          name      = "CACHE_TLS"
          valueFrom = "${var.mediawiki_app_secrets_arn}:CACHE_TLS::"
        },
        {
          name      = "MW_ENABLE_LOCAL_LOGIN"
          valueFrom = "${var.mediawiki_app_secrets_arn}:MW_ENABLE_LOCAL_LOGIN::"
        },
        {
          name      = "OIDC_PROVIDER_URL"
          valueFrom = "${var.mediawiki_app_secrets_arn}:OIDC_PROVIDER_URL::"
        },
        {
          name      = "OIDC_CLIENT_ID"
          valueFrom = "${var.mediawiki_app_secrets_arn}:OIDC_CLIENT_ID::"
        },
        {
          name      = "OIDC_CLIENT_SECRET"
          valueFrom = "${var.mediawiki_app_secrets_arn}:OIDC_CLIENT_SECRET::"
        },
        {
          name      = "OIDC_REDIRECT_URI"
          valueFrom = "${var.mediawiki_app_secrets_arn}:OIDC_REDIRECT_URI::"
        }
      ]
      environment = [
        {
          name  = "AWS_S3_BUCKET"
          value = var.s3_bucket_name
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "CACHE_HOST"
          value = var.cache_host
        },
        {
          name  = "CACHE_PORT"
          value = tostring(var.cache_port)
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.mediawiki.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 120
      }
      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-mediawiki-${var.environment}-task-definition"
  }
}

# ECS Service for MediaWiki
resource "aws_ecs_service" "mediawiki" {
  name            = "${var.project_name}-mediawiki-${var.environment}"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.mediawiki.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-mediawiki"
    container_port   = 80
  }

  tags = {
    Name = "${var.project_name}-mediawiki-${var.environment}-service"
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "mediawiki" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.mediawiki.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "mediawiki_cpu" {
  name               = "${var.project_name}-mediawiki-${var.environment}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mediawiki.resource_id
  scalable_dimension = aws_appautoscaling_target.mediawiki.scalable_dimension
  service_namespace  = aws_appautoscaling_target.mediawiki.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_target_value
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "mediawiki_memory" {
  name               = "${var.project_name}-mediawiki-${var.environment}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mediawiki.resource_id
  scalable_dimension = aws_appautoscaling_target.mediawiki.scalable_dimension
  service_namespace  = aws_appautoscaling_target.mediawiki.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = var.memory_target_value
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
