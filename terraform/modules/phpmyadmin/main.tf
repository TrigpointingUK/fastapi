# CloudWatch Log Group for phpMyAdmin
resource "aws_cloudwatch_log_group" "phpmyadmin" {
  name              = "/aws/ecs/${var.project_name}-phpmyadmin-${var.environment}"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-phpmyadmin-${var.environment}-logs"
  }
}

# ECS Task Definition for phpMyAdmin
resource "aws_ecs_task_definition" "phpmyadmin" {
  family                   = "${var.project_name}-phpmyadmin-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "${var.project_name}-phpmyadmin"
      image = "phpmyadmin/phpmyadmin:latest"
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "PMA_ARBITRARY"
          value = "1"
        },
        {
          name  = "UPLOAD_LIMIT"
          value = "64M"
        },
        {
          name  = "MEMORY_LIMIT"
          value = "256M"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.phpmyadmin.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-phpmyadmin-${var.environment}-task-definition"
  }
}

# ECS Service for phpMyAdmin
resource "aws_ecs_service" "phpmyadmin" {
  name            = "${var.project_name}-phpmyadmin-${var.environment}"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.phpmyadmin.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "${var.project_name}-phpmyadmin"
    container_port   = 80
  }

  tags = {
    Name = "${var.project_name}-phpmyadmin-${var.environment}-service"
  }
}
