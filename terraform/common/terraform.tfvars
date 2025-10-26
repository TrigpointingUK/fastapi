# Enable CloudFlare SSL for the shared ALB
enable_cloudflare_ssl = true

# MediaWiki database credentials secret ARN (from terraform/mysql outputs)
# Get this from: cd terraform/mysql && terraform output mediawiki_credentials_arn
mediawiki_db_credentials_arn = "arn:aws:secretsmanager:eu-west-1:534526983272:secret:trigpointing-mediawiki-credentials-pk6CXv"

# phpBB database credentials secret ARN (from terraform/mysql outputs)
# Get this from: cd terraform/mysql && terraform output phpbb_credentials_arn
phpbb_db_credentials_arn = "arn:aws:secretsmanager:eu-west-1:534526983272:secret:trigpointing-phpbb-credentials"
cloudflare_account_id    = "5cf73c6796e372c552fdf80a9716b3fb"