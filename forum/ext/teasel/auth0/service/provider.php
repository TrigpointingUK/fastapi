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
    /** @var config */
    protected $config;

    /** @var request_interface */
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
        return '\\teasel\\auth0\\service\\auth0';
    }

    /**
     * {@inheritdoc}
     */
    public function perform_auth_login()
    {
        if (!($this->service_provider instanceof \OAuth\OAuth2\Service\AbstractService))
        {
            throw new \phpbb\auth\provider\oauth\service\exception('AUTH_PROVIDER_OAUTH_ERROR_INVALID_SERVICE_TYPE');
        }

        $this->service_provider->requestAccessToken(
            $this->request->variable('code', '')
        );
    }

    /**
     * {@inheritdoc}
     */
    public function perform_token_auth()
    {
        if (!($this->service_provider instanceof \OAuth\OAuth2\Service\AbstractService))
        {
            throw new \phpbb\auth\provider\oauth\service\exception('AUTH_PROVIDER_OAUTH_ERROR_INVALID_SERVICE_TYPE');
        }

        $this->service_provider->refreshAccessToken(
            $this->service_provider->getStorage()->retrieveAccessToken($this->get_service_name())->getRefreshToken()
        );
    }
    
    /**
     * {@inheritdoc}
     */
    protected function get_user_identity()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: '';
        
        // Request user info from Auth0
        $uri = new \OAuth\Common\Http\Uri\Uri('https://' . $domain . '/userinfo');
        $response = $this->service_provider->request($uri);
        
        $data = json_decode($response, true);
        
        // Map Auth0 user data to phpBB format
        return [
            'user_id' => $data['sub'] ?? '',
            'username' => $data['email'] ?? $data['nickname'] ?? $data['name'] ?? '',
            'email' => $data['email'] ?? '',
            'name' => $data['name'] ?? '',
        ];
    }

    /**
     * {@inheritdoc}
     */
    public function get_auth_user_id()
    {
        $user_data = $this->get_user_identity();
        return $user_data['user_id'];
    }

    /**
     * Allow auto-linking accounts by email
     */
    public function is_email_verified()
    {
        // Auth0 verifies emails, so we trust them
        return true;
    }

    /**
     * {@inheritdoc}
     */
    public function get_auth_user_email()
    {
        $user_data = $this->get_user_identity();
        return $user_data['email'];
    }
}
