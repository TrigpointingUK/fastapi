output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs_tasks.id
}

output "cloudflare_ip_ranges" {
  description = "CloudFlare IP ranges allowed to access ALB"
  value       = local.cloudflare_ips
}
