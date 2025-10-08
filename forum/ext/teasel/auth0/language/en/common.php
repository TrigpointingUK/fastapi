<?php
/**
 * Auth0 OAuth Service
 *
 * @package language
 * @copyright (c) 2024 Teasel
 * @license http://opensource.org/licenses/gpl-2.0.php GNU General Public License v2
 */

if (!defined('IN_PHPBB'))
{
    exit;
}

if (empty($lang) || !is_array($lang))
{
    $lang = [];
}

// OAuth service names
$lang = array_merge($lang, [
    'AUTH_PROVIDER_OAUTH_SERVICE_AUTH0' => 'Login with Auth0',
]);
