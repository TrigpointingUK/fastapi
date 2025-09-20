# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode(concat([
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
          name  = "ENVIRONMENT"
          value = var.environment
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
        },
        {
          name  = "UVICORN_HOST"
          value = "0.0.0.0"
        }
      ],
      # Add Auth0 configuration if enabled
      var.auth0_domain != null ? [
        {
          name  = "AUTH0_DOMAIN"
          value = var.auth0_domain
        },
        {
          name  = "AUTH0_CONNECTION"
          value = var.auth0_connection
        },
        {
          name  = "AUTH0_ENABLED"
          value = "true"
        },
        {
          name  = "AUTH0_MANAGEMENT_API_AUDIENCE"
          value = "https://${var.auth0_domain}/api/v2/"
        },
        {
          name  = "AUTH0_API_AUDIENCE"
          value = var.auth0_api_audience
        }
      ] : [
        {
          name  = "AUTH0_ENABLED"
          value = "false"
        }
      ],
      )

      # Secrets from AWS Secrets Manager
      secrets = concat([
        # JWT Secret
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = "${var.secrets_arn}:jwt_secret_key::"
        },
        # Database Credentials
        {
          name      = "DB_HOST"
          valueFrom = "${var.credentials_secret_arn}:host::"
        },
        {
          name      = "DB_PORT"
          valueFrom = "${var.credentials_secret_arn}:port::"
        },
        {
          name      = "DB_USER"
          valueFrom = "${var.credentials_secret_arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${var.credentials_secret_arn}:password::"
        },
        {
          name      = "DB_NAME"
          valueFrom = "${var.credentials_secret_arn}:dbname::"
        }
      ],
      # Auth0 secrets (if Auth0 is enabled)
      var.auth0_domain != null ? [
        {
          name      = "AUTH0_CLIENT_ID"
          valueFrom = "${var.secrets_arn}:auth0_client_id::"
        },
        {
          name      = "AUTH0_CLIENT_SECRET"
          valueFrom = "${var.secrets_arn}:auth0_client_secret::"
        }
      ] : [],
      # Parameter Store Configuration (if enabled)
      var.parameter_store_config.enabled ? [
        for key, param in local.parameter_map : {
          name      = upper(replace(key, "/", "_"))
          valueFrom = aws_ssm_parameter.parameters[key].arn
        }
      ] : []
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = var.cloudwatch_log_group_name
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
  ],
  # Add X-Ray daemon container if X-Ray is enabled
  var.parameter_store_config.enabled && var.parameter_store_config.parameters.xray.enabled ? [
    {
      name  = "${var.project_name}-xray-daemon"
      image = "amazon/aws-xray-daemon:latest"
      cpu   = 32
      memory = 256
      portMappings = [
        {
          containerPort = 2000
          protocol      = "udp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = var.cloudwatch_log_group_name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "xray-daemon"
        }
      }
      healthCheck = {
        command = ["CMD-SHELL", "timeout 1 bash -c '</dev/tcp/127.0.0.1/2000' || exit 1"]
        interval = 30
        timeout = 5
        retries = 3
        startPeriod = 10
      }
      essential = false
    }
  ] : []
  ))

  tags = {
    Name = "${var.project_name}-${var.environment}-task-definition"
  }
}

## X-Ray permissions are included in the ecs_credentials_access policy below
## to avoid hitting the AWS limit of 10 managed policy attachments per role.

# IAM policy for ECS tasks to read database credentials
resource "aws_iam_policy" "ecs_credentials_access" {
  name        = "${var.project_name}-${var.environment}-ecs-credentials-access"
  description = "Allow ECS tasks to read database credentials"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          var.secrets_arn,
          var.credentials_secret_arn
        ]
      },
      # X-Ray permissions folded into this policy to reduce managed attachments
      {
        Effect = "Allow",
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ],
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-credentials-access"
  }
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = var.service_name != null ? var.service_name : "${var.project_name}-${var.environment}"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-app"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener_rule.app]

  tags = {
    Name = "${var.project_name}-${var.environment}-service"
  }
}

# Application Load Balancer Listener Rule
resource "aws_lb_listener_rule" "app" {
  listener_arn = var.alb_listener_arn
  priority     = var.alb_rule_priority

  action {
    type             = "forward"
    target_group_arn = var.target_group_arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-listener-rule"
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.app.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = {
    Name = "${var.project_name}-${var.environment}-autoscaling-target"
  }
}

# Auto Scaling Policy - CPU
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

# Auto Scaling Policy - Memory
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

# Attach credentials access policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_task_credentials" {
  role       = var.ecs_task_role_name
  policy_arn = aws_iam_policy.ecs_credentials_access.arn
}

# Attach credentials access policy to ECS task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_credentials" {
  role       = var.ecs_task_execution_role_name
  policy_arn = aws_iam_policy.ecs_credentials_access.arn
}
