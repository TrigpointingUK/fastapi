# AWS Systems Manager Parameter Store Configuration
# Clean object-based approach with dynamic parameter creation

locals {
  # Build parameter map dynamically from the object configuration
  parameter_map = merge(
    # X-Ray parameters
    var.parameter_store_config.enabled && var.parameter_store_config.parameters.xray.enabled ? {
      "xray/enabled" = {
        value       = tostring(var.parameter_store_config.parameters.xray.enabled)
        type        = "String"
        description = "Enable X-Ray tracing"
      }
      "xray/service_name" = {
        value       = var.parameter_store_config.parameters.xray.service_name
        type        = "String"
        description = "X-Ray service name"
      }
      "xray/sampling_rate" = {
        value       = tostring(var.parameter_store_config.parameters.xray.sampling_rate)
        type        = "String"
        description = "X-Ray sampling rate (0.0 to 1.0)"
      }
    } : {},

    # Optional X-Ray daemon address
    var.parameter_store_config.enabled && var.parameter_store_config.parameters.xray.daemon_address != null ? {
      "xray/daemon_address" = {
        value       = var.parameter_store_config.parameters.xray.daemon_address
        type        = "String"
        description = "X-Ray daemon address (optional)"
      }
    } : {},

    # Application parameters
    var.parameter_store_config.enabled ? {
      "app/log_level" = {
        value       = var.parameter_store_config.parameters.app.log_level
        type        = "String"
        description = "Application log level (DEBUG, INFO, WARNING, ERROR)"
      }
    } : {},

    # Optional CORS origins
    var.parameter_store_config.enabled && var.parameter_store_config.parameters.app.cors_origins != null ? {
      "app/cors_origins" = {
        value       = var.parameter_store_config.parameters.app.cors_origins
        type        = "String"
        description = "CORS allowed origins (comma-separated)"
      }
    } : {},

    # Database parameters
    var.parameter_store_config.enabled ? {
      "database/pool_size" = {
        value       = tostring(var.parameter_store_config.parameters.database.pool_size)
        type        = "String"
        description = "Database connection pool size"
      }
      "database/pool_recycle" = {
        value       = tostring(var.parameter_store_config.parameters.database.pool_recycle)
        type        = "String"
        description = "Database connection pool recycle time (seconds)"
      }
    } : {}
  )
}

# Create parameters dynamically
resource "aws_ssm_parameter" "parameters" {
  for_each = var.parameter_store_config.enabled ? local.parameter_map : {}

  name  = "/${var.project_name}/${var.environment}/${each.key}"
  type  = each.value.type
  value = each.value.value

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = each.key
  }
}

# IAM policy for ECS tasks to read Parameter Store parameters
resource "aws_iam_policy" "ecs_parameter_store_access" {
  count       = var.parameter_store_config.enabled ? 1 : 0
  name        = "${var.project_name}-${var.environment}-ecs-parameter-store-access"
  description = "Allow ECS tasks to read Parameter Store parameters"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/${var.environment}/*"
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-parameter-store-access"
  }
}

# Attach Parameter Store policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_parameter_store_access" {
  count      = var.parameter_store_config.enabled ? 1 : 0
  role       = var.ecs_task_role_name
  policy_arn = aws_iam_policy.ecs_parameter_store_access[0].arn
}

# Attach Parameter Store policy to ECS task execution role as well,
# because secrets/ssm references in task definitions are fetched by the execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_parameter_store_access" {
  count      = var.parameter_store_config.enabled ? 1 : 0
  role       = var.ecs_task_execution_role_name
  policy_arn = aws_iam_policy.ecs_parameter_store_access[0].arn
}
