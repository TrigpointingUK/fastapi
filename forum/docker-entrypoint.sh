#!/bin/sh
set -e
# let official script init PHP ext, etc.
[ -x /usr/local/bin/docker-php-entrypoint ] && docker-php-entrypoint php-fpm >/dev/null 2>&1 || true

# Replace phpBB directories with symlinks to EFS (support two layouts)
link_dir() {
    target_name="$1"    # e.g. files | store | images/avatars/upload
    dest="/var/www/html/${target_name}"
    src_a="/mnt/phpbb/phpbb/${target_name}"
    src_b="/mnt/phpbb/${target_name}"

    if [ -d "$src_a" ]; then
        echo "Linking ${dest} -> ${src_a}"
        rm -rf "$dest"
        ln -sf "$src_a" "$dest"
    elif [ -d "$src_b" ]; then
        echo "Linking ${dest} -> ${src_b}"
        rm -rf "$dest"
        ln -sf "$src_b" "$dest"
    else
        echo "EFS path not found for ${target_name} (checked ${src_a} and ${src_b})"
    fi
}

echo "Setting up EFS symlinks (files, store, avatars)..."
link_dir files
link_dir store
link_dir images/avatars/upload

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

# Apply custom green theme by appending import to colours.css
if [ -f /var/www/html/styles/prosilver/theme/colours.css ]; then
    echo "Applying custom green theme..."
    # Check if import already exists to avoid duplicates
    if ! grep -q "colours_green.css" /var/www/html/styles/prosilver/theme/colours.css; then
        if [ -n "${ASSET_VERSION}" ]; then
            echo "@import url(\"colours_green.css?v=${ASSET_VERSION}\");" >> /var/www/html/styles/prosilver/theme/colours.css
        else
            echo '@import url("colours_green.css");' >> /var/www/html/styles/prosilver/theme/colours.css
        fi
    fi
fi

# Remove installer if present to prevent install wizard
if [ -d /var/www/html/install ]; then
    rm -rf /var/www/html/install
fi

# php-fpm not used in apache image; start apache
exec apache2-foreground
