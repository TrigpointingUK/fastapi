# AWS Systems Manager Parameter Store Configuration
# This file manages application configuration parameters

# X-Ray Configuration Parameters
resource "aws_ssm_parameter" "xray_enabled" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/xray/enabled"
  type  = "String"
  value = var.xray_enabled ? "true" : "false"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "xray-config"
  }
}

resource "aws_ssm_parameter" "xray_service_name" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/xray/service_name"
  type  = "String"
  value = var.xray_service_name

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "xray-config"
  }
}

resource "aws_ssm_parameter" "xray_sampling_rate" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/xray/sampling_rate"
  type  = "String"
  value = tostring(var.xray_sampling_rate)

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "xray-config"
  }
}

resource "aws_ssm_parameter" "xray_daemon_address" {
  count = var.enable_parameter_store && var.xray_daemon_address != null ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/xray/daemon_address"
  type  = "String"
  value = var.xray_daemon_address

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "xray-config"
  }
}

# Application Configuration Parameters
resource "aws_ssm_parameter" "log_level" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/app/log_level"
  type  = "String"
  value = var.log_level

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "app-config"
  }
}

resource "aws_ssm_parameter" "cors_origins" {
  count = var.enable_parameter_store && var.cors_origins != null ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/app/cors_origins"
  type  = "String"
  value = var.cors_origins

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "app-config"
  }
}

# Database Configuration Parameters (non-sensitive)
resource "aws_ssm_parameter" "db_pool_size" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/database/pool_size"
  type  = "String"
  value = tostring(var.db_pool_size)

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "db-config"
  }
}

resource "aws_ssm_parameter" "db_pool_recycle" {
  count = var.enable_parameter_store ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/database/pool_recycle"
  type  = "String"
  value = tostring(var.db_pool_recycle)

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Component   = "parameter-store"
    Purpose     = "db-config"
  }
}
