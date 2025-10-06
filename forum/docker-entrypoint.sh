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

# Don't create config.php - let phpBB installer create it
# The installer will handle database setup and create config.php with proper settings

# After successful installation, the installer creates a .lock file
# Only remove the installer directory if phpBB is fully installed
if [ -f /var/www/html/config.php ] && [ -d /var/www/html/install ]; then
    # Check if there's a lock file indicating successful installation
    if [ -f /var/www/html/install/install.lock ] || grep -q "PHPBB_INSTALLED" /var/www/html/config.php 2>/dev/null; then
        echo "phpBB installation detected - removing installer directory"
        rm -rf /var/www/html/install
    else
        echo "phpBB installer present - waiting for installation to complete"
    fi
fi

# php-fpm not used in apache image; start apache
exec apache2-foreground
