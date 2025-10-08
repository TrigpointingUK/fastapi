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
    // No constructor needed - base class handles it

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
        return '\\OAuth\\OAuth2\\Service\\Generic';
    }

    /**
     * {@inheritdoc}
     */
    public function get_external_service_config()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: '';
        return [
            'baseApiUri'          => 'https://' . $domain,
            'authorizationEndpoint' => '/authorize',
            'accessTokenEndpoint' => '/oauth/token',
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
    
    /**
     * {@inheritdoc}
     */
    protected function get_user_identity()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: '';
        $token = $this->service_provider->getStorage()->retrieveAccessToken($this->service_name);
        
        $request = new \OAuth\Common\Http\Uri\Uri('https://' . $domain . '/userinfo');
        $response = $this->service_provider->request($request, 'GET', null, ['Authorization' => 'Bearer ' . $token->getAccessToken()]);
        
        return json_decode($response, true);
    }
}
