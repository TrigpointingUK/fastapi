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
        return ['core.auth_oauth_login_after' => 'on_oauth_login_after'];
    }
    public function on_oauth_login_after($event)
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
