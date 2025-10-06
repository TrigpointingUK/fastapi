#!/bin/sh
set -e
# let official script init PHP ext, etc.
[ -x /usr/local/bin/docker-php-entrypoint ] && docker-php-entrypoint php-fpm >/dev/null 2>&1 || true

# EFS directories are now mounted directly via ECS, no symlinking needed

if [ ! -f /var/www/html/config.php ]; then
cat > /var/www/html/config.php <<PHP
<?php
\$dbms = 'phpbb\\db\\driver\\mysqli';
\$dbhost = '${PHPBB_DB_HOST}';
\$dbport = '';
\$dbname = '${PHPBB_DB_NAME}';
\$dbuser = '${PHPBB_DB_USER}';
\$dbpasswd = '${PHPBB_DB_PASS}';
\$table_prefix = '${PHPBB_TABLE_PREFIX}';
\$phpbb_adm_relative_path = 'adm/';
\$acm_type = 'phpbb\\cache\\driver\\file';
\$load_extensions = '';

@define('PHPBB_INSTALLED', true);
@define('PHPBB_ENVIRONMENT', 'production');
PHP
chown www-data:www-data /var/www/html/config.php
fi

# Remove installer if present to prevent install wizard
if [ -d /var/www/html/install ]; then
    rm -rf /var/www/html/install
fi

# php-fpm not used in apache image; start apache
exec apache2-foreground
