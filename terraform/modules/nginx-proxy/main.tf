# CloudWatch Log Group for nginx proxy
resource "aws_cloudwatch_log_group" "nginx_proxy" {
  name              = "/aws/ecs/${var.project_name}-nginx-proxy"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-nginx-proxy-logs"
  }
}

# ECS Task Definition for nginx proxy
resource "aws_ecs_task_definition" "nginx_proxy" {
  family                   = "${var.project_name}-nginx-proxy"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "${var.project_name}-nginx-proxy"
      image = "nginx:alpine"
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "LEGACY_SERVER_TARGET"
          value = var.legacy_server_target
        }
      ]
      # Use a startup command to fetch config from Parameter Store and start nginx
      command = [
        "/bin/sh",
        "-c",
        <<-EOT
        apk add --no-cache aws-cli && \
        aws ssm get-parameter --name ${var.nginx_config_parameter_name} --region ${var.aws_region} --with-decryption --query 'Parameter.Value' --output text > /etc/nginx/conf.d/default.conf && \
        nginx -g 'daemon off;'
        EOT
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.nginx_proxy.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost/nginx-health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-nginx-proxy-task-definition"
  }
}

# ECS Service for nginx proxy
resource "aws_ecs_service" "nginx_proxy" {
  name                   = "${var.project_name}-nginx-proxy"
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.nginx_proxy.arn
  desired_count          = var.desired_count
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-nginx-proxy"
    container_port   = 80
  }

  tags = {
    Name = "${var.project_name}-nginx-proxy-service"
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "nginx_proxy" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.nginx_proxy.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = {
    Name = "${var.project_name}-nginx-proxy-autoscaling-target"
  }
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "nginx_proxy_cpu" {
  name               = "${var.project_name}-nginx-proxy-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.nginx_proxy.resource_id
  scalable_dimension = aws_appautoscaling_target.nginx_proxy.scalable_dimension
  service_namespace  = aws_appautoscaling_target.nginx_proxy.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = var.cpu_target_value
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# IAM policy to allow ECS task to read SSM parameter
resource "aws_iam_policy" "nginx_proxy_ssm_access" {
  name        = "${var.project_name}-nginx-proxy-ssm-access"
  description = "Allow nginx proxy ECS task to read SSM parameter for nginx config"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter${var.nginx_config_parameter_name}"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-nginx-proxy-ssm-access"
  }
}

# Attach SSM policy to task role
resource "aws_iam_role_policy_attachment" "nginx_proxy_ssm" {
  role       = split("/", var.ecs_task_role_arn)[1]
  policy_arn = aws_iam_policy.nginx_proxy_ssm_access.arn
}

