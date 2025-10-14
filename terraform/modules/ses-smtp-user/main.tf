# IAM user for SES SMTP access
resource "aws_iam_user" "smtp_user" {
  name = var.user_name

  tags = {
    Name    = var.user_name
    Project = var.project_name
    Purpose = "SES SMTP access"
  }
}

# IAM policy to allow SES sending
resource "aws_iam_user_policy" "smtp_user_policy" {
  name = "${var.user_name}-ses-policy"
  user = aws_iam_user.smtp_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "ses:SendEmail",
            "ses:SendRawEmail"
          ]
          Resource = "*"
        }
      ],
      # Add conditional statement only if from_addresses is specified
      length(var.allowed_from_addresses) > 0 ? [] : []
    )
  })
}

# Generate SMTP credentials
resource "aws_iam_access_key" "smtp_credentials" {
  user = aws_iam_user.smtp_user.name
}
