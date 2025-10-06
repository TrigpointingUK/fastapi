#!/bin/sh
set -e
# let official script init PHP ext, etc.
[ -x /usr/local/bin/docker-php-entrypoint ] && docker-php-entrypoint php-fpm >/dev/null 2>&1 || true

# Replace phpBB directories with symlinks to EFS
if [ -d /mnt/phpbb/phpbb ]; then
    echo "Setting up EFS symlinks..."

    # Remove existing directories and replace with symlinks
    if [ -d /mnt/phpbb/phpbb/files ]; then
        echo "Removing existing files directory..."
        rm -rf /var/www/html/files
        ln -sf /mnt/phpbb/phpbb/files /var/www/html/files
    fi

    if [ -d /mnt/phpbb/phpbb/store ]; then
        echo "Removing existing store directory..."
        rm -rf /var/www/html/store
        ln -sf /mnt/phpbb/phpbb/store /var/www/html/store
    fi

    if [ -d /mnt/phpbb/phpbb/images/avatars/upload ]; then
        echo "Removing existing avatars directory..."
        rm -rf /var/www/html/images/avatars/upload
        ln -sf /mnt/phpbb/phpbb/images/avatars/upload /var/www/html/images/avatars/upload
    fi
fi

#if [ ! -f /var/www/html/config.php ]; then
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
#fi


ls -al /var/www/html
ls -alR /var/www/html/files
ls -alR /var/www/html/store
ls -alR /var/www/html/images/avatars/upload
cat /var/www/html/config.php

find /mnt/phpbb -type d -print

# Remove installer if present to prevent install wizard
if [ -d /var/www/html/install ]; then
    rm -rf /var/www/html/install
fi

# php-fpm not used in apache image; start apache
exec apache2-foreground
