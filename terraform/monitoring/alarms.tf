# Alarms: trigger if 3 consecutive failures; notify OK as well

locals {
  alarm_eval_periods = 3
  alarm_period_sec   = 60
}

resource "aws_cloudwatch_metric_alarm" "api_trig_1_failed" {
  alarm_name          = "${var.project_name}-${var.environment}-api-trig-1-failed"
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
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "web_trig_1_failed" {
  alarm_name          = "${var.project_name}-${var.environment}-web-trig-1-failed"
  alarm_description   = "Web trig/1 canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.web_trig_1.name
  }
  treat_missing_data = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "login_me_failed" {
  alarm_name          = "${var.project_name}-${var.environment}-api-login-me-failed"
  alarm_description   = "Login/me canary failed 3x consecutively"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = local.alarm_eval_periods
  threshold           = 1
  metric_name         = "Failed"
  namespace           = "CloudWatchSynthetics"
  statistic           = "Maximum"
  period              = local.alarm_period_sec
  dimensions = {
    CanaryName = aws_synthetics_canary.login_me.name
  }
  treat_missing_data = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}
