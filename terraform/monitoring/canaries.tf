# CloudWatch Synthetics canaries for uptime and login checks

locals {
  # Use recommended runtime
  canary_runtime = "syn-nodejs-puppeteer-11.0"
}
data "archive_file" "health_check" {
  type        = "zip"
  source_file = "${path.module}/scripts/health_check.js"
  output_path = "${path.module}/scripts/health_check.zip"
}

resource "aws_s3_object" "health_check_src" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/health_check.zip"
  source = data.archive_file.health_check.output_path
  etag   = filemd5(data.archive_file.health_check.output_path)
}

resource "aws_synthetics_canary" "api_health" {
  name                 = "${var.project_name}-${var.environment}-api-health"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canaries/api-health/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "health_check.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.health_check_src.key
  s3_version           = aws_s3_object.health_check_src.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 20
    environment_variables = {
      TARGET_URL          = var.environment == "production" ? "https://api.trigpointing.uk/health" : "https://api.trigpointing.me/health"
      EXPECTED_ENVIRONMENT = var.environment
      USER_AGENT          = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH           = data.archive_file.health_check.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "api-health"
  }
}

data "archive_file" "api_json_contains" {
  type        = "zip"
  source_file = "${path.module}/scripts/api_json_contains.js"
  output_path = "${path.module}/scripts/api_json_contains.zip"
}

data "archive_file" "html_contains" {
  type        = "zip"
  source_file = "${path.module}/scripts/html_contains.js"
  output_path = "${path.module}/scripts/html_contains.zip"
}

data "archive_file" "login_and_me" {
  type        = "zip"
  source_file = "${path.module}/scripts/login_and_me.js"
  output_path = "${path.module}/scripts/login_and_me.zip"
}

# Upload canary source zips to S3 so Synthetics can fetch reliably
resource "aws_s3_object" "api_json_contains_src" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/api_json_contains.zip"
  source = data.archive_file.api_json_contains.output_path
  etag   = filemd5(data.archive_file.api_json_contains.output_path)
}

resource "aws_s3_object" "html_contains_src" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/html_contains.zip"
  source = data.archive_file.html_contains.output_path
  etag   = filemd5(data.archive_file.html_contains.output_path)
}

resource "aws_s3_object" "login_and_me_src" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  key    = "sources/login_and_me.zip"
  source = data.archive_file.login_and_me.output_path
  etag   = filemd5(data.archive_file.login_and_me.output_path)
}

resource "aws_synthetics_canary" "api_trig_1" {
  name                 = "${var.project_name}-${var.environment}-api-trig-1"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canaries/api-trig-1/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "api_json_contains.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.api_json_contains_src.key
  s3_version           = aws_s3_object.api_json_contains_src.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 30
    environment_variables = {
      EXPECTED_SUBSTRING = "\"name\":\"Fetlar\""
      TARGET_URL         = "https://api.trigpointing.uk/api/v1/trig/1"
      USER_AGENT         = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH          = data.archive_file.api_json_contains.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "api-json"
  }
}

resource "aws_synthetics_canary" "web_trig_1" {
  name                 = "${var.project_name}-${var.environment}-web-trig-1"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canaries/web-trig-1/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "html_contains.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.html_contains_src.key
  s3_version           = aws_s3_object.html_contains_src.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 30
    environment_variables = {
      EXPECTED_SUBSTRING = "Fetlar"
      TARGET_URL         = "https://trigpointing.uk/trig/1"
      USER_AGENT         = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH          = data.archive_file.html_contains.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "web-html"
  }
}

resource "aws_synthetics_canary" "login_me" {
  name                 = "${var.project_name}-${var.environment}-api-login-me"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts.bucket}/canaries/api-login-me/"
  execution_role_arn   = aws_iam_role.canary_role.arn
  handler              = "login_and_me.handler"
  runtime_version      = local.canary_runtime
  s3_bucket            = aws_s3_bucket.synthetics_artifacts.bucket
  s3_key               = aws_s3_object.login_and_me_src.key
  s3_version           = aws_s3_object.login_and_me_src.version_id
  start_canary         = true
  schedule {
    expression = "rate(1 minute)"
  }
  run_config {
    timeout_in_seconds = 45
    environment_variables = {
      LOGIN_URL = "https://api.trigpointing.uk/api/v1/auth/login"
      ME_URL    = "https://api.trigpointing.uk/api/v1/user/me"
      # Provide credentials via env vars to avoid bundling SDK
      USERNAME  = local.tuk_guest_parsed.username
      PASSWORD  = local.tuk_guest_parsed.password
      LEGACY_USER_ID = tostring(local.tuk_guest_parsed.legacy_userid)
      USER_AGENT = "Trigpointing-canary/1.0 (+https://trigpointing.uk)"
      CODE_HASH = data.archive_file.login_and_me.output_base64sha256
    }
  }
  failure_retention_period = 31
  success_retention_period = 7
  tags = {
    CheckType = "api-login"
  }
}
