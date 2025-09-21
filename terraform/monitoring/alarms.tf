# Alarms: trigger if 3 consecutive failures; notify OK as well

locals {
  alarm_eval_periods = 1
  alarm_period_sec   = 3600
}

resource "aws_cloudwatch_metric_alarm" "api_trig_1" {
  alarm_name          = "fastapi-${var.environment}-api-trig-1"
  alarm_description   = "API trig/1 canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.api_trig_1.name
  }
  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.alerts.arn]
  ok_actions         = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "web_trig_1" {
  count                = var.environment == "production" ? 1 : 0
  alarm_name          = "fastapi-${var.environment}-web-trig-1"
  alarm_description   = "Web trig/1 canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.web_trig_1[0].name
  }
  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.alerts.arn]
  ok_actions         = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "user_profile" {
  alarm_name          = "fastapi-${var.environment}-api-user-profile"
  alarm_description   = "Login / get profile canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.user_profile.name
  }
  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.alerts.arn]
  ok_actions         = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "api_health" {
  alarm_name          = "fastapi-${var.environment}-health"
  alarm_description   = "Health environment canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.api_health.name
  }
  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.alerts.arn]
  ok_actions         = [aws_sns_topic.alerts.arn]
}
