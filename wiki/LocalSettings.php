<?php
# -- Basics --
$wgSitename = getenv('MW_SITENAME') ?: 'TrigpointingUK Wiki';
$wgServer   = getenv('MW_SERVER')   ?: 'https://wiki.trigpointing.uk';
$wgScriptPath = "";  // adjust if you deploy under /w
$wgArticlePath = '/$1';     // emit /PageTitle links instead of /wiki/PageTitle
$wgUsePathInfo = true;      // (usually true by default)

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

# --- Redis / Valkey (ElastiCache) ---
$redisHost = getenv('CACHE_HOST') ?: '';
$redisPort = (int)(getenv('CACHE_PORT') ?: 6379);
$useTls    = (getenv('CACHE_TLS') ?: 'true') === 'true';

if ($redisHost !== '') {
    $server = ($useTls ? 'tls://' : '') . $redisHost . ':' . $redisPort;

    $wgObjectCaches['redis'] = [
        'class'           => 'RedisBagOStuff',
        'servers'         => [ $server ],   // or ['host' => $redisHost, 'port' => $redisPort, 'password' => null, 'persistent' => true]
        'persistent'      => true,
        'connectTimeout'  => 1.0,
    ];

    $wgMainCacheType    = 'redis';
    $wgParserCacheType  = 'redis';
    $wgSessionCacheType = 'redis';

    $wgJobTypeConf['default'] = [
        'class'       => 'JobQueueRedis',
        'redisServer' => $server,
        'redisConfig' => [],
    ];
} else {
    $wgMainCacheType    = 'none';
    $wgParserCacheType  = 'none';
    $wgSessionCacheType = 'db';
}

# -- Uploads on S3 (AWS extension) --
$wgEnableUploads = true;
wfLoadExtension( 'AWS' );
$wgAWSRegion     = getenv('AWS_REGION') ?: 'eu-west-1';
$wgAWSBucketName = getenv('AWS_S3_BUCKET') ?: '';
// Optional: $wgAWSBucketTopSubdirectory = "/$wgDBname";

// Use IAM role credentials (ECS task role provides these automatically)
$wgAWSCredentials = false; // false = use IAM role

// Serve images via signed URLs (since bucket is private)
$wgAWSRepoHashLevels = 2;
$wgAWSRepoDeletedHashLevels = 3;

# -- Auth0 via PluggableAuth + OpenID Connect --
wfLoadExtension( 'PluggableAuth' );
wfLoadExtension( 'OpenIDConnect' );
$wgPluggableAuth_EnableLocalLogin = getenv('MW_ENABLE_LOCAL_LOGIN') === 'true';
$wgGroupPermissions['*']['autocreateaccount'] = true;

$providerURL   = getenv('OIDC_PROVIDER_URL') ?: '';
$clientID      = getenv('OIDC_CLIENT_ID') ?: '';
$clientSecret  = getenv('OIDC_CLIENT_SECRET') ?: '';
$redirectURI   = getenv('OIDC_REDIRECT_URI') ?: ($wgServer . '/wiki/Special:PluggableAuthLogin');
$wgOpenIDConnect_SingleLogout = true;

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

# -- Extensions --
wfLoadExtension( 'Cite' );

wfLoadSkin( 'MinervaNeue' );
wfLoadSkin( 'MonoBook' );
wfLoadSkin( 'Timeless' );
wfLoadSkin( 'Vector' );
