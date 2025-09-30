output "phpmyadmin_service_name" {
  description = "phpMyAdmin ECS service name"
  value       = aws_ecs_service.phpmyadmin.name
}

output "phpmyadmin_task_definition_arn" {
  description = "phpMyAdmin ECS task definition ARN"
  value       = aws_ecs_task_definition.phpmyadmin.arn
}

output "phpmyadmin_log_group_name" {
  description = "phpMyAdmin CloudWatch log group name"
  value       = aws_cloudwatch_log_group.phpmyadmin.name
}
