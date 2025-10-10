<?php
/**
 * Quick diagnostic script to check Auth0 extension configuration
 * Access at: https://forum.trigpointing.uk/check_config.php
 */

define('IN_PHPBB', true);
$phpbb_root_path = (defined('PHPBB_ROOT_PATH')) ? PHPBB_ROOT_PATH : './';
$phpEx = substr(strrchr(__FILE__, '.'), 1);

header('Content-Type: text/plain');

echo "=== Auth0 Extension Configuration Check ===\n\n";

// Check if extension directory exists
$ext_path = $phpbb_root_path . 'ext/teasel/auth0/';
if (is_dir($ext_path)) {
    echo "✓ Extension directory exists: $ext_path\n";

    // Check key files
    $files = ['ext.php', 'event/subscriber.php', 'apache/../apache/phpbb-auth0.conf'];
    foreach ($files as $file) {
        $full_path = $ext_path . $file;
        if (file_exists($full_path)) {
            echo "  ✓ $file exists\n";
            if ($file === 'event/subscriber.php') {
                $content = file_get_contents($full_path);
                if (strpos($content, 'on_page_header') !== false) {
                    echo "    ✓ on_page_header method found\n";
                } else {
                    echo "    ✗ on_page_header method NOT found\n";
                }
            }
        } else {
            echo "  ✗ $file missing\n";
        }
    }
} else {
    echo "✗ Extension directory NOT found: $ext_path\n";
}

// Check Apache config
$apache_conf = $phpbb_root_path . 'apache/phpbb-auth0.conf';
if (file_exists($apache_conf)) {
    echo "\n✓ Apache config exists: $apache_conf\n";
    $conf_content = file_get_contents($apache_conf);
    if (strpos($conf_content, 'RewriteEngine On') !== false) {
        echo "  ✓ RewriteEngine directive found\n";
    }
    if (strpos($conf_content, 'oauth_service=auth.provider.oauth.service.auth0') !== false) {
        echo "  ✓ Auth0 service name found in rewrite rules\n";
    }
} else {
    echo "\n✗ Apache config NOT found: $apache_conf\n";
}

// Try to check if extension is enabled (requires phpBB bootstrap)
try {
    include($phpbb_root_path . 'common.' . $phpEx);
    include($phpbb_root_path . 'includes/functions.' . $phpEx);

    $ext_manager = $phpbb_container->get('ext.manager');
    if ($ext_manager->is_enabled('teasel/auth0')) {
        echo "\n✓ Extension is ENABLED in phpBB\n";
    } else {
        echo "\n✗ Extension is NOT enabled in phpBB\n";
        echo "  → Go to: ACP > Customise > Extension Management\n";
        echo "  → Enable the 'Auth0 OAuth' extension\n";
    }
} catch (Exception $e) {
    echo "\n⚠ Could not check extension status: " . $e->getMessage() . "\n";
}

echo "\n=== Configuration Tests ===\n\n";

// Check environment
echo "PHP Version: " . PHP_VERSION . "\n";
echo "Server Software: " . ($_SERVER['SERVER_SOFTWARE'] ?? 'Unknown') . "\n";
echo "Document Root: " . ($_SERVER['DOCUMENT_ROOT'] ?? 'Unknown') . "\n";

// Check mod_rewrite
if (function_exists('apache_get_modules')) {
    $modules = apache_get_modules();
    if (in_array('mod_rewrite', $modules)) {
        echo "✓ mod_rewrite is loaded\n";
    } else {
        echo "✗ mod_rewrite is NOT loaded\n";
    }
}

echo "\n=== Next Steps ===\n\n";
echo "1. Ensure extension is enabled in ACP > Customise > Extension Management\n";
echo "2. Clear phpBB cache: ACP > General > Purge the cache\n";
echo "3. Verify Apache config is loaded: check Apache logs\n";
echo "4. Test login: go to ucp.php?mode=login (should redirect to Auth0)\n";
echo "5. Test break-glass: go to ucp.php?mode=login&local=1 (should show password form)\n";
echo "\n";
