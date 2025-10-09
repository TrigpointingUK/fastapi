<?php
namespace teasel\auth0\event;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use phpbb\db\driver\driver_interface;
use phpbb\user;

class subscriber implements EventSubscriberInterface
{
    protected $db; protected $user;
    public function __construct(driver_interface $db, user $user) { $this->db=$db; $this->user=$user; }
    protected function flog($msg){
        // Log to stdout for Docker/containerized environments
        error_log('[auth0] ' . $msg);
        // Also log to tmp as fallback
        @file_put_contents('/tmp/auth0_debug.log', date('c')." ".$msg."\n", FILE_APPEND);
    }
    
    /**
     * Get unique username by appending numbers if needed
     */
    protected function get_unique_username($base, $db)
    {
        $table_users = defined('USERS_TABLE') ? USERS_TABLE : 'phpbb_users';
        $username = $base;
        $counter = 0;
        
        while (true) {
            $clean = utf8_clean_string($username);
            $sql = "SELECT user_id FROM $table_users WHERE username_clean='" . $db->sql_escape($clean) . "'";
            $res = $db->sql_query($sql);
            $row = $db->sql_fetchrow($res);
            $db->sql_freeresult($res);
            
            if (!$row) {
                return $username; // Username is available
            }
            
            $counter++;
            $username = $base . $counter;
            
            if ($counter > 100) {
                // Fallback to random
                return 'user_' . substr(bin2hex(random_bytes(4)), 0, 8);
            }
        }
    }
    public static function getSubscribedEvents() {
        return [
            'core.auth_oauth_authenticate_after' => 'on_oauth_authenticate_after',
            // Some phpBB versions expose additional hooks after fetching remote data
            'core.auth_oauth_remote_data_after' => 'on_oauth_remote_data_after',
            // Intercept before link/register UI is shown
            'core.auth_oauth_link_before' => 'on_oauth_link_before',
            'core.auth_oauth_login_after' => 'on_oauth_login_after',
            'core.auth_oauth_link_after' => 'on_oauth_link_after',
        ];
    }
    public function on_oauth_remote_data_after($event)
    {
        $this->flog('[auth0] on_oauth_remote_data_after');
        $this->ensure_oauth_mapping($event);
    }
    public function on_oauth_authenticate_after($event)
    {
        $this->flog('[auth0] on_oauth_authenticate_after');
        $this->ensure_oauth_mapping($event);
    }
    public function on_oauth_link_before($event)
    {
        $this->flog('[auth0] on_oauth_link_before');
        // Try to create/link then redirect away to avoid showing the prompt
        $made = $this->ensure_oauth_mapping($event);
        if ($made) {
            global $phpbb_root_path, $phpEx;
            if (!function_exists('redirect')) {
                include_once($phpbb_root_path.'includes/functions.'.$phpEx);
            }
            $target = append_sid($phpbb_root_path.'index.'.$phpEx);
            redirect($target);
        }
    }

