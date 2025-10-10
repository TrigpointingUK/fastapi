# Auth0 SSO Enforcement for phpBB

This extension enforces Auth0 as the primary authentication method for phpBB, with username/password login available only as a break-glass option for administrators.

## Features

1. **Auto-redirect to Auth0**: All login attempts are automatically redirected to Auth0 OAuth login
2. **Hidden username/password forms**: Login forms with username/password fields are hidden via CSS
3. **Rewritten login links**: JavaScript rewrites all login links throughout the site to point to Auth0
4. **Apache-level redirects**: Server-level redirects ensure all login URLs lead to Auth0
5. **Break-glass admin access**: Adding `?local=1` to any login URL allows traditional username/password login

## How It Works

### 1. Apache Redirects (`apache/phpbb-auth0.conf`)

The Apache configuration catches all `ucp.php?mode=login` requests and redirects them to the Auth0 OAuth service, unless:
- `?local=1` is present (break-glass admin login)
- `?login=external` is already present (already an OAuth request)

Registration and password reset endpoints are blocked entirely (return HTTP 403).

### 2. PHP Event Listeners (`event/subscriber.php`)

The extension subscribes to `core.page_header` and:
- **Auto-redirects**: If a user reaches the login page without `?local=1`, they're immediately redirected to Auth0
- **Injects CSS**: Hides username/password forms, register links, and password reset links site-wide
- **Injects JavaScript**: Rewrites all login links in the DOM to point to Auth0 OAuth

### 3. OAuth Account Mapping

The extension automatically:
- Links Auth0 accounts to existing phpBB users by email
- Creates new phpBB users for first-time Auth0 logins
- Syncs group memberships from Auth0 claims
- Handles the OAuth flow to complete user sessions

## Break-Glass Admin Login

If Auth0 is unavailable or you need emergency access, administrators can:

1. Access the login page with `?local=1`: `https://forum.example.com/ucp.php?mode=login&local=1`
2. The username/password form will be visible
3. Standard phpBB authentication will be used

**Important**: Keep admin credentials secure and documented for emergency use.

## Configuration

### Required Apache Configuration

Include `apache/phpbb-auth0.conf` in your Apache virtual host configuration:

```apache
Include /path/to/forum/apache/phpbb-auth0.conf
```

Or if running in Docker, mount it in the container:

```yaml
volumes:
  - ./forum/apache/phpbb-auth0.conf:/etc/apache2/conf-enabled/phpbb-auth0.conf
```

### Environment Variables

- `AUTH0_GROUPS_CLAIM`: Custom claim name for phpBB groups (default: `https://forum.trigpointing.uk/phpbb_groups`)
- `AUTH0_GROUP_MAP_JSON`: JSON mapping of Auth0 roles to phpBB groups (default: `{"forum-admin": "ADMINISTRATORS", "forum-mod": "GLOBAL_MODERATORS"}`)

### phpBB OAuth Configuration

In phpBB Admin Panel > Client Communication > Authentication:
1. Enable the Auth0 OAuth provider
2. Configure Client ID and Client Secret from Auth0
3. Set the OAuth service name to: `auth.provider.oauth.service.auth0`

## User Experience

### For Regular Users

1. Click "Login" anywhere on the forum
2. Automatically redirected to Auth0 login page
3. After Auth0 authentication, redirected back to forum as logged-in user
4. No username/password forms visible

### For Administrators (Emergency)

1. Navigate to: `ucp.php?mode=login&local=1`
2. Username/password form is visible
3. Log in with phpBB credentials
4. Use this only when Auth0 is unavailable

## Security Considerations

1. **Defense in depth**: Multiple layers (Apache, PHP redirect, JavaScript, CSS) ensure SSO enforcement
2. **Emergency access**: `?local=1` parameter provides controlled break-glass access
3. **No registration**: Local registration is blocked at Apache level
4. **No password reset**: Password reset is blocked to prevent social engineering

## Testing

After deployment, verify:

1. ✅ Login links redirect to Auth0
2. ✅ Direct navigation to `ucp.php?mode=login` redirects to Auth0
3. ✅ Username/password forms are hidden
4. ✅ `ucp.php?mode=login&local=1` shows username/password form
5. ✅ Registration links are hidden/blocked
6. ✅ Password reset links are hidden/blocked

## Troubleshooting

### Users see username/password form

- Check Apache configuration is loaded: `apache2ctl -S`
- Check PHP extension is enabled: Admin Panel > Extensions
- Clear phpBB cache: `rm -rf cache/*`

### Apache redirects not working

- Verify `mod_rewrite` is enabled: `a2enmod rewrite && systemctl reload apache2`
- Check Apache error logs: `tail -f /var/log/apache2/error.log`
- Ensure `.htaccess` or virtual host allows `RewriteEngine On`

### JavaScript not rewriting links

- Check browser console for errors
- Verify template cache is cleared
- Check that `core.page_header` event is firing (check `/tmp/auth0_debug.log`)

## Logging

The extension logs to:
- `error_log` (Docker stdout/stderr)
- `/tmp/auth0_debug.log` (fallback)

Look for lines prefixed with `[auth0]` for debugging.

