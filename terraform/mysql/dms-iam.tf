# IAM role for DMS to access legacy credentials secret
resource "aws_iam_role" "dms_secret_access" {
  name = "${var.project_name}-dms-secret-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "dms.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-dms-secret-access"
  }
}

# IAM policy for DMS to access the legacy credentials secret
resource "aws_iam_policy" "dms_secret_access" {
  name        = "${var.project_name}-dms-secret-access"
  description = "Policy for DMS to access legacy credentials secret"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.legacy_credentials.arn
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-dms-secret-access"
  }
}

# Attach the policy to the DMS role
resource "aws_iam_role_policy_attachment" "dms_secret_access" {
  role       = aws_iam_role.dms_secret_access.name
  policy_arn = aws_iam_policy.dms_secret_access.arn
}
