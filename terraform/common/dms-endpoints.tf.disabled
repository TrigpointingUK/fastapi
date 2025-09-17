# DMS Endpoints for Staging and Production Users
# These reference the credentials from the mysql directory via remote state

# Data source for mysql remote state
data "terraform_remote_state" "mysql" {
  backend = "s3"
  config = {
    bucket = "tuk-terraform-state"
    key    = "fastapi-mysql/terraform.tfstate"
    region = "eu-west-1"
  }
}

# Data sources for secret values
data "aws_secretsmanager_secret_version" "staging_credentials" {
  secret_id = data.terraform_remote_state.mysql.outputs.staging_credentials_arn
}

data "aws_secretsmanager_secret_version" "production_credentials" {
  secret_id = data.terraform_remote_state.mysql.outputs.production_credentials_arn
}

# DMS Endpoint for Staging User
resource "aws_dms_endpoint" "staging_user" {
  endpoint_id   = "${var.project_name}-staging-user"
  endpoint_type = "target"
  engine_name   = "mysql"
  server_name   = split(":", aws_db_instance.main.endpoint)[0]
  port          = aws_db_instance.main.port
  username      = "fastapi_staging"
  password      = jsondecode(data.aws_secretsmanager_secret_version.staging_credentials.secret_string)["password"]
  database_name = "tuk_staging"
  ssl_mode      = "none"

  tags = {
    Name        = "${var.project_name}-staging-user"
    Environment = "staging"
    User        = "fastapi_staging"
  }
}

# DMS Endpoint for Production User
resource "aws_dms_endpoint" "production_user" {
  endpoint_id   = "${var.project_name}-production-user"
  endpoint_type = "target"
  engine_name   = "mysql"
  server_name   = split(":", aws_db_instance.main.endpoint)[0]
  port          = aws_db_instance.main.port
  username      = "fastapi_production"
  password      = jsondecode(data.aws_secretsmanager_secret_version.production_credentials.secret_string)["password"]
  database_name = "tuk_production"
  ssl_mode      = "none"

  tags = {
    Name        = "${var.project_name}-production-user"
    Environment = "production"
    User        = "fastapi_production"
  }
}
