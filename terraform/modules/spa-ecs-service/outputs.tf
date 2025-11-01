output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.spa.name
}

output "service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.spa.id
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.spa.arn
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.spa.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.spa.name
}

