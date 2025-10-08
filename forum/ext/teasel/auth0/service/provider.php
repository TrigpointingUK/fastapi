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
    /**
     * Constructor
     *
     * @param config $config
     * @param request_interface $request
     */
    public function __construct(config $config, request_interface $request)
    {
        parent::__construct($config, $request);
    }

    /**
     * {@inheritdoc}
     */
    public function get_service_credentials()
    {
        $client_id = getenv('AUTH0_CLIENT_ID') ?: '';
        $client_secret = getenv('AUTH0_CLIENT_SECRET') ?: '';
        
        return [
            'key'    => $client_id,
            'secret' => $client_secret,
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
        return '\\teasel\\auth0\\service\\auth0_service';
    }

    /**
     * {@inheritdoc}
     */
    public function get_external_service_config()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: '';
        return [
            'baseApiUri' => 'https://' . $domain,
        ];
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

        $domain = getenv('AUTH0_DOMAIN') ?: '';
        $this->service_provider->setAuthorizationEndpoint(new \OAuth\Common\Http\Uri\Uri('https://' . $domain . '/authorize'));
        $this->service_provider->setAccessTokenEndpoint(new \OAuth\Common\Http\Uri\Uri('https://' . $domain . '/oauth/token'));

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
