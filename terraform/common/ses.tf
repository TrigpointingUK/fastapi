# SES Email Identity Verification for Common Services
# These email addresses need to be verified before they can send emails
# Note: Environment-specific email identities (noreply@trigpointing.me,
# noreply@trigpointing.uk) are managed in their respective environment configs

resource "aws_ses_email_identity" "admin" {
  email = "admin@trigpointing.uk"
}

# SMTP User for MediaWiki
module "smtp_mediawiki" {
  source       = "../modules/ses-smtp-user"
  user_name    = "smtp-mediawiki"
  project_name = var.project_name
  allowed_from_addresses = [
    "noreply@trigpointing.uk",
    "admin@trigpointing.uk"
  ]
}

# SMTP User for phpBB (already exists, needs to be imported)
module "smtp_phpbb" {
  source       = "../modules/ses-smtp-user"
  user_name    = "smtp-phpbb"
  project_name = var.project_name
  allowed_from_addresses = [
    "noreply@trigpointing.uk",
    "forum@trigpointing.uk"
  ]
}

# Note: Auth0 SMTP users are created per-environment in the auth0 module
# for better security isolation and credential management
