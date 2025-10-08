<?php
/**
 * Debug OAuth Service Creation
 * Access at: https://your-forum-url.com/debug_oauth.php
 * DELETE AFTER USE!
 */

define('IN_PHPBB', true);
$phpbb_root_path = __DIR__ . '/';
$phpEx = 'php';
include($phpbb_root_path . 'common.' . $phpEx);

header('Content-Type: text/plain');

echo "OAuth Service Debug\n";
echo "===================\n\n";

try {
    $service_collection = $phpbb_container->get('auth.provider.oauth.service_collection');
    
    echo "Available OAuth services:\n";
    foreach ($service_collection as $service_name => $service) {
        echo "- $service_name: " . get_class($service) . "\n";
    }
    
    echo "\n\nAttempting to get Auth0 service directly from container:\n";
    try {
        $auth0_service = $phpbb_container->get('auth.provider.oauth.service.auth0');
        echo "✓ Service instantiated: " . get_class($auth0_service) . "\n";
        
        echo "\nService credentials:\n";
        try {
            $creds = $auth0_service->get_service_credentials();
            echo "- Key length: " . strlen($creds['key'] ?? '') . "\n";
            echo "- Secret length: " . strlen($creds['secret'] ?? '') . "\n";
        } catch (\Exception $e) {
            echo "ERROR getting credentials: " . $e->getMessage() . "\n";
            echo $e->getTraceAsString() . "\n";
        }
        
        echo "\nService scopes:\n";
        try {
            $scopes = $auth0_service->get_auth_scope();
            echo "- " . implode(', ', $scopes) . "\n";
        } catch (\Exception $e) {
            echo "ERROR getting scopes: " . $e->getMessage() . "\n";
        }
        
        echo "\nExternal service class:\n";
        try {
            $ext_class = $auth0_service->get_external_service_class();
            echo "- $ext_class\n";
            echo "- Class exists: " . (class_exists($ext_class) ? 'YES' : 'NO') . "\n";
        } catch (\Exception $e) {
            echo "ERROR: " . $e->getMessage() . "\n";
        }
        
    } catch (\Exception $e) {
        echo "✗ FAILED to instantiate service\n";
        echo "Error: " . $e->getMessage() . "\n";
        echo "Trace:\n" . $e->getTraceAsString() . "\n";
    }
    
    echo "\n\nAttempting to access via collection key 'auth0':\n";
    if (isset($service_collection['auth0'])) {
        echo "✓ Found in collection\n";
    } else {
        echo "✗ Not found in collection - checking all keys:\n";
        foreach ($service_collection as $key => $svc) {
            echo "  - '$key'\n";
        }
    }
    
} catch (\Exception $e) {
    echo "\nFATAL ERROR: " . $e->getMessage() . "\n";
    echo "Trace:\n" . $e->getTraceAsString() . "\n";
}

echo "\n\n*** DELETE THIS FILE ***\n";

