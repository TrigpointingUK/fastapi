# SES Email Identity Verification
# These email addresses need to be verified before they can send emails

resource "aws_ses_email_identity" "noreply" {
  email = "noreply@trigpointing.uk"
}

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
