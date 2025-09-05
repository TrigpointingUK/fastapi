# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.environment == "production" ? 1024 : 512
  memory                   = var.environment == "production" ? 2048 : 1024
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "${var.project_name}-app"
      image = var.container_image
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      environment = concat([
        {
          name  = "JWT_SECRET_KEY"
          value = var.jwt_secret_key
        },
        {
          name  = "JWT_ALGORITHM"
          value = "HS256"
        },
        {
          name  = "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
          value = "30"
        },
        {
          name  = "DEBUG"
          value = var.environment == "production" ? "false" : "true"
        }
      ], 
      # Add Auth0 configuration if enabled
      var.auth0_domain != null ? [
        {
          name  = "AUTH0_DOMAIN"
          value = var.auth0_domain
        },
        {
          name  = "AUTH0_SECRET_NAME"
          value = var.auth0_secret_name
        },
        {
          name  = "AUTH0_CONNECTION"
          value = var.auth0_connection
        },
        {
          name  = "AUTH0_ENABLED"
          value = "true"
        }
      ] : [
        {
          name  = "AUTH0_ENABLED"
          value = "false"
        }
      ],
      # Add DATABASE_URL for managed RDS (when not using external database)
      var.use_external_database ? [] : [
        {
          name  = "DATABASE_URL"
          value = "mysql+pymysql://${var.db_username}:${var.db_password}@${aws_db_instance.main[0].endpoint}/${var.db_schema}"
        }
      ]
      )
      
      # Secrets from AWS Secrets Manager
      secrets = concat(
        # External database secret (if using external database)
        var.use_external_database ? [
          {
            name      = "DATABASE_URL"
            valueFrom = "${aws_secretsmanager_secret.external_database[0].arn}:database_url::"
          }
        ] : [],
        # Auth0 secrets (if Auth0 is enabled)
        var.auth0_domain != null ? [
          {
            name      = "AUTH0_CLIENT_ID"
            valueFrom = "${aws_secretsmanager_secret.auth0_credentials[0].arn}:client_id::"
          },
          {
            name      = "AUTH0_CLIENT_SECRET"
            valueFrom = "${aws_secretsmanager_secret.auth0_credentials[0].arn}:client_secret::"
          },
          {
            name      = "AUTH0_AUDIENCE"
            valueFrom = "${aws_secretsmanager_secret.auth0_credentials[0].arn}:audience::"
          }
        ] : []
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=10)\" || exit 1"]
        interval = 30
        timeout = 10
        retries = 3
        startPeriod = 60
      }
      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-${var.environment}-task-definition"
  }
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-${var.environment}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "${var.project_name}-app"
    container_port   = 8000
  }



  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution_role,
    # Note: Terraform requires static depends_on - both listeners are declared
    # but only one will be created based on enable_cloudflare_ssl
    aws_lb_listener.app_https,
    aws_lb_listener.app_http,
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-service"
  }
}

# Auto Scaling
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "${var.project_name}-${var.environment}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = var.cpu_target_value
  }
}

resource "aws_appautoscaling_policy" "ecs_policy_memory" {
  name               = "${var.project_name}-${var.environment}-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = var.memory_target_value
  }
}
