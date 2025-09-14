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
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from CloudFlare"
    from_port   = 80
    to_port     = 80
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

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# CloudFlare Origin Certificate
resource "aws_acm_certificate" "cloudflare_origin" {
  count           = var.enable_cloudflare_ssl ? 1 : 0
  certificate_body = var.cloudflare_origin_cert
  private_key     = var.cloudflare_origin_key

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-cloudflare-cert"
    Type = "CloudFlare Origin Certificate"
  }
}

# HTTPS Listener with CloudFlare Origin Certificate
resource "aws_lb_listener" "app_https" {
  count             = var.enable_cloudflare_ssl ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.cloudflare_origin[0].arn

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "No target group configured"
      status_code  = "503"
    }
  }

  tags = {
    Name = "${var.project_name}-https-listener"
  }
}

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
