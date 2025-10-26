output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.nginx_proxy.name
}

output "ecs_service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.nginx_proxy.id
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.nginx_proxy.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.nginx_proxy.name
}

