FROM mediawiki:1.43

# Install tools & composer
RUN apt-get update && apt-get install -y git unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /var/www/html

# Clone MediaWiki extensions
RUN set -eux; \
  cd extensions; \
  git clone -b REL1_43 https://gerrit.wikimedia.org/r/mediawiki/extensions/PluggableAuth; \
  git clone -b REL1_43 https://gerrit.wikimedia.org/r/mediawiki/extensions/OpenIDConnect; \
  git clone https://github.com/edwardspec/mediawiki-aws-s3 AWS

# Install composer and update dependencies for OIDC/AWS extensions
COPY composer.local.json /var/www/html/
RUN php -r "copy('https://getcomposer.org/installer','composer-setup.php');" \
 && php composer-setup.php --install-dir=/usr/local/bin --filename=composer \
 && composer update -n --no-dev

# LocalSettings.php will be mounted at runtime from AWS Secrets Manager
# No need to copy it into the image

EXPOSE 80

