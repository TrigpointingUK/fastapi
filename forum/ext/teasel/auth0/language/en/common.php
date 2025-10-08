<?php
/**
 * Auth0 OAuth Service Language File
 */

if (!defined('IN_PHPBB'))
{
    exit;
}

if (empty($lang) || !is_array($lang))
{
    $lang = array();
}

$lang = array_merge($lang, array(
    'AUTH_PROVIDER_OAUTH_SERVICE_AUTH0' => 'Login with Auth0',
));
