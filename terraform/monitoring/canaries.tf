# CloudWatch Synthetics canaries for uptime and login checks

locals {
  # Use recommended runtime
  canary_runtime = "syn-nodejs-puppeteer-11.0"
  api_url_base   = var.environment == "production" ? "https://api.trigpointing.uk" : "https://api.trigpointing.me"
  web_url_base   = var.environment == "production" ? "https://trigpointing.uk" : "https://trigpointing.me"
  s3_base_path   = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/${var.environment}/canaries"
}


# resource "aws_synthetics_canary" "api_health" {
#   name                 = "${var.project_name}-${var.environment}-api-health"
#   artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/${var.environment}/canaries/api-health/"
#   execution_role_arn   = aws_iam_role.canary_role.arn
#   handler              = "api_health.handler"
#   runtime_version      = local.canary_runtime
#   s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
#   s3_key               = aws_s3_object.api_health.key
#   s3_version           = aws_s3_object.api_health.version_id
#   start_canary         = true
#   schedule {
#     expression = "rate(1 minute)"
#   }
#   run_config {
#     timeout_in_seconds = 20
#     environment_variables = {
#       TARGET_URL           = "${local.url_base}/health"
#       EXPECTED_ENVIRONMENT = var.environment
#       USER_AGENT           = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
#       CODE_HASH            = data.archive_file.api_health.output_base64sha256
#     }
#   }
#   failure_retention_period = 31
#   success_retention_period = 7
#   tags = {
#     CheckType = "api-health"
#   }
# }
# data "archive_file" "api_health" {
#   type        = "zip"
#   source_file = "${path.module}/scripts/api_health.js"
#   output_path = "${path.module}/scripts/api_health.zip"
# }
# resource "aws_s3_object" "api_health" {
#   bucket = aws_s3_bucket.synthetics_artifacts.id
#   key    = "sources/api_health.zip"
#   source = data.archive_file.api_health.output_path
#   etag   = filemd5(data.archive_file.api_health.output_path)
# }




resource "aws_synthetics_canary" "api_trig_1" {
  name                 = "fastapi-${var.environment}-api-trig-1"
  artifact_s3_location = "${local.s3_base_path}/api-trig-1/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "json_contains.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.json_contains.key
  s3_version           = aws_s3_object.json_contains.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 30
    environment_variables = {
      EXPECTED_SUBSTRING = "\"name\":\"Fetlar\""
      TARGET_URL         = "${local.api_url_base}/api/v1/trig/1"
      USER_AGENT         = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH          = data.archive_file.json_contains.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "json-contains"
  }
}



resource "aws_synthetics_canary" "web_trig_1" {
  count                = var.environment == "production" ? 1 : 0
  name                 = "fastapi-${var.environment}-web-trig-1"
  artifact_s3_location = "${local.s3_base_path}/web-trig-1/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "html_contains.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.html_contains.key
  s3_version           = aws_s3_object.html_contains.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 30
    environment_variables = {
      EXPECTED_SUBSTRING = "Fetlar"
      TARGET_URL         = "${local.web_url_base}/trig/1"
      USER_AGENT         = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH          = data.archive_file.html_contains.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "html-contains"
  }
}



# data "archive_file" "web_trig_1" {
#   type        = "zip"
#   source_file = "${path.module}/scripts/web_trig_1.js"
#   output_path = "${path.module}/scripts/web_trig_1.zip"
# }
# resource "aws_s3_object" "web_trig_1" {
#   bucket = aws_s3_bucket.synthetics_artifacts.id
#   key    = "sources/web_trig_1.zip"
#   source = data.archive_file.web_trig_1.output_path
#   etag   = filemd5(data.archive_file.web_trig_1.output_path)
# }


# resource "aws_synthetics_canary" "user_profile" {
#   name                 = "${var.project_name}-${var.environment}-api-user-profile"
#   artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canaries/api-user-profile/"
#   execution_role_arn   = aws_iam_role.canary_role.arn
#   handler              = "user_profile.handler"
#   runtime_version      = local.canary_runtime
#   s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
#   s3_key               = aws_s3_object.user_profile.key
#   s3_version           = aws_s3_object.user_profile.version_id
#   start_canary         = true
#   schedule {
#     expression = "rate(1 minute)"
#   }
#   run_config {
#     timeout_in_seconds = 45
#     environment_variables = {
#       LOGIN_URL = "${local.url_base}/api/v1/auth/login"
#       ME_URL    = "${local.url_base}/api/v1/user/me"
#       # Provide credentials via env vars to avoid bundling SDK
#       USERNAME       = local.tuk_guest_parsed.username
#       PASSWORD       = local.tuk_guest_parsed.password
#       LEGACY_USER_ID = tostring(local.tuk_guest_parsed.legacy_userid)
#       USER_AGENT     = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
#       CODE_HASH      = data.archive_file.user_profile.output_base64sha256
#     }
#   }
#   failure_retention_period = 31
#   success_retention_period = 7
#   tags = {
#     CheckType = "api-login"
#   }
# }
# data "archive_file" "user_profile" {
#   type        = "zip"
#   source_file = "${path.module}/scripts/user_profile.js"
#   output_path = "${path.module}/scripts/user_profile.zip"
# }
# resource "aws_s3_object" "user_profile" {
#   bucket = aws_s3_bucket.synthetics_artifacts.id
#   key    = "sources/user_profile.zip"
#   source = data.archive_file.user_profile.output_path
#   etag   = filemd5(data.archive_file.user_profile.output_path)
# }




data "archive_file" "json_contains" {
  type        = "zip"
  source_file = "${path.module}/scripts/json_contains.js"
  output_path = "${path.module}/scripts/json_contains.zip"
}
resource "aws_s3_object" "json_contains" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/json_contains.zip"
  source = data.archive_file.json_contains.output_path
  etag   = filemd5(data.archive_file.json_contains.output_path)
}


data "archive_file" "html_contains" {
  type        = "zip"
  source_file = "${path.module}/scripts/html_contains.js"
  output_path = "${path.module}/scripts/html_contains.zip"
}
resource "aws_s3_object" "html_contains" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/html_contains.zip"
  source = data.archive_file.html_contains.output_path
  etag   = filemd5(data.archive_file.html_contains.output_path)
}
