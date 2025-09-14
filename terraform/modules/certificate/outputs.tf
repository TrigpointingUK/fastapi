output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = var.enable_cloudflare_ssl ? aws_acm_certificate.cloudflare_origin[0].arn : null
}
