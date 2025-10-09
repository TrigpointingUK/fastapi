<?php
namespace teasel\auth0\service;

use OAuth\OAuth2\Service\AbstractService;
use OAuth\OAuth2\Token\StdOAuth2Token;
use OAuth\Common\Http\Exception\TokenResponseException;
use OAuth\Common\Http\Uri\Uri;
use OAuth\Common\Http\Uri\UriInterface;
use OAuth\Common\Consumer\CredentialsInterface;
use OAuth\Common\Http\Client\ClientInterface;
use OAuth\Common\Storage\TokenStorageInterface;

/**
 * Auth0 OAuth2 Service
 */
class auth0 extends AbstractService
{
    /**
     * Defined scopes for Auth0
     */
    const SCOPE_OPENID = 'openid';
    const SCOPE_EMAIL = 'email';
    const SCOPE_PROFILE = 'profile';

    /**
     * {@inheritdoc}
     */
    public function getAuthorizationEndpoint()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: 'auth.example.com';
        return new Uri('https://' . $domain . '/authorize');
    }

    /**
     * {@inheritdoc}
     */
    public function getAccessTokenEndpoint()
    {
        $domain = getenv('AUTH0_DOMAIN') ?: 'auth.example.com';
        return new Uri('https://' . $domain . '/oauth/token');
    }

    /**
     * {@inheritdoc}
     */
    protected function getAuthorizationMethod()
    {
        return static::AUTHORIZATION_METHOD_HEADER_BEARER;
    }

    /**
     * {@inheritdoc}
     */
    protected function parseAccessTokenResponse($responseBody)
    {
        $data = json_decode($responseBody, true);

        if (null === $data || !is_array($data)) {
            throw new TokenResponseException('Unable to parse response.');
        } elseif (isset($data['error_description'])) {
            throw new TokenResponseException('Error: ' . $data['error_description']);
        } elseif (isset($data['error'])) {
            throw new TokenResponseException('Error: ' . $data['error']);
        }

        $token = new StdOAuth2Token();
        $token->setAccessToken($data['access_token']);
        
        if (isset($data['expires_in'])) {
            $token->setLifeTime($data['expires_in']);
        }

        if (isset($data['refresh_token'])) {
            $token->setRefreshToken($data['refresh_token']);
            unset($data['refresh_token']);
        }

        unset($data['access_token'], $data['expires_in']);
        $token->setExtraParams($data);

        return $token;
    }

    /**
     * {@inheritdoc}
     */
    protected function getExtraOAuthHeaders()
    {
        return ['Accept' => 'application/json'];
    }
    

    /**
     * {@inheritdoc}
     */
    protected function getExtraApiHeaders()
    {
        return ['Accept' => 'application/json'];
    }
}

