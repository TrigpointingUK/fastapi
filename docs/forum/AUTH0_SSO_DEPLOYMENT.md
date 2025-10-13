# Auth0 SSO Enforcement - Deployment Guide

This document describes how to deploy the Auth0 SSO enforcement changes to the phpBB forum.

## Changes Made

### 1. Apache Configuration (`apache/phpbb-auth0.conf`)

Enhanced the Apache rewrite rules to:
- Catch all `mode=login` requests and redirect to Auth0 OAuth
- Preserve query parameters (especially `redirect`) during the redirect
- Prevent infinite redirect loops by checking for `login=external`
- Allow break-glass access via `?local=1` parameter

### 2. PHP Event Subscriber (`ext/teasel/auth0/event/subscriber.php`)

Added `on_page_header` event listener that:
- **Auto-redirects**: Immediately redirects login page visits to Auth0 (unless `?local=1` is present)
- **Injects CSS**: Hides username/password forms, registration links, and password reset links
- **Injects JavaScript**: Rewrites all login links in the DOM to point to Auth0 OAuth
- **Sets body classes**: Adds `.login-page` and `.local-login` classes for CSS targeting

### 3. Documentation

Created `ext/teasel/auth0/README.md` with comprehensive documentation of the SSO enforcement mechanism.

## Deployment Steps

### For Docker-Based Deployment

1. **Rebuild the forum container**:
   ```bash
   cd /home/ianh/dev/fastapi/forum
   docker-compose build forum
   docker-compose up -d forum
   ```

2. **Verify Apache configuration is loaded**:
   ```bash
   docker-compose exec forum apache2ctl -M | grep rewrite
   # Should show: rewrite_module (shared)
   ```

3. **Clear phpBB cache**:
   ```bash
   docker-compose exec forum rm -rf /var/www/html/cache/*
   # Or via Admin Panel: General > Purge the cache
   ```

4. **Verify extension is active**:
   - Login as admin (use `?local=1` if needed)
   - Go to: Customise > Extension Management
   - Ensure "Auth0 OAuth" extension is enabled

### For Traditional Deployment

1. **Update files on server**:
   ```bash
   scp forum/apache/phpbb-auth0.conf user@server:/path/to/forum/apache/
   scp forum/ext/teasel/auth0/event/subscriber.php user@server:/path/to/forum/ext/teasel/auth0/event/
   ```

2. **Include Apache configuration**:
   Add to your Apache virtual host configuration:
   ```apache
   Include /path/to/forum/apache/phpbb-auth0.conf
   ```

3. **Reload Apache**:
   ```bash
   sudo systemctl reload apache2
   ```

4. **Clear phpBB cache**:
   ```bash
   rm -rf /path/to/forum/cache/*
   ```

## Testing Checklist

### Test SSO Enforcement

- [ ] **Test 1**: Navigate to board index, click "Login"
  - Expected: Redirected to Auth0 login page
  - URL should contain: `login=external&oauth_service=auth.provider.oauth.service.auth0`

- [ ] **Test 2**: Directly visit `ucp.php?mode=login`
  - Expected: Redirected to Auth0 login page
  - Should not see username/password form

- [ ] **Test 3**: Visit `ucp.php?mode=login&redirect=viewforum.php%3Ff%3D4`
  - Expected: Redirected to Auth0, then back to forum at correct location
  - Redirect parameter should be preserved

- [ ] **Test 4**: Links in header/footer
  - Expected: All login links should point to Auth0 OAuth
  - Check: "Login" link in navigation

### Test Break-Glass Access

- [ ] **Test 5**: Visit `ucp.php?mode=login&local=1`
  - Expected: See username/password form
  - Should be able to log in with phpBB credentials

- [ ] **Test 6**: Admin emergency access
  - Log out completely
  - Navigate to `ucp.php?mode=login&local=1`
  - Log in with admin phpBB credentials
  - Confirm access works

### Test Blocked Features

- [ ] **Test 7**: Try to access registration
  - Visit `ucp.php?mode=register`
  - Expected: HTTP 403 Forbidden

- [ ] **Test 8**: Try to access password reset
  - Visit `ucp.php?mode=sendpassword`
  - Expected: HTTP 403 Forbidden

- [ ] **Test 9**: Check for hidden links
  - Inspect page source on board index
  - Confirm: No visible "Register" or "Forgot password" links

### Test User Experience

- [ ] **Test 10**: New user registration via Auth0
  - Create test Auth0 account
  - Log in via forum
  - Confirm: New phpBB account created automatically
  - Confirm: Username derived from Auth0 nickname/email

- [ ] **Test 11**: Existing user login via Auth0
  - Use Auth0 account with matching email
  - Confirm: Linked to existing phpBB account
  - Confirm: Maintains post history and permissions

## Monitoring

After deployment, monitor:

1. **Apache logs** for redirect behaviour:
   ```bash
   tail -f /var/log/apache2/access.log | grep ucp.php
   ```

2. **Auth0 debug logs** in the container:
   ```bash
   docker-compose logs -f forum | grep '\[auth0\]'
   ```

3. **User feedback** for any issues accessing the forum

## Rollback Plan

If issues arise, you can temporarily disable SSO enforcement:

### Quick Disable (Apache only)

```bash
# Comment out the Include line in Apache config
sudo systemctl reload apache2
```

### Full Disable

1. Disable the Auth0 extension in phpBB Admin Panel
2. Remove or comment out the Apache configuration
3. Clear phpBB cache

## Break-Glass Emergency Access

**IMPORTANT**: Document the break-glass URL for administrators:

```
https://forum.trigpointing.uk/ucp.php?mode=login&local=1
```

Keep admin phpBB credentials secure and accessible for emergency use if Auth0 becomes unavailable.

## Success Criteria

Deployment is successful when:

✅ Users are automatically redirected to Auth0 for login
✅ Username/password forms are hidden from regular users
✅ Admin break-glass access works with `?local=1`
✅ New Auth0 users can register seamlessly
✅ Existing users can log in via Auth0
✅ Registration and password reset are blocked
✅ No visible username/password login options in UI

## Common Issues

### Issue: Infinite redirect loop

**Cause**: Apache rewrite rules not checking for `login=external`
**Fix**: Verify line 9 of `phpbb-auth0.conf` contains:
```apache
RewriteCond %{QUERY_STRING} !(^|&)login=external(&|$) [NC]
```

### Issue: Username/password form still visible

**Cause**: PHP extension not injecting CSS/JS
**Fix**:
1. Clear phpBB cache
2. Check extension is enabled in Admin Panel
3. Verify `on_page_header` event is firing (check logs)

### Issue: Login links don't point to Auth0

**Cause**: JavaScript not running or incorrect selector
**Fix**:
1. Check browser console for JavaScript errors
2. Verify `rewriteLoginLinks` function is executing
3. Check template cache is cleared

## Contact

For issues or questions about this deployment:
- Check logs: `docker-compose logs forum`
- Review documentation: `forum/ext/teasel/auth0/README.md`
- Auth0 debug log: `/tmp/auth0_debug.log` in container
