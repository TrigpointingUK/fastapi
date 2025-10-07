<?php
// ext_diag.php — temporary! remove after use.
define('IN_PHPBB', true);
$phpbb_root_path = __DIR__ . '/';
$phpEx = 'php';
include($phpbb_root_path . 'common.' . $phpEx);

header('Content-Type: text/plain');

// Use phpBB's extension manager to list what it found.
$em = $phpbb_container->get('ext.manager');

echo "Available extensions (vendor/name) -> state\n";
foreach ($em->all_available() as $name => $meta) {
    $state = $em->is_enabled($name) ? 'ENABLED' : 'DISABLED';
    echo "- $name -> $state\n";
}

// Show any scan errors the manager knows about.
if (method_exists($em, 'get_errors')) {
    $errors = $em->get_errors();
    if (!empty($errors)) {
        echo "\nErrors:\n";
        foreach ($errors as $ext => $err) {
            echo "[$ext] $err\n";
        }
    }
}

echo "\nDirect file checks for teasel/auth0:\n";
$base = __DIR__ . '/ext/teasel/auth0';
$req  = [
  "$base/composer.json",
  "$base/ext.php",
  "$base/config/services.yml",
  "$base/src/service/provider.php",
];
foreach ($req as $p) {
    echo (file_exists($p) ? "[OK] " : "[MISSING] ") . $p . "\n";
}

// Validate composer.json quickly
$cfile = "$base/composer.json";
if (file_exists($cfile)) {
    $j = json_decode(file_get_contents($cfile), true);
    echo "\ncomposer.json type: " . ($j['type'] ?? '(none)') . "\n";
    echo "composer.json name: " . ($j['name'] ?? '(none)') . "\n";
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo "JSON ERROR: " . json_last_error_msg() . "\n";
    }
}
