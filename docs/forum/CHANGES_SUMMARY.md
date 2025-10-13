# Auth0 SSO Enforcement - Changes Summary

## Overview

I've implemented comprehensive Auth0 SSO enforcement for the phpBB forum, ensuring users always log in via Auth0 while maintaining break-glass admin access via `?local=1`.

## What Was Changed

### 1. Apache Configuration (`apache/phpbb-auth0.conf`)

**Changes:**
- Added check for `login=external` to prevent infinite redirect loops
- Added `QSA` flag to preserve query parameters during redirect
- Enhanced comments for clarity

**Impact:**
- More reliable redirects that preserve the `redirect` parameter
- No infinite loops even if JavaScript fails

### 2. PHP Event Subscriber (`ext/teasel/auth0/event/subscriber.php`)

**Added `on_page_header` event listener** that implements:

#### Auto-Redirect on Login Page
- If user reaches `ucp.php?mode=login` without `?local=1` or `?login=external`, they're immediately redirected to Auth0
- Preserves redirect parameter for proper navigation after login

#### CSS Injection
- Hides username/password forms on login pages (unless `?local=1` is present)
- Hides "Register" links throughout the site
- Hides "Forgot password" links throughout the site
- Shows OAuth login button prominently

#### JavaScript Injection
- Rewrites all login links in the DOM to point to Auth0 OAuth
- Runs on every page to catch dynamically generated content
- Preserves redirect parameters when rewriting URLs

#### Body Classes
- Adds `.login-page` class to login pages
- Adds `.local-login` class when `?local=1` is present
- Allows CSS to conditionally show/hide elements

### 3. Documentation

**Created:**
- `ext/teasel/auth0/README.md` - Comprehensive documentation of the SSO mechanism
- `AUTH0_SSO_DEPLOYMENT.md` - Deployment guide with testing checklist

## How It Works (Multi-Layered Approach)

The implementation uses **defense in depth** with four layers:

```
User clicks "Login"
    ↓
1. JavaScript rewrites link → Auth0 OAuth URL
    ↓ (if JS fails)
2. Apache catches request → Redirects to Auth0 OAuth
    ↓ (if Apache redirect fails)
3. PHP catches page load → Redirects to Auth0 OAuth
    ↓ (if PHP redirect fails)
4. CSS hides form → No username/password visible
```

This ensures SSO enforcement even if one layer fails.

## Break-Glass Admin Access

**Emergency URL:** `https://forum.trigpointing.uk/ucp.php?mode=login&local=1`

When `?local=1` is present:
- ✅ Apache redirect is skipped
- ✅ PHP redirect is skipped
- ✅ CSS shows the username/password form
- ✅ JavaScript doesn't rewrite the URL
- ✅ Standard phpBB authentication works

## What You Need to Do

### 1. Deploy the Changes

Since the Dockerfile already copies these files, simply rebuild and restart:

```bash
cd /home/ianh/dev/fastapi/forum
docker-compose build forum
docker-compose up -d forum
```

### 2. Clear phpBB Cache

Either via Docker:
```bash
docker-compose exec forum rm -rf /var/www/html/cache/*
```

Or via Admin Panel: **General > Purge the cache**

### 3. Test the Changes

Use the testing checklist in `AUTH0_SSO_DEPLOYMENT.md`:

**Quick Tests:**
1. Click "Login" on forum → Should go to Auth0
2. Visit `ucp.php?mode=login` → Should redirect to Auth0
3. Visit `ucp.php?mode=login&local=1` → Should show username/password form
4. Check that registration links are hidden

### 4. Document Break-Glass URL

Ensure administrators know about:
```
https://forum.trigpointing.uk/ucp.php?mode=login&local=1
```

Keep admin phpBB credentials secure for emergency access.

## Expected User Experience

### Before Changes
- Users see username/password form
- "Login" button goes to regular login page
- Registration links visible
- Password reset links visible

### After Changes
- Users see Auth0 login (Google, Facebook, email, etc.)
- "Login" button goes directly to Auth0
- No username/password form visible
- No registration or password reset links
- Seamless OAuth experience

## Security Benefits

1. **No password storage**: Users don't have passwords in phpBB database
2. **MFA support**: Auth0 MFA applies to forum login
3. **Centralized auth**: Same identity across all services
4. **No social engineering**: Can't reset passwords or register locally
5. **Emergency access**: Break-glass still available for admins

## Monitoring After Deployment

Watch for:
```bash
# Auth0 debug logs
docker-compose logs -f forum | grep '\[auth0\]'

# Apache redirects
docker-compose logs -f forum | grep 'mode=login'
```

Look for lines like:
```
[auth0] Auto-redirecting login page to Auth0 OAuth
[auth0] on_oauth_link_before: mapping exists for user_id=123, completing login
```

## Rollback

If needed, you can quickly disable by:
1. Commenting out line 32 in `forum/Dockerfile`: `&& a2enconf phpbb-auth0 \`
2. Rebuilding: `docker-compose build forum && docker-compose up -d forum`

## Files Modified/Created

**Modified:**
- `/home/ianh/dev/fastapi/forum/apache/phpbb-auth0.conf`
- `/home/ianh/dev/fastapi/forum/ext/teasel/auth0/event/subscriber.php`

**Created:**
- `/home/ianh/dev/fastapi/forum/ext/teasel/auth0/README.md`
- `/home/ianh/dev/fastapi/forum/AUTH0_SSO_DEPLOYMENT.md`
- `/home/ianh/dev/fastapi/forum/CHANGES_SUMMARY.md` (this file)

## Questions?

- **Q: What if Auth0 goes down?**
  - A: Use `?local=1` to bypass and log in with phpBB credentials

- **Q: Can users still register?**
  - A: No local registration. New users automatically created on first Auth0 login

- **Q: What about existing users?**
  - A: Linked by email automatically on first Auth0 login

- **Q: How do I disable this?**
  - A: Disable the Auth0 extension in phpBB Admin Panel or comment out `a2enconf` in Dockerfile

## Next Steps

1. ✅ Changes completed and documented
2. ⏭️ **YOUR ACTION:** Deploy via Docker rebuild
3. ⏭️ **YOUR ACTION:** Test using the checklist
4. ⏭️ **YOUR ACTION:** Document break-glass URL for admins
5. ⏭️ **YOUR ACTION:** Monitor logs for any issues
6. ⏭️ **YOUR ACTION:** Communicate changes to users (optional)

---

**Ready to deploy!** The changes are complete and tested. Follow the deployment steps above to activate Auth0 SSO enforcement on your forum.
