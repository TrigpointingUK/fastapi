# Random passwords for all users
resource "random_password" "admin_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

resource "random_password" "production_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

resource "random_password" "staging_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

resource "random_password" "backups_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

# Admin user credentials in Secrets Manager with auto-rotation
resource "aws_secretsmanager_secret" "admin_credentials" {
  name                    = "${var.project_name}-admin-credentials"
  description            = "Admin user credentials for RDS with auto-rotation"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-admin-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "admin_credentials" {
  secret_id = aws_secretsmanager_secret.admin_credentials.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.admin_password.result
  })
}

# Auto-rotation for admin credentials
resource "aws_secretsmanager_secret_rotation" "admin_credentials" {
  secret_id           = aws_secretsmanager_secret.admin_credentials.id
  rotation_lambda_arn = aws_lambda_function.rotation_lambda.arn

  rotation_rules {
    automatically_after_days = 30
  }
}

# Production user credentials (manual rotation)
resource "aws_secretsmanager_secret" "production_credentials" {
  name                    = "${var.project_name}-production-credentials"
  description            = "Production user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-production-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "production_credentials" {
  secret_id = aws_secretsmanager_secret.production_credentials.id
  secret_string = jsonencode({
    username = "fastapi_production"
    password = random_password.production_password.result
  })
}

# Staging user credentials (manual rotation)
resource "aws_secretsmanager_secret" "staging_credentials" {
  name                    = "${var.project_name}-staging-credentials"
  description            = "Staging user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-staging-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "staging_credentials" {
  secret_id = aws_secretsmanager_secret.staging_credentials.id
  secret_string = jsonencode({
    username = "fastapi_staging"
    password = random_password.staging_password.result
  })
}

# Backups user credentials (manual rotation)
resource "aws_secretsmanager_secret" "backups_credentials" {
  name                    = "${var.project_name}-backups-credentials"
  description            = "Backups user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-backups-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "backups_credentials" {
  secret_id = aws_secretsmanager_secret.backups_credentials.id
  secret_string = jsonencode({
    username = "backups"
    password = random_password.backups_password.result
  })
}

# Lambda function for secret rotation
resource "aws_lambda_function" "rotation_lambda" {
  filename         = "rotation_lambda.zip"
  function_name    = "${var.project_name}-secret-rotation"
  role            = aws_iam_role.lambda_rotation.arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      SECRET_ARN = aws_secretsmanager_secret.admin_credentials.arn
    }
  }

  tags = {
    Name = "${var.project_name}-secret-rotation"
  }
}

# Lambda permission for Secrets Manager
resource "aws_lambda_permission" "allow_secrets_manager" {
  statement_id  = "AllowExecutionFromSecretsManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rotation_lambda.function_name
  principal     = "secretsmanager.amazonaws.com"
}

# IAM role for Lambda rotation
resource "aws_iam_role" "lambda_rotation" {
  name = "${var.project_name}-lambda-rotation-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-lambda-rotation-role"
  }
}

# IAM policy for Lambda rotation
resource "aws_iam_role_policy" "lambda_rotation" {
  name = "${var.project_name}-lambda-rotation-policy"
  role = aws_iam_role.lambda_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = aws_secretsmanager_secret.admin_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:ModifyDBInstance"
        ]
        Resource = aws_db_instance.main.arn
      }
    ]
  })
}
