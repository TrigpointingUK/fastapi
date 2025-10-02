
# Create production schema
resource "mysql_database" "production" {
  name = "tuk_production"

  depends_on = [data.terraform_remote_state.common]
}

# Create staging schema
resource "mysql_database" "staging" {
  name = "tuk_staging"

  depends_on = [data.terraform_remote_state.common]
}

# Create phpbb schema
resource "mysql_database" "phpbb" {
  name = "phpbb_db"

  depends_on = [data.terraform_remote_state.common]
}

# Create mediawiki schema
resource "mysql_database" "mediawiki" {
  name = "mediawiki"

  depends_on = [data.terraform_remote_state.common]
}


# Create production user
resource "mysql_user" "production" {
  user               = "fastapi_production"
  host               = "%"
  plaintext_password = random_password.production_password.result

  depends_on = [data.terraform_remote_state.common]
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

  depends_on = [data.terraform_remote_state.common]
}

# Grant full permissions to staging user on staging schema
resource "mysql_grant" "staging" {
  user       = mysql_user.staging.user
  host       = mysql_user.staging.host
  database   = mysql_database.staging.name
  privileges = ["ALL"]

  depends_on = [mysql_user.staging, mysql_database.staging]
}


# Create phpbb user
resource "mysql_user" "phpbb" {
  user               = "phpbb_user"
  host               = "%"
  plaintext_password = random_password.phpbb_password.result

  depends_on = [data.terraform_remote_state.common]
}

# Grant full permissions to phpbb user on phpbb schema
resource "mysql_grant" "phpbb" {
  user       = mysql_user.staging.user
  host       = mysql_user.staging.host
  database   = mysql_database.phpbb.name
  privileges = ["ALL"]

  depends_on = [mysql_user.phpbb, mysql_database.phpbb]
}
# Create backups user
resource "mysql_user" "backups" {
  user               = "backups"
  host               = "%"
  plaintext_password = random_password.backups_password.result

  depends_on = [data.terraform_remote_state.common]
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

# Create mediawiki user
resource "mysql_user" "mediawiki" {
  user               = "mediawiki_user"
  host               = "%"
  plaintext_password = random_password.mediawiki_password.result

  depends_on = [data.terraform_remote_state.common]
}

# Grant full permissions to mediawiki user on mediawiki schema
resource "mysql_grant" "mediawiki" {
  user       = mysql_user.mediawiki.user
  host       = mysql_user.mediawiki.host
  database   = mysql_database.mediawiki.name
  privileges = ["ALL"]

  depends_on = [mysql_user.mediawiki, mysql_database.mediawiki]
}

# Grant SELECT permissions to backups user on mediawiki schema
resource "mysql_grant" "backups_mediawiki" {
  user       = mysql_user.backups.user
  host       = mysql_user.backups.host
  database   = mysql_database.mediawiki.name
  privileges = ["SELECT"]

  depends_on = [mysql_user.backups, mysql_database.mediawiki]
}
