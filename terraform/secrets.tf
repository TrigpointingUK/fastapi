# AWS Secrets Manager for external database configuration (production)
resource "aws_secretsmanager_secret" "external_database" {
  count = var.use_external_database ? 1 : 0

  name        = var.external_database_secret_name
  description = "External database connection URL for ${var.environment} environment"

  tags = {
    Name        = "${var.project_name}-${var.environment}-external-db-secret"
    Environment = var.environment
    Purpose     = "External Database URL"
  }
}

# Secret version with placeholder value (you'll update this manually)
resource "aws_secretsmanager_secret_version" "external_database" {
  count = var.use_external_database ? 1 : 0

  secret_id = aws_secretsmanager_secret.external_database[0].id
  secret_string = jsonencode({
    database_url = "mysql+pymysql://username:password@hostname:3306/database_name"
  })

  # Ignore changes to secret string after initial creation
  # This allows manual updates via AWS Console/CLI without Terraform interference
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM policy for ECS tasks to read the external database secret
resource "aws_iam_policy" "ecs_secrets_access" {
  count = var.use_external_database ? 1 : 0

  name        = "${var.project_name}-${var.environment}-ecs-secrets-access"
  description = "Allow ECS tasks to read external database secret"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.external_database[0].arn
      }
    ]
  })
}

# Attach the secrets policy to the ECS task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_secrets" {
  count = var.use_external_database ? 1 : 0

  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.ecs_secrets_access[0].arn
}