    protected function ensure_oauth_mapping($event)
    {
        // Ensure an oauth mapping exists; return true if mapping was created
        $service = $event['service'] ?? null;
        if (!$service) return false;
        $claims = $service->get_user_identity();
        // Get the actual service name if available; fall back to 'auth0'
        $provider = method_exists($service, 'get_service_name') ? (string)$service->get_service_name() : 'auth0';
        $external = isset($claims['sub']) ? (string)$claims['sub'] : '';
        $this->flog('[auth0] ensure_oauth_mapping provider=' . $provider . ' sub_present=' . ($external !== '' ? 'yes' : 'no'));
        if ($external === '') return false;

        // Already linked?
        $sql = 'SELECT user_id FROM ' . (defined('OAUTH_ACCOUNTS_TABLE') ? OAUTH_ACCOUNTS_TABLE : 'phpbb_oauth_accounts') .
               " WHERE provider='".$this->db->sql_escape($provider)."' AND oauth_provider_id='".$this->db->sql_escape($external)."'";
        $res = $this->db->sql_query($sql);
        $row = $this->db->sql_fetchrow($res);
        $this->db->sql_freeresult($res);
        if ($row && (int)$row['user_id'] > 0) { $this->flog('[auth0] mapping exists'); return false; }

        // Try to link by email if present
        $email = isset($claims['email']) ? (string)$claims['email'] : '';
        $user_id = 0;
        if ($email !== '') {
            $sql = 'SELECT user_id FROM ' . (defined('USERS_TABLE') ? USERS_TABLE : 'phpbb_users') .
                   " WHERE user_email='".$this->db->sql_escape($email)."' AND user_type <> 2"; // exclude anonymous
            $res = $this->db->sql_query($sql);
            $userRow = $this->db->sql_fetchrow($res);
            $this->db->sql_freeresult($res);
            if ($userRow && (int)$userRow['user_id'] > 0) {
                $user_id = (int)$userRow['user_id'];
                $this->flog('[auth0] linked by email user_id=' . $user_id);
            }
        }

        if ($user_id === 0) {
            // Create a new phpBB user using nickname as username
            global $phpbb_root_path, $phpEx;
            if (!function_exists('user_add')) {
                include_once($phpbb_root_path.'includes/functions_user.'.$phpEx);
            }
            if (!function_exists('phpbb_hash')) {
                include_once($phpbb_root_path.'includes/functions_user.'.$phpEx);
            }
            
            // Determine base username
            $nickname = isset($claims['nickname']) ? (string)$claims['nickname'] : '';
            $name = isset($claims['name']) ? (string)$claims['name'] : '';
            $baseUsername = $nickname !== '' ? $nickname : ($name !== '' ? $name : $email);
            if ($baseUsername === '') {
                $baseUsername = 'user_'.substr(bin2hex(random_bytes(4)), 0, 8);
            }
            
            // Ensure username is unique
            $username = $this->get_unique_username($baseUsername, $this->db);
            
            // Generate random password and hash it properly
            $randomPassword = bin2hex(random_bytes(32));
            
            $userData = [
                'username' => $username,
                'user_password' => phpbb_hash($randomPassword),
                'user_email' => $email,
                'group_id' => 2, // REGISTERED
                'user_type' => 0, // NORMAL
                'user_actkey' => '', // No activation needed
                'user_inactive_reason' => 0,
                'user_inactive_time' => 0,
            ];
            
            $newId = user_add($userData, false); // false = suppress validation error array
            
            if (is_int($newId) && $newId > 0) {
                $user_id = $newId;
                $this->flog('[auth0] created user user_id=' . $user_id . ' username=' . $username);
            } else {
                $this->flog('[auth0] user_add FAILED for username=' . $username . ' result=' . var_export($newId, true));
                return false;
            }
        }

        if ($user_id > 0) {
            // Insert mapping (ignore if a race created it)
            $table = (defined('OAUTH_ACCOUNTS_TABLE') ? OAUTH_ACCOUNTS_TABLE : 'phpbb_oauth_accounts');
            $sql = "INSERT IGNORE INTO $table (user_id,provider,oauth_provider_id) VALUES (".(int)$user_id.", '".$this->db->sql_escape($provider)."', '".$this->db->sql_escape($external)."')";
            $this->db->sql_query($sql);
            $affected = $this->db->sql_affectedrows();
            $this->flog('[auth0] inserted oauth mapping for user_id=' . (int)$user_id . ' affected_rows=' . $affected);
            return true;
        }
        $this->flog('[auth0] ensure_oauth_mapping failed: user_id=0');
        return false;
    }
    public function on_oauth_login_after($event)
    {
        $this->assign_groups_from_auth0($event);
    }

    public function on_oauth_link_after($event)
    {
        $this->assign_groups_from_auth0($event);
    }

    protected function assign_groups_from_auth0($event)
    {
        $claims = $event['service']->get_user_identity(); // includes /userinfo payload
        $claim_name = getenv('AUTH0_GROUPS_CLAIM') ?: 'https://forum.trigpointing.uk/phpbb_groups';
        $roles = [];
        if (isset($claims[$claim_name]) && is_array($claims[$claim_name])) {
            $roles = $claims[$claim_name];
        }

        // Map from Auth0 role names to phpBB built-in groups; overridable by JSON in env
        $map = ['forum-admin' => 'ADMINISTRATORS', 'forum-mod' => 'GLOBAL_MODERATORS'];
        $env_map = getenv('AUTH0_GROUP_MAP_JSON');
        if ($env_map) { $j = json_decode($env_map, true); if (is_array($j)) $map = $j; }

        $uid = (int)$event['user_row']['user_id'];
        foreach ($map as $role => $group_name) {
            $gid = $this->group_id($group_name);
            if (!$gid) continue;
            if (in_array($role, $roles, true)) $this->ensure_member($gid, $uid);
            else                                 $this->remove_member($gid, $uid);
        }
    }
    protected function group_id($name){
        $sql="SELECT group_id FROM phpbb_groups WHERE group_name='".$this->db->sql_escape($name)."'";
        $res=$this->db->sql_query($sql); $row=$this->db->sql_fetchrow($res); $this->db->sql_freeresult($res);
        return $row['group_id'] ?? 0;
    }
    protected function ensure_member($gid,$uid){
        $sql="INSERT IGNORE INTO phpbb_user_group (group_id,user_id,group_leader,user_pending) VALUES ($gid,$uid,0,0)";
        $this->db->sql_query($sql);
    }
    protected function remove_member($gid,$uid){
        $sql="DELETE FROM phpbb_user_group WHERE group_id=$gid AND user_id=$uid";
        $this->db->sql_query($sql);
    }
}
