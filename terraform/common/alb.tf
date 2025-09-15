# Application Load Balancer (shared between staging and production)
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "fastapi-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # HTTP access (only when CloudFlare SSL is disabled - for testing)
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

  # HTTPS access (only when CloudFlare SSL is enabled)
  dynamic "ingress" {
    for_each = var.enable_cloudflare_ssl ? [1] : []
    content {
      description = "HTTPS from CloudFlare"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = [
        "173.245.48.0/20",
        "103.21.244.0/22",
        "103.22.200.0/22",
        "103.31.4.0/22",
        "141.101.64.0/18",
        "108.162.192.0/18",
        "190.93.240.0/20",
        "188.114.96.0/20",
        "197.234.240.0/22",
        "198.41.128.0/17",
        "162.158.0.0/15",
        "104.16.0.0/13",
        "104.24.0.0/14",
        "172.64.0.0/13",
        "131.0.72.0/22"
      ]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fastapi-alb-sg"
  }
}

# Note: HTTPS listeners are now managed by individual environment modules
# (staging and production) to support multiple certificates and host-based routing

# HTTP Listener (only when CloudFlare SSL is disabled - for testing)
resource "aws_lb_listener" "app_http" {
  count             = var.enable_cloudflare_ssl ? 0 : 1
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "No target group configured"
      status_code  = "503"
    }
  }

  tags = {
    Name = "${var.project_name}-http-listener"
  }
}
