<?php
/**
 * Auth0 Extension Diagnostics
 * Access this at: https://your-forum-url.com/ext_auth0_diag.php
 * Remove this file after troubleshooting!
 */

header('Content-Type: text/plain');

echo "Auth0 OAuth Extension Diagnostics\n";
echo "==================================\n\n";

echo "Environment Variables:\n";
echo "---------------------\n";
echo "AUTH0_DOMAIN: " . (getenv('AUTH0_DOMAIN') ?: '[NOT SET]') . "\n";
echo "AUTH0_CLIENT_ID: " . (getenv('AUTH0_CLIENT_ID') ? '[SET - ' . strlen(getenv('AUTH0_CLIENT_ID')) . ' chars]' : '[NOT SET]') . "\n";
echo "AUTH0_CLIENT_SECRET: " . (getenv('AUTH0_CLIENT_SECRET') ? '[SET - ' . strlen(getenv('AUTH0_CLIENT_SECRET')) . ' chars]' : '[NOT SET]') . "\n";
echo "AUTH0_SCOPE: " . (getenv('AUTH0_SCOPE') ?: 'openid email profile (default)') . "\n";
echo "\n";

echo "Extension Files:\n";
echo "----------------\n";
$files = [
    'ext/teasel/auth0/ext.php',
    'ext/teasel/auth0/composer.json',
    'ext/teasel/auth0/config/services.yml',
    'ext/teasel/auth0/service/provider.php',
    'ext/teasel/auth0/language/en/common.php',
    'ext/teasel/auth0/event/subscriber.php',
];

foreach ($files as $file) {
    $path = __DIR__ . '/' . $file;
    echo ($file . ': ' . (file_exists($path) ? 'EXISTS' : 'MISSING') . "\n");
}

echo "\n";
echo "If environment variables are NOT SET, add them to your ECS task definition.\n";
echo "Remember to delete this diagnostic file after use!\n";

