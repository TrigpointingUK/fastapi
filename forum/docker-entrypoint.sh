#!/bin/sh
set -e
# let official script init PHP ext, etc.
[ -x /usr/local/bin/docker-php-entrypoint ] && docker-php-entrypoint php-fpm >/dev/null 2>&1 || true

if [ -d /mnt/phpbb/phpbb ]; then
    # create symlinks to EFS-backed dirs if present
    [ -d /mnt/phpbb/phpbb/files ] && ln -snf /mnt/phpbb/phpbb/files /var/www/html/files
    [ -d /mnt/phpbb/phpbb/store ] && ln -snf /mnt/phpbb/phpbb/store /var/www/html/store
    [ -d /mnt/phpbb/phpbb/images ] && ln -snf /mnt/phpbb/phpbb/images /var/www/html/images
fi

if [ ! -f /var/www/html/config.php ]; then
cat > /var/www/html/config.php <<'PHP'
<?php
$dbms = 'mysqli';
$dbhost = getenv('PHPBB_DB_HOST');
$dbport = '';
$dbname = getenv('PHPBB_DB_NAME');
$dbuser = getenv('PHPBB_DB_USER');
$dbpasswd = getenv('PHPBB_DB_PASS');
$table_prefix = getenv('PHPBB_TABLE_PREFIX') ?: 'phpbb_';
$acm_type = 'file';
$load_extensions = '';
@define('PHPBB_INSTALLED', true);
PHP
chown www-data:www-data /var/www/html/config.php
fi

# php-fpm not used in apache image; start apache
exec apache2-foreground
