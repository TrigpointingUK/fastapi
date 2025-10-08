<?php
namespace teasel\auth0\event;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use phpbb\db\driver\driver_interface;
use phpbb\user;

class subscriber implements EventSubscriberInterface
{
    protected $db; protected $user;
    public function __construct(driver_interface $db, user $user) { $this->db=$db; $this->user=$user; }
    public static function getSubscribedEvents() {
        return [
            'core.auth_oauth_authenticate_after' => 'on_oauth_authenticate_after',
            'core.auth_oauth_login_after' => 'on_oauth_login_after',
            'core.auth_oauth_link_after' => 'on_oauth_link_after',
        ];
    }
    public function on_oauth_authenticate_after($event)
    {
        // Ensure an oauth mapping exists before phpBB prompts to link/register
        $service = $event['service'];
        if (!$service) return;
        $claims = $service->get_user_identity();
        $provider = method_exists($service, 'get_service_name') ? (string)$service->get_service_name() : 'auth0';
        $external = isset($claims['sub']) ? (string)$claims['sub'] : '';
        if ($external === '') return;

        // Already linked?
        $sql = "SELECT user_id FROM phpbb_oauth_accounts WHERE provider='".$this->db->sql_escape($provider)."' AND oauth_provider_id='".$this->db->sql_escape($external)."'";
        $res = $this->db->sql_query($sql);
        $row = $this->db->sql_fetchrow($res);
        $this->db->sql_freeresult($res);
        if ($row && (int)$row['user_id'] > 0) return;

        // Try to link by email if present
        $email = isset($claims['email']) ? (string)$claims['email'] : '';
        $user_id = 0;
        if ($email !== '') {
            $sql = "SELECT user_id FROM phpbb_users WHERE user_email='".$this->db->sql_escape($email)."' AND user_type <> 2"; // exclude anonymous
            $res = $this->db->sql_query($sql);
            $userRow = $this->db->sql_fetchrow($res);
            $this->db->sql_freeresult($res);
            if ($userRow && (int)$userRow['user_id'] > 0) {
                $user_id = (int)$userRow['user_id'];
            }
        }

        if ($user_id === 0) {
            // Create a new phpBB user using nickname as username
            global $phpbb_root_path, $phpEx;
            include_once($phpbb_root_path.'includes/functions_user.'.$phpEx);

            $nickname = isset($claims['nickname']) ? (string)$claims['nickname'] : '';
            $name = isset($claims['name']) ? (string)$claims['name'] : '';
            $username = $nickname !== '' ? $nickname : ($name !== '' ? $name : $email);
            if ($username === '') $username = 'user_'.substr(bin2hex(random_bytes(4)), 0, 8);

            $randomPassword = bin2hex(random_bytes(32));

            $userData = [
                'username' => $username,
                'user_password' => $randomPassword,
                'user_email' => $email,
                'group_id' => 2, // REGISTERED
                'user_type' => 0, // NORMAL
            ];
            $newId = user_add($userData);
            if (is_int($newId) && $newId > 0) $user_id = $newId;
        }

        if ($user_id > 0) {
            // Insert mapping (ignore if a race created it)
            $sql = "INSERT IGNORE INTO phpbb_oauth_accounts (user_id,provider,oauth_provider_id) VALUES (".(int)$user_id.", '".$this->db->sql_escape($provider)."', '".$this->db->sql_escape($external)."')";
            $this->db->sql_query($sql);
        }
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
