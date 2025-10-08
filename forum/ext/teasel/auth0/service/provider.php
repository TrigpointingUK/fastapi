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
        if (!is_array($data)) {
            $data = [];
        }

        // Provide phpBB-friendly aliases but keep all original claims for subscribers
        $data['user_id'] = $data['sub'] ?? '';
        // Prefer nickname, then name, then email to avoid phpBB managing usernames
        $data['username'] = $data['nickname'] ?? ($data['name'] ?? ($data['email'] ?? ''));
        $data['email'] = $data['email'] ?? '';
        $data['name'] = $data['name'] ?? '';

        return $data;
    }

    /**
     * {@inheritdoc}
     */
    public function get_auth_user_id()
    {
        // Ensure a phpBB user and oauth mapping exist before phpBB decides to show link/register
        $this->flog('[auth0] provider.get_auth_user_id() invoked');
        $this->ensure_oauth_mapping();
        $user_data = $this->get_user_identity();
        $this->flog('[auth0] provider.get_auth_user_id() returning sub=' . ($user_data['user_id'] ?? ''));
        return $user_data['user_id'];
    }

    /**
     * Ensure the oauth mapping exists; create/link user if needed
     */
    protected function ensure_oauth_mapping()
    {
        $this->flog('[auth0] provider.ensure_oauth_mapping() start');
        // Access services lazily to avoid hard dependency in constructor
        if (!isset($GLOBALS['phpbb_container'])) {
            $this->flog('[auth0] provider.ensure_oauth_mapping() no container');
            return;
        }
        $container = $GLOBALS['phpbb_container'];
        try {
            $db = $container->get('dbal.conn');
        } catch (\Exception $e) {
            $this->flog('[auth0] provider.ensure_oauth_mapping() failed get db: ' . $e->getMessage());
            return;
        }

        $claims = $this->get_user_identity();
        $provider = $this->get_service_name(); // e.g. 'auth.provider.oauth.service.auth0'
        $external = isset($claims['sub']) ? (string)$claims['sub'] : '';
        if ($external === '') {
            $this->flog('[auth0] provider.ensure_oauth_mapping() missing sub');
            return;
        }
        $this->flog('[auth0] provider.ensure_oauth_mapping() provider=' . $provider . ' sub_present=yes');

        // Already linked?
        $table_oauth = defined('OAUTH_ACCOUNTS_TABLE') ? OAUTH_ACCOUNTS_TABLE : 'phpbb_oauth_accounts';
        $sql = "SELECT user_id FROM $table_oauth WHERE provider='" . $db->sql_escape($provider) . "' AND oauth_provider_id='" . $db->sql_escape($external) . "'";
        $res = $db->sql_query($sql);
        $row = $db->sql_fetchrow($res);
        $db->sql_freeresult($res);
        if ($row && (int)$row['user_id'] > 0) {
            $this->flog('[auth0] provider.ensure_oauth_mapping() mapping exists user_id=' . (int)$row['user_id']);
            return;
        }

        $email = isset($claims['email']) ? (string)$claims['email'] : '';
        $user_id = 0;
        if ($email !== '') {
            $table_users = defined('USERS_TABLE') ? USERS_TABLE : 'phpbb_users';
            $sql = "SELECT user_id FROM $table_users WHERE user_email='" . $db->sql_escape($email) . "' AND user_type <> 2"; // exclude anonymous
            $res = $db->sql_query($sql);
            $userRow = $db->sql_fetchrow($res);
            $db->sql_freeresult($res);
            if ($userRow && (int)$userRow['user_id'] > 0) {
                $user_id = (int)$userRow['user_id'];
                $this->flog('[auth0] provider.ensure_oauth_mapping() linked by email user_id=' . $user_id);
            }
        }

        if ($user_id === 0) {
            // Create a new phpBB user using nickname as username
            global $phpbb_root_path, $phpEx;
            if (!function_exists('user_add')) {
                include_once($phpbb_root_path . 'includes/functions_user.' . $phpEx);
            }
            $nickname = isset($claims['nickname']) ? (string)$claims['nickname'] : '';
            $name = isset($claims['name']) ? (string)$claims['name'] : '';
            $username = $nickname !== '' ? $nickname : ($name !== '' ? $name : $email);
            if ($username === '') {
                $username = 'user_' . substr(bin2hex(random_bytes(4)), 0, 8);
            }
            $randomPassword = bin2hex(random_bytes(32));
            $userData = [
                'username'      => $username,
                'user_password' => $randomPassword,
                'user_email'    => $email,
                'group_id'      => 2, // REGISTERED
                'user_type'     => 0, // NORMAL
            ];
            $newId = user_add($userData);
            if (is_int($newId) && $newId > 0) {
                $user_id = $newId;
            }
            $this->flog('[auth0] provider.ensure_oauth_mapping() created user_id=' . (int)$user_id . ' username=' . $username);
        }

        if ($user_id > 0) {
            // Insert mapping (ignore duplicates)
            $sql = "INSERT IGNORE INTO $table_oauth (user_id,provider,oauth_provider_id) VALUES (" . (int)$user_id . ", '" . $db->sql_escape($provider) . "', '" . $db->sql_escape($external) . "')";
            $db->sql_query($sql);
            $this->flog('[auth0] provider.ensure_oauth_mapping() inserted mapping for user_id=' . (int)$user_id);
        }
        $this->flog('[auth0] provider.ensure_oauth_mapping() end');
    }

    protected function flog($msg)
    {
        @file_put_contents('/var/www/html/auth0_debug.log', date('c') . ' ' . $msg . "\n", FILE_APPEND);
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

    /**
     * {@inheritdoc}
     */
    public function perform_link()
    {
        // Auto-link account by email
        return true;
    }

    /**
     * {@inheritdoc}
     */
    public function perform_register()
    {
        // Auto-register new users
        return true;
    }
}
