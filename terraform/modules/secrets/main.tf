# Random string for unique policy naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# AWS Secrets Manager for application secrets (JWT, Database, Auth0)
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "fastapi-${var.environment}-app-secrets"
  description = "Application secrets for ${var.environment} environment (JWT, Database, Auth0)"

  tags = {
    Name        = "fastapi-${var.environment}-app-secrets"
    Environment = var.environment
    Purpose     = "Application Secrets"
  }
}

# Secret version with placeholder values (you'll update this manually)
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    # JWT Configuration
    jwt_secret_key = "your-jwt-secret-key-change-this"

    # Auth0 Configuration (if enabled)
    auth0_client_id     = var.auth0_domain != null ? "your-auth0-client-id" : null
    auth0_client_secret = var.auth0_domain != null ? "your-auth0-client-secret" : null
    auth0_domain        = var.auth0_domain
  })

  # Ignore changes to secret string after initial creation
  # This allows manual updates via AWS Console/CLI without Terraform interference
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM policy for ECS tasks to read application secrets
resource "aws_iam_policy" "ecs_app_secrets_access" {
  name        = "${var.project_name}-${var.environment}-ecs-app-secrets-access-${random_string.suffix.result}"
  description = "Allow ECS tasks to read application secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "${aws_secretsmanager_secret.app_secrets.arn}*"
      }
    ]
  })
}

# Attach the app secrets policy to the ECS task role (where the app runs)
resource "aws_iam_role_policy_attachment" "ecs_task_app_secrets" {
  role       = basename(var.ecs_task_role_name) # Extract role name from ARN
  policy_arn = aws_iam_policy.ecs_app_secrets_access.arn

  depends_on = [
    aws_iam_policy.ecs_app_secrets_access,
    aws_secretsmanager_secret.app_secrets
  ]
}

# Attach the app secrets policy to the ECS task execution role (for ECS to retrieve secrets at startup)
resource "aws_iam_role_policy_attachment" "ecs_task_execution_app_secrets" {
  role       = basename(var.ecs_task_execution_role_name) # Extract role name from ARN
  policy_arn = aws_iam_policy.ecs_app_secrets_access.arn

  depends_on = [
    aws_iam_policy.ecs_app_secrets_access,
    aws_secretsmanager_secret.app_secrets
  ]
}
