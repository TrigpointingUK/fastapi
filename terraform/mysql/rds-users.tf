# Random passwords for application users

resource "random_password" "production_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

resource "random_password" "staging_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

resource "random_password" "backups_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
  min_special = 1
  min_upper = 1
  min_lower = 1
  min_numeric = 1
}

# Note: Admin user credentials are managed by the RDS instance itself
# and stored in the common infrastructure. Use those for database administration.

# Production user credentials (manual rotation)
resource "aws_secretsmanager_secret" "production_credentials" {
  name                    = "${var.project_name}-production-credentials"
  description            = "Production user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-production-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "production_credentials" {
  secret_id = aws_secretsmanager_secret.production_credentials.id
  secret_string = jsonencode({
    username                = "fastapi_production"
    password                = random_password.production_password.result
    engine                  = "mysql"
    host                    = data.terraform_remote_state.common.outputs.rds_endpoint
    port                    = data.terraform_remote_state.common.outputs.rds_port
    dbname                  = "tuk_production"
    dbInstanceIdentifier    = data.terraform_remote_state.common.outputs.rds_identifier
  })
}

# Staging user credentials (manual rotation)
resource "aws_secretsmanager_secret" "staging_credentials" {
  name                    = "${var.project_name}-staging-credentials"
  description            = "Staging user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-staging-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "staging_credentials" {
  secret_id = aws_secretsmanager_secret.staging_credentials.id
  secret_string = jsonencode({
    username                = "fastapi_staging"
    password                = random_password.staging_password.result
    engine                  = "mysql"
    host                    = data.terraform_remote_state.common.outputs.rds_endpoint
    port                    = data.terraform_remote_state.common.outputs.rds_port
    dbname                  = "tuk_staging"
    dbInstanceIdentifier    = data.terraform_remote_state.common.outputs.rds_identifier
  })
}

# Backups user credentials (manual rotation)
resource "aws_secretsmanager_secret" "backups_credentials" {
  name                    = "${var.project_name}-backups-credentials"
  description            = "Backups user credentials for RDS"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.project_name}-backups-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "backups_credentials" {
  secret_id = aws_secretsmanager_secret.backups_credentials.id
  secret_string = jsonencode({
    username                = "backups"
    password                = random_password.backups_password.result
    engine                  = "mysql"
    host                    = data.terraform_remote_state.common.outputs.rds_endpoint
    port                    = data.terraform_remote_state.common.outputs.rds_port
    dbname                  = "tuk_production"  # Backups user has access to both schemas
    dbInstanceIdentifier    = data.terraform_remote_state.common.outputs.rds_identifier
  })
}

# Legacy credentials secret (manually created, imported into Terraform)
resource "aws_secretsmanager_secret" "legacy_credentials" {
  name                    = "fastapi-legacy-credentials"
  description            = "Legacy database credentials for DMS migration"
  recovery_window_in_days = 7

  tags = {
    Name = "fastapi-legacy-credentials"
  }
}

# Note: Lambda rotation removed - RDS master user password rotation
# is handled by RDS built-in rotation feature
