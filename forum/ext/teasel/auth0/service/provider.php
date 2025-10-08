<?php
namespace teasel\auth0\service;

use phpbb\auth\provider\oauth\service\base;
use phpbb\config\config;

/**
 * Auth0 OAuth provider that reads settings from environment variables:
 *  AUTH0_DOMAIN (e.g. your-tenant.eu.auth0.com)
 *  AUTH0_CLIENT_ID
 *  AUTH0_CLIENT_SECRET
 *  AUTH0_SCOPE (optional, default 'openid email profile')
 */
class provider extends base
{
    protected $client_id;
    protected $client_secret;

    public function __construct(config $config)
    {
        $domain = getenv('AUTH0_DOMAIN') ?: '';
        $this->client_id = getenv('AUTH0_CLIENT_ID') ?: '';
        $this->client_secret = getenv('AUTH0_CLIENT_SECRET') ?: '';
        $scope = getenv('AUTH0_SCOPE') ?: 'openid email profile';

        $credentials = ['key' => $this->client_id, 'secret' => $this->client_secret];
        $options     = ['scope' => $scope];
        $endpoints   = [
            'base_url'     => 'https://' . $domain,
            'authorize_url'=> '/authorize',
            'token_url'    => '/oauth/token',
            'info_url'     => '/userinfo',
        ];

        parent::__construct($config, $credentials, $options, $endpoints, 'auth0');
    }

    /**
     * {@inheritdoc}
     */
    public function get_service_credentials()
    {
        return [
            'key'    => $this->client_id,
            'secret' => $this->client_secret,
        ];
    }

    /**
     * {@inheritdoc}
     */
    public function perform_auth_login()
    {
        return parent::perform_auth_login();
    }

    /**
     * {@inheritdoc}
     */
    public function perform_token_auth()
    {
        return parent::perform_token_auth();
    }
}
