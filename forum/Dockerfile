# Build a minimal, supported phpBB container
ARG PHPBB_VERSION=3.3.15
FROM php:8.2-apache

# PHP extensions phpBB needs
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip libpng-dev libjpeg-dev libfreetype6-dev libzip-dev ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
 && docker-php-ext-install -j"$(nproc)" mysqli pdo pdo_mysql gd zip opcache

RUN a2enmod rewrite

WORKDIR /var/www/html

# Fetch phpBB and set ownership (ZIP first, tar.bz2 fallback)
ARG PHPBB_VERSION=3.3.15
RUN set -eux; \
    base="https://download.phpbb.com/pub/release/3.3/${PHPBB_VERSION}"; \
    mkdir -p /tmp/phpBB3; \
<<<<<<< HEAD
    if curl -fSL "$base/phpBB-${PHPBB_VERSION}.zip" -o /tmp/phpbb.zip; then \
        unzip -q /tmp/phpbb.zip -d /tmp; \
    else \
        curl -fSL "$base/phpBB-${PHPBB_VERSION}.tar.bz2" -o /tmp/phpbb.tar.bz2; \
        tar -xjf /tmp/phpbb.tar.bz2 -C /tmp; \
    fi; \
=======
    curl -fSL "$base/phpBB-${PHPBB_VERSION}.tar.bz2" -o /tmp/phpbb.tar.bz2; \
    tar -xjf /tmp/phpbb.tar.bz2 -C /tmp; \
>>>>>>> 8e24469 (debug)
    mv /tmp/phpBB3/* /var/www/html/; \
    rm -rf /tmp/phpbb.zip /tmp/phpbb.tar.bz2 /tmp/phpBB3; \
    chown -R www-data:www-data /var/www/html

# Add entrypoint to create config.php and link EFS directories
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
