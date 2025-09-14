# CloudFlare Origin Certificate
resource "aws_acm_certificate" "cloudflare_origin" {
  count            = var.enable_cloudflare_ssl ? 1 : 0
  certificate_body = var.cloudflare_origin_cert
  private_key      = var.cloudflare_origin_key

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cloudflare-cert"
    Type        = "CloudFlare Origin Certificate"
    Environment = var.environment
    Domain      = var.domain_name
  }
}

# Attach certificate to existing HTTPS listener
# All environments add their certificates as additional certificates
resource "aws_lb_listener_certificate" "additional" {
  count           = var.enable_cloudflare_ssl ? 1 : 0
  listener_arn    = var.listener_arn
  certificate_arn = aws_acm_certificate.cloudflare_origin[0].arn
}
