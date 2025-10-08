<?php
/**
 * Clear phpBB Container Cache
 * Access this at: https://your-forum-url.com/clear_container_cache.php
 * DELETE THIS FILE AFTER USE!
 */

$cache_dir = __DIR__ . '/cache/production/';

if (is_dir($cache_dir)) {
    $files = glob($cache_dir . 'container_*');
    foreach ($files as $file) {
        if (is_file($file)) {
            unlink($file);
            echo "Deleted: " . basename($file) . "\n";
        }
    }
    echo "\nContainer cache cleared!\n";
    echo "Now visit ACP and purge the regular cache.\n";
} else {
    echo "Cache directory not found: $cache_dir\n";
}

echo "\n*** DELETE THIS FILE NOW ***\n";

