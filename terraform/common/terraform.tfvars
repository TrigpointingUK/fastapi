# Enable CloudFlare SSL for the shared ALB
enable_cloudflare_ssl = true

# MediaWiki database credentials secret ARN (from terraform/mysql outputs)
# Get this from: cd terraform/mysql && terraform output mediawiki_credentials_arn
mediawiki_db_credentials_arn = "arn:aws:secretsmanager:eu-west-1:730335650803:secret:trigpointing-mediawiki-credentials-XXXXXX"
