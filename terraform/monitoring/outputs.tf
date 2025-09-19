output "synthetics_artifacts_bucket" {
  value       = aws_s3_bucket.synthetics_artifacts.bucket
  description = "Bucket used by Synthetics canaries for artifacts"
}

output "alerts_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "SNS topic for monitoring alerts"
}
