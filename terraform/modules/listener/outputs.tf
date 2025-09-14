output "listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = var.enable_cloudflare_ssl ? aws_lb_listener.app_https[0].arn : null
}

output "certificate_arn" {
  description = "ARN of the CloudFlare origin certificate"
  value       = var.enable_cloudflare_ssl ? aws_acm_certificate.cloudflare_origin[0].arn : null
}
