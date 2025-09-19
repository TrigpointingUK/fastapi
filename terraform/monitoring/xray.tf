# AWS X-Ray Configuration
# This file contains resources for X-Ray tracing and sampling rules

# X-Ray sampling rule for the API service
resource "aws_xray_sampling_rule" "api_sampling" {
  rule_name      = "trigpointing-api-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 100
  fixed_rate     = var.xray_sampling_rate
  url_path       = "/api/*"
  host           = "api.trigpointing.uk"
  http_method    = "*"
  service_type   = "*"
  service_name   = "trigpointing-api"
  resource_arn   = "*"

  tags = {
    Component = "monitoring"
    Purpose   = "xray-sampling"
  }
}

# X-Ray sampling rule for the web service
resource "aws_xray_sampling_rule" "web_sampling" {
  rule_name      = "trigpointing-web-sampling"
  priority       = 1001
  version        = 1
  reservoir_size = 50
  fixed_rate     = var.xray_sampling_rate
  url_path       = "/*"
  host           = "trigpointing.uk"
  http_method    = "*"
  service_type   = "*"
  service_name   = "trigpointing-web"
  resource_arn   = "*"

  tags = {
    Component = "monitoring"
    Purpose   = "xray-sampling"
  }
}

# IAM role for X-Ray daemon (if running on EC2)
resource "aws_iam_role" "xray_daemon" {
  count = var.enable_xray_daemon_role ? 1 : 0
  name  = "${var.project_name}-${var.environment}-xray-daemon-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Component = "monitoring"
    Purpose   = "xray-daemon"
  }
}

# Attach X-Ray daemon policy to the role
resource "aws_iam_role_policy_attachment" "xray_daemon" {
  count      = var.enable_xray_daemon_role ? 1 : 0
  role       = aws_iam_role.xray_daemon[0].name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# Instance profile for X-Ray daemon (if running on EC2)
resource "aws_iam_instance_profile" "xray_daemon" {
  count = var.enable_xray_daemon_role ? 1 : 0
  name  = "${var.project_name}-${var.environment}-xray-daemon-profile"
  role  = aws_iam_role.xray_daemon[0].name

  tags = {
    Component = "monitoring"
    Purpose   = "xray-daemon"
  }
}

# CloudWatch Log Group for X-Ray daemon logs
resource "aws_cloudwatch_log_group" "xray_daemon" {
  count             = var.enable_xray_daemon_logs ? 1 : 0
  name              = "/aws/xray/daemon"
  retention_in_days = var.log_retention_days

  tags = {
    Component = "monitoring"
    Purpose   = "xray-daemon-logs"
  }
}

# X-Ray group for API traces
resource "aws_xray_group" "api_group" {
  group_name        = "${var.project_name}-${var.environment}-api"
  filter_expression = "service(\"trigpointing-api\")"

  tags = {
    Component = "monitoring"
    Purpose   = "xray-group"
  }
}

# X-Ray group for web traces
resource "aws_xray_group" "web_group" {
  group_name        = "${var.project_name}-${var.environment}-web"
  filter_expression = "service(\"trigpointing-web\")"

  tags = {
    Component = "monitoring"
    Purpose   = "xray-group"
  }
}

# X-Ray group for database traces
resource "aws_xray_group" "database_group" {
  group_name        = "${var.project_name}-${var.environment}-database"
  filter_expression = "service(\"trigpointing-database\")"

  tags = {
    Component = "monitoring"
    Purpose   = "xray-group"
  }
}
