<?php
/**
 * Auth0 OAuth Service
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
    'AUTH0_OAUTH_SERVICE' => 'Auth0 OAuth Service',
    'AUTH0_OAUTH_SERVICE_DESCRIPTION' => 'Provides Auth0 OAuth authentication for phpBB',
    'AUTH_PROVIDER_OAUTH_SERVICE_TEASEL.AUTH0.PROVIDER' => 'Login with Auth0',
));

