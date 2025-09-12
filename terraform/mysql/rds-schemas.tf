# MySQL provider for database management
provider "mysql" {
  endpoint = aws_db_instance.main.endpoint
  username = "admin"
  password = jsondecode(aws_secretsmanager_secret_version.admin_credentials.secret_string)["password"]
}

# Create production schema
resource "mysql_database" "production" {
  name = "tuk_production"

  depends_on = [aws_db_instance.main]
}

# Create staging schema
resource "mysql_database" "staging" {
  name = "tuk_staging"

  depends_on = [aws_db_instance.main]
}

# Create production user
resource "mysql_user" "production" {
  user               = "fastapi_production"
  host               = "%"
  plaintext_password = random_password.production_password.result

  depends_on = [aws_db_instance.main]
}

# Grant full permissions to production user on production schema
resource "mysql_grant" "production" {
  user       = mysql_user.production.user
  host       = mysql_user.production.host
  database   = mysql_database.production.name
  privileges = ["ALL"]

  depends_on = [mysql_user.production, mysql_database.production]
}

# Create staging user
resource "mysql_user" "staging" {
  user               = "fastapi_staging"
  host               = "%"
  plaintext_password = random_password.staging_password.result

  depends_on = [aws_db_instance.main]
}

# Grant full permissions to staging user on staging schema
resource "mysql_grant" "staging" {
  user       = mysql_user.staging.user
  host       = mysql_user.staging.host
  database   = mysql_database.staging.name
  privileges = ["ALL"]

  depends_on = [mysql_user.staging, mysql_database.staging]
}

# Create backups user
resource "mysql_user" "backups" {
  user               = "backups"
  host               = "%"
  plaintext_password = random_password.backups_password.result

  depends_on = [aws_db_instance.main]
}

# Grant SELECT permissions to backups user on production schema
resource "mysql_grant" "backups_production" {
  user       = mysql_user.backups.user
  host       = mysql_user.backups.host
  database   = mysql_database.production.name
  privileges = ["SELECT"]

  depends_on = [mysql_user.backups, mysql_database.production]
}

# Grant SELECT permissions to backups user on staging schema
resource "mysql_grant" "backups_staging" {
  user       = mysql_user.backups.user
  host       = mysql_user.backups.host
  database   = mysql_database.staging.name
  privileges = ["SELECT"]

  depends_on = [mysql_user.backups, mysql_database.staging]
}
