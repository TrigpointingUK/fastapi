# Reference existing guest user secret without managing it
data "aws_secretsmanager_secret" "tuk_guest" {
  name = var.tuk_guest_secret_name
}

data "aws_secretsmanager_secret_version" "tuk_guest" {
  secret_id = data.aws_secretsmanager_secret.tuk_guest.id
}

locals {
  tuk_guest_parsed = try(jsondecode(data.aws_secretsmanager_secret_version.tuk_guest.secret_string), {})
}

# Allow canaries to read the secret
resource "aws_iam_role_policy_attachment" "canary_secret_access" {
  role       = aws_iam_role.canary_role.name
  policy_arn = aws_iam_policy.canary_secret_access.arn
}

resource "aws_iam_policy" "canary_secret_access" {
  name        = "${var.project_name}-${var.environment}-synthetics-secrets-access"
  description = "Allow Synthetics canaries to read required secrets"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Resource = concat([
          data.aws_secretsmanager_secret.tuk_guest.arn
        ], var.additional_allowed_secret_arns)
      }
    ]
  })
}
