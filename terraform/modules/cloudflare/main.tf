# Data source for CloudFlare IP ranges
data "http" "cloudflare_ips_v4" {
  url = "https://www.cloudflare.com/ips-v4"
}

locals {
  # Parse CloudFlare IP ranges from their public API
  cloudflare_ips_v4 = split("\n", chomp(data.http.cloudflare_ips_v4.response_body))

  # CloudFlare IPv4 ranges (fallback if API fails)
  cloudflare_ips_fallback = [
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "108.162.192.0/18",
    "131.0.72.0/22",
    "141.101.64.0/18",
    "162.158.0.0/15",
    "172.64.0.0/13",
    "173.245.48.0/20",
    "188.114.96.0/20",
    "190.93.240.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17"
  ]

  # Use API results if available, otherwise fallback
  cloudflare_ips = length(local.cloudflare_ips_v4) > 0 ? local.cloudflare_ips_v4 : local.cloudflare_ips_fallback
}

# Security Group for ALB with CloudFlare IP restrictions
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  # HTTPS access - only when CloudFlare SSL is enabled
  dynamic "ingress" {
    for_each = var.enable_cloudflare_ssl ? [1] : []
    content {
      description = "HTTPS from CloudFlare"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = local.cloudflare_ips
    }
  }

  # HTTP access - only when CloudFlare SSL is disabled
  dynamic "ingress" {
    for_each = var.enable_cloudflare_ssl ? [] : [1]
    content {
      description = "HTTP access"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

# Security Group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-tasks-sg"
  }
}
