<?php
# -- Basics --
$wgSitename      = getenv('MW_SITENAME') ?: 'TrigpointingUK';
$wgServer        = getenv('MW_SERVER')   ?: 'https://wiki.trigpointing.uk';
$wgScriptPath    = "";  // adjust if you deploy under /w
$wgArticlePath   = '/$1';     // emit /PageTitle links instead of /wiki/PageTitle
$wgUsePathInfo   = true;      // (usually true by default)
$wgLogo          = "https://trigpointing.uk/pics/tuk_logo.gif";
$wgLanguageCode  = "en-GB";
$wgLocaltimezone = "Europe/London";
$wgForceHTTPS    = true;

# Debug settings (remove after fixing)
// $wgDebugToolbar = true;
// $wgShowExceptionDetails = true;
// $wgShowDBErrorBacktrace = true;

# -- Rights --
$wgRightsText = "Creative Commons Attribution-ShareAlike";
$wgRightsUrl = "https://creativecommons.org/licenses/by-sa/4.0/";
$wgRightsIcon = "$wgResourceBasePath/resources/assets/licenses/cc-by-sa.png";

# -- DB --
$wgDBtype         = 'mysql';
$wgDBserver       = getenv('MEDIAWIKI_DB_HOST') ?: 'localhost';
$wgDBname         = getenv('MEDIAWIKI_DB_NAME') ?: 'mediawiki';
$wgDBuser         = getenv('MEDIAWIKI_DB_USER') ?: 'wiki';
$wgDBpassword     = getenv('MEDIAWIKI_DB_PASSWORD') ?: '';
$wgDBTableOptions = 'ENGINE=InnoDB, DEFAULT CHARSET=utf8mb4';
$wgDBprefix       = getenv('MEDIAWIKI_DB_PREFIX') ?: '';


# -- Keys (store in Secrets Manager and pass as env) --
$wgSecretKey      = getenv('MW_SECRET_KEY')  ?: 'CHANGE-ME';
$wgUpgradeKey     = getenv('MW_UPGRADE_KEY') ?: 'CHANGE-ME';


# --- Redis / Valkey (ElastiCache) ---
$redisHost        = getenv('CACHE_HOST') ?: '';
$redisPort        = (int)(getenv('CACHE_PORT') ?: 6379);
$useTls           = (getenv('CACHE_TLS') ?: 'true') === 'true';

if ($redisHost !== '') {
    $server = ($useTls ? 'tls://' : '') . $redisHost . ':' . $redisPort;

    $wgObjectCaches['redis'] = [
        'class'           => 'RedisBagOStuff',
        'servers'         => [ $server ],
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
    $wgMainCacheType    = 'db';
    $wgParserCacheType  = 'db';
    $wgSessionCacheType = 'db';
}
$wgCacheDirectory = '/tmp/mw-cache'; // Used for localisation cache


# -- Uploads on S3 (AWS extension) --
$wgEnableUploads = true;
wfLoadExtension( 'AWS' );
$wgAWSRegion                = getenv('AWS_REGION') ?: 'eu-west-1';
$wgAWSBucketName            = getenv('AWS_S3_BUCKET') ?: '';
$wgAWSCredentials           = false; // false = use IAM role
$wgAWSRepoHashLevels        = 2;
$wgAWSRepoDeletedHashLevels = 3;
$wgFileExtensions           = ['png', 'gif', 'jpg', 'jpeg', 'pdf', 'svg'];
$wgMaxUploadSize            = 20 * 1024 * 1024; // 20MB
$wgUploadPath               = ""; // Handled by AWS extension
$wgUploadDirectory          = ""; // Handled by AWS extension


# -- Email with SES SMTP --
$wgEnableEmail      = true;
$wgEnableUserEmail  = true;
$wgEmergencyContact = "admin@trigpointing.uk";
$wgPasswordSender   = "noreply@trigpointing.uk";

$smtpUsername = getenv('SMTP_USERNAME');
$smtpPassword = getenv('SMTP_PASSWORD');

if ($smtpUsername && $smtpPassword) {
    $wgSMTP = [
        'host'     => 'email-smtp.eu-west-1.amazonaws.com',
        'IDHost'   => 'wiki.trigpointing.uk',
        'port'     => 587,
        'auth'     => true,
        'username' => $smtpUsername,
        'password' => $smtpPassword,
    ];
}


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
    'scope'              => [ 'openid', 'profile', 'email', 'roles' ],
    'preferred_username' => 'nickname',
    'redirectURI'        => $redirectURI,
  ],
  'buttonLabelMessage' => 'auth0-login',
  'groupsyncs' => [
    [
      'type' => 'mapped',
      'map' => [
        'sysop' => ['https://trigpointing.uk/roles' => ['tuk-admin']],
        // 'bureaucrat' => ['https://trigpointing.uk/roles' => ['tuk-bureaucrat']],
      ],
    ],
  ],
]];

# Auth0 manages all user rights - disable local rights management
unset( $wgGroupPermissions['bureaucrat'] );
unset( $wgRevokePermissions['bureaucrat'] );
unset( $wgAddGroups['bureaucrat'] );
unset( $wgRemoveGroups['bureaucrat'] );
unset( $wgGroupsAddToSelf['bureaucrat'] );
unset( $wgGroupsRemoveFromSelf['bureaucrat'] );
$wgGroupPermissions['sysop']['userrights'] = false;

# -- Extensions --
wfLoadExtension( 'Cite' );


# -- Styles --
wfLoadSkin( 'MinervaNeue' );
wfLoadSkin( 'MonoBook' );
wfLoadSkin( 'Timeless' );
wfLoadSkin( 'Vector' );
$wgDefaultSkin = "Vector";


# Custom Namespace for Book
define("NS_BOOK", 3036);
define("NS_BOOK_TALK", 3037);

$wgExtraNamespaces[NS_BOOK] = "Book";
$wgExtraNamespaces[NS_BOOK_TALK] = "Book_talk";

$wgNamespaceProtection[NS_BOOK] = array( 'editbook' );
$wgNamespacesWithSubpages[NS_BOOK] = true;
$wgGroupPermissions['sysop']['editbook'] = true;
$wgNamespacesToBeSearchedDefault[NS_BOOK] = true;


# Custom Namespaces for Archive
define("NS_ARCHIVE", 3038);
define("NS_ARCHIVE_TALK", 3039);

$wgExtraNamespaces[NS_ARCHIVE] = "Archive";
$wgExtraNamespaces[NS_ARCHIVE_TALK] = "Archive_talk";

$wgNamespaceProtection[NS_ARCHIVE] = array( 'editarchive' );
$wgNamespacesWithSubpages[NS_ARCHIVE] = true;
$wgGroupPermissions['sysop']['editarchive'] = true;
$wgGroupPermissions['user']['editarchive'] = true;
$wgNamespacesToBeSearchedDefault[NS_ARCHIVE] = true;


# Enable subpages in the main and archive namespace
$wgNamespacesWithSubpages[NS_MAIN] = true;
$wgNamespacesWithSubpages[NS_ARCHIVE] = true;
