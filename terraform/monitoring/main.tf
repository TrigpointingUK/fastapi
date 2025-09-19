terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    # Backend configuration will be provided via backend.conf
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Component   = "monitoring"
    }
  }
}

# Reference common stack for VPC/roles if needed
data "terraform_remote_state" "common" {
  backend = "s3"
  config = {
    bucket = "tuk-terraform-state"
    key    = "fastapi-common-eu-west-1/terraform.tfstate"
    region = "eu-west-1"
  }
}

# S3 bucket for Synthetics artifacts (scripts, results)
resource "aws_s3_bucket" "synthetics_artifacts" {
  bucket = "${var.project_name}-${var.environment}-synthetics-artifacts"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "synthetics_artifacts" {
  bucket = aws_s3_bucket.synthetics_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# SNS topic for alarms
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-monitoring-alerts"
}

# Optional: AWS Chatbot Slack integration (Slack channel must be pre-authorised)
resource "aws_iam_role" "chatbot" {
  count              = var.enable_slack_notifications ? 1 : 0
  name               = "${var.project_name}-${var.environment}-chatbot-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "chatbot.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "chatbot_readonly" {
  count      = var.enable_slack_notifications ? 1 : 0
  role       = aws_iam_role.chatbot[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_chatbot_slack_channel_configuration" "slack" {
  count               = var.enable_slack_notifications ? 1 : 0
  configuration_name  = "${var.project_name}-${var.environment}-slack"
  slack_channel_id    = var.slack_channel_id
  slack_team_id       = var.slack_workspace_id
  iam_role_arn        = aws_iam_role.chatbot[0].arn
  sns_topic_arns      = [aws_sns_topic.alerts.arn]
  logging_level       = "ERROR"
}

# IAM role for CloudWatch Synthetics canaries
data "aws_iam_policy_document" "canary_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com", "synthetics.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "canary_role" {
  name               = "${var.project_name}-${var.environment}-synthetics-role"
  assume_role_policy = data.aws_iam_policy_document.canary_assume.json
}

resource "aws_iam_role_policy_attachment" "canary_lambda_basic" {
  role       = aws_iam_role.canary_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "canary_policy" {
  name = "${var.project_name}-${var.environment}-synthetics-inline"
  role = aws_iam_role.canary_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetBucketLocation",
          "s3:ListAllMyBuckets",
          "s3:ListBucket",
          "s3:GetObject"
        ],
        Resource = [
          aws_s3_bucket.synthetics_artifacts.arn,
          "${aws_s3_bucket.synthetics_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ],
        Resource = "*"
      }
    ]
  })
}
