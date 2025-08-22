# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-tg"
  }
}

# No HTTP listener - CloudFlare handles HTTP->HTTPS redirects at edge
# Origin server only accepts HTTPS traffic from CloudFlare

# CloudFlare Origin Certificate
resource "aws_acm_certificate" "cloudflare_origin" {
  count           = var.enable_cloudflare_ssl ? 1 : 0
  certificate_body = var.cloudflare_origin_cert
  private_key     = var.cloudflare_origin_key

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cloudflare-cert"
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
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-https-listener"
  }
}

# HTTP Listener (only when CloudFlare SSL is disabled - for staging/testing)
resource "aws_lb_listener" "app_http" {
  count             = var.enable_cloudflare_ssl ? 0 : 1
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-http-listener"
  }
}

# Note: When CloudFlare SSL is enabled, HTTP listener is not created
# CloudFlare handles HTTP->HTTPS redirects at the edge for security
