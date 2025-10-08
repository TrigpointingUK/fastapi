<?php
namespace teasel\auth0\service;

use OAuth\Common\Http\Uri\UriInterface;
use phpbb\auth\provider\oauth\service\base;
use phpbb\config\config;
use phpbb\request\request_interface;

/**
 * Auth0 OAuth provider that reads settings from environment variables:
 *  AUTH0_DOMAIN (e.g. your-tenant.eu.auth0.com)
 *  AUTH0_CLIENT_ID
 *  AUTH0_CLIENT_SECRET
 *  AUTH0_SCOPE (optional, default 'openid email profile')
 */
class provider extends base
{
    /** @var string */
    protected $auth0_domain;
    
    /** @var string */
    protected $client_id;
    
    /** @var string */
    protected $client_secret;

    /**
     * phpBB config
     *
     * @var config
     */
    protected $config;

    /**
     * phpBB request
     *
     * @var request_interface
     */
    protected $request;

    /**
     * Constructor
     *
     * @param config $config
     * @param request_interface $request
     */
    public function __construct(config $config, request_interface $request)
    {
        $this->config = $config;
        $this->request = $request;
        
        $this->auth0_domain = getenv('AUTH0_DOMAIN') ?: '';
        $this->client_id = getenv('AUTH0_CLIENT_ID') ?: '';
        $this->client_secret = getenv('AUTH0_CLIENT_SECRET') ?: '';
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
    public function get_auth_scope()
    {
        $scope = getenv('AUTH0_SCOPE') ?: 'openid email profile';
        return explode(' ', $scope);
    }

    /**
     * {@inheritdoc}
     */
    public function get_external_service_class()
    {
        return '\teasel\auth0\service\auth0_service';
    }

    /**
     * {@inheritdoc}
     */
    public function perform_auth_login()
    {
        if (!$this->service_provider)
        {
            throw new \phpbb\auth\provider\oauth\service\exception('OAUTH_SERVICE_NOT_INITIALIZED');
        }

        $this->service_provider->setAuthorizationEndpoint(new \OAuth\Common\Http\Uri\Uri('https://' . $this->auth0_domain . '/authorize'));
        $this->service_provider->setAccessTokenEndpoint(new \OAuth\Common\Http\Uri\Uri('https://' . $this->auth0_domain . '/oauth/token'));

        return parent::perform_auth_login();
    }

    /**
     * {@inheritdoc}
     */
    public function perform_token_auth()
    {
        if (!$this->service_provider)
        {
            throw new \phpbb\auth\provider\oauth\service\exception('OAUTH_SERVICE_NOT_INITIALIZED');
        }

        return parent::perform_token_auth();
    }
}
