output "service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.mediawiki.name
}

output "service_id" {
  description = "ID of the ECS service"
  value       = aws_ecs_service.mediawiki.id
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = aws_ecs_task_definition.mediawiki.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.mediawiki.name
}
