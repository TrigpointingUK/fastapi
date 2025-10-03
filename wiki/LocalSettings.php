<?php
# -- Basics --
$wgSitename = getenv('MW_SITENAME') ?: 'TrigpointingUK Wiki';
$wgServer   = getenv('MW_SERVER')   ?: 'https://wiki.trigpointing.uk';
$wgScriptPath = "";  // adjust if you deploy under /w

# -- DB --
$wgDBtype     = 'mysql';
$wgDBserver   = getenv('MEDIAWIKI_DB_HOST') ?: 'localhost';
$wgDBname     = getenv('MEDIAWIKI_DB_NAME') ?: 'mediawiki';
$wgDBuser     = getenv('MEDIAWIKI_DB_USER') ?: 'wiki';
$wgDBpassword = getenv('MEDIAWIKI_DB_PASSWORD') ?: '';
$wgDBTableOptions = 'ENGINE=InnoDB, DEFAULT CHARSET=utf8mb4';
$wgDBprefix = getenv('MEDIAWIKI_DB_PREFIX') ?: '';

# -- Keys (store in Secrets Manager and pass as env) --
$wgSecretKey  = getenv('MW_SECRET_KEY')  ?: 'CHANGE-ME';
$wgUpgradeKey = getenv('MW_UPGRADE_KEY') ?: 'CHANGE-ME';

# -- Caching & Sessions (Redis / Valkey) --
$cacheHost = getenv('CACHE_HOST') ?: '';
$cachePort = getenv('CACHE_PORT') ?: '6379';
if ($cacheHost) {
    // Use TLS if your ElastiCache/Valkey is encrypted (serverless usually is)
    $useTls = (getenv('CACHE_TLS') ?: 'true') === 'true';
    $server = ($useTls ? 'tls://' : '') . $cacheHost . ':' . $cachePort;

    $wgObjectCaches['redis'] = [
        'class' => 'RedisBagOStuff',
        'servers' => [ $server ],
        'persistent' => true,
        'connectTimeout' => 1.0,
    ];
    $wgMainCacheType    = CACHE_REDIS;
    $wgParserCacheType  = CACHE_REDIS;
    $wgSessionCacheType = CACHE_REDIS;

    $wgJobTypeConf['default'] = [
        'class' => 'JobQueueRedis',
        'redisServer' => $server,
        'redisConfig' => [],
    ];
} else {
    $wgMainCacheType    = CACHE_NONE;
    $wgParserCacheType  = CACHE_NONE;
    $wgSessionCacheType = CACHE_DB;
}

# -- Uploads on S3 (AWS extension) --
$wgEnableUploads = true;
wfLoadExtension( 'AWS' );
$wgAWSRegion     = getenv('AWS_REGION') ?: 'eu-west-1';
$wgAWSBucketName = getenv('AWS_S3_BUCKET') ?: '';
// Optional: $wgAWSBucketTopSubdirectory = "/$wgDBname";

# -- Auth0 via PluggableAuth + OpenID Connect --
wfLoadExtension( 'PluggableAuth' );
wfLoadExtension( 'OpenIDConnect' );
$wgPluggableAuth_EnableLocalLogin = getenv('MW_ENABLE_LOCAL_LOGIN') === 'true';
$wgGroupPermissions['*']['autocreateaccount'] = true;

$providerURL   = getenv('OIDC_PROVIDER_URL') ?: '';
$clientID      = getenv('OIDC_CLIENT_ID') ?: '';
$clientSecret  = getenv('OIDC_CLIENT_SECRET') ?: '';
$redirectURI   = getenv('OIDC_REDIRECT_URI') ?: ($wgServer . '/wiki/Special:PluggableAuthLogin');

$wgPluggableAuth_Config = [[
  'plugin' => 'OpenIDConnect',
  'data' => [
    'providerURL'        => $providerURL,
    'clientID'           => $clientID,
    'clientsecret'       => $clientSecret,
    'scope'              => [ 'openid', 'profile', 'email' ],
    'preferred_username' => 'nickname',
    'redirectURI'        => $redirectURI,
  ],
  'buttonLabelMessage' => 'auth0-login'
]];

# -- Misc --
$wgCacheDirectory = '/tmp/mw-cache';
$wgShowExceptionDetails = true;
