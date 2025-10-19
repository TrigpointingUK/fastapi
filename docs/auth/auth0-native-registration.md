# Auth0 Native Registration Setup Guide

## Overview

This guide documents the Auth0 native registration flow where new users sign up directly through Auth0 (rather than the legacy system), and are automatically provisioned in the website's database via a webhook endpoint.

## Architecture

```
User → Auth0 Signup → Auth0 Database → Post-Registration Action → FastAPI Webhook → Database
                                                                                       ↓
User ← Auth0 Login ← Auth0 Token ← FastAPI API ← Database User ← Created
```

## Key Features

- **Native Auth0 Registration**: Users register via Auth0 Universal Login (email + password)
- **Automatic Provisioning**: Post-registration Action calls FastAPI webhook
- **Nickname-Based Display Names**: Uses Auth0 `nickname` (not `username`) to allow spaces and special characters
- **Profile Management**: Users can update name/email which syncs back to Auth0
- **Database-Only Fields**: Firstname and surname are stored only in the database
- **Legacy Compatibility**: Random `cryptpw` field for legacy cookie support

**Important**: Auth0 `username` field is NOT used because it has restrictions (no spaces, special characters). Instead, the `user.name` database column maps to Auth0 `nickname`, which allows flexible display names that your users already have.

## Database Schema

### Fields Synced from Auth0
- `name` (nickname/display name) - syncs bidirectionally with Auth0 `nickname`
- `email` - syncs bidirectionally
- `auth0_user_id` - set once at creation

### Database-Only Fields
- `firstname` - user sets after registration
- `surname` - user sets after registration
- `cryptpw` - random token for legacy compatibility
- Other profile fields

## API Endpoints

### POST /v1/users
**Purpose**: Create new user from Auth0 webhook  
**Authentication**: M2M token (Management API audience)  
**Called by**: Auth0 Post User Registration Action

**Request Body**:
```json
{
  "username": "nickname",
  "email": "user@example.com",
  "auth0_user_id": "auth0|abc123"
}
```

**Response (201)**:
```json
{
  "id": 123,
  "name": "nickname",
  "email": "user@example.com",
  "auth0_user_id": "auth0|abc123"
}
```

**Error Responses**:
- 401: Invalid/missing M2M token
- 409: Username, email, or auth0_user_id already exists
- 422: Invalid request body
- 500: Database error

### PATCH /v1/users/me
**Purpose**: Update user profile with Auth0 sync  
**Authentication**: User Auth0 token

**Synced to Auth0**:
- `name` → nickname
- `email` → email (marked as verified)

**Database Only**:
- `firstname`
- `surname`
- `homepage`
- `about`
- Preference fields

## Configuration

### Environment Variables (Local Development)

Add to `.env` for local testing:

```bash
# Auth0 Webhook Configuration
AUTH0_WEBHOOK_M2M_AUDIENCE=https://your-domain.auth0.com/api/v2/
AUTH0_API_IDENTIFIER=https://api.trigpointing.me/v1/
```

### AWS Secrets Manager (Staging/Production)

Add to `fastapi-staging-app-secrets` and `fastapi-production-app-secrets`:

```json
{
  "AUTH0_WEBHOOK_M2M_AUDIENCE": "https://your-domain.auth0.com/api/v2/",
  "AUTH0_API_IDENTIFIER": "https://api-staging.trigpointing.me/v1/"
}
```

## Auth0 Configuration

### 1. Enable Database Connection Registration

In Auth0 Dashboard → Authentication → Database:
1. Select your connection (e.g., "Username-Password-Authentication")
2. Settings tab:
   - Enable "Disable Sign Ups" → **OFF** (enable signups)
   - Enable "Requires Username" → **OFF** (usernames have restrictions; use nickname instead)
3. Save changes

### 2. Configure Signup Form

**Minimum signup form (email + password only)**:
- Email (required, login identifier)
- Password (required)

**Important**: 
- Do NOT enable "Requires Username" - Auth0 usernames don't allow spaces or special characters
- Your `user.name` column maps to Auth0 `nickname` (which allows spaces, special characters, etc.)
- Nickname can be set after registration via the Post-Registration Action or by the user later

**Do NOT collect at signup**:
- Firstname
- Surname  
- Other profile fields

These are database-only and user sets them later.

### 2a. Nickname Handling Strategy

Since Auth0 signup only requires email/password, you have two options for nicknames:

**Option 1: Generate from email (Implemented)**
- Action generates nickname from email prefix (e.g., "user@example.com" → "user")
- On collision, appends random 6-digit number (e.g., "user432524")
- This avoids predictable patterns and DoS attacks on common names
- User can change it later via `PATCH /v1/users/me` to something more memorable

**Option 2: Collect via Universal Login customization**
- Customize Auth0 Universal Login to collect nickname at signup
- Requires Auth0 Custom Login Page or New Universal Login customization
- More complex but provides better UX

### 3. Create M2M Application for Webhook

If not already done via Terraform:
1. Applications → Create Application
2. Name: "FastAPI Webhook Client"
3. Type: Machine to Machine
4. Authorize for your API
5. Note Client ID and Secret (store in AWS Secrets Manager)

### 4. Create Post User Registration Action

**Code** (Actions → Library → Build Custom → Post User Registration):

```javascript
exports.onExecutePostUserRegistration = async (event, api) => {
  const axios = require('axios');
  
  // Generate base nickname from email prefix
  // Auth0 signup only collects email/password by default
  // Nickname allows spaces and special characters (unlike username)
  const baseNickname = event.user.nickname || event.user.email.split('@')[0];
  
  // Try to create user, handling username collisions with random suffixes
  let nickname = baseNickname;
  let attempt = 0;
  const maxAttempts = 10;
  
  while (attempt < maxAttempts) {
    const payload = {
      username: nickname,  // Maps to user.name (nickname/display name)
      email: event.user.email,
      auth0_user_id: event.user.user_id
    };
    
    try {
      await axios.post(
        event.secrets.FASTAPI_URL + '/v1/users',
        payload,
        {
          headers: {
            'Authorization': `Bearer ${event.secrets.M2M_TOKEN}`,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        }
      );
      
      console.log('User provisioned successfully:', event.user.user_id, 'with nickname:', nickname);
      
      // Set the final nickname in Auth0 user metadata
      api.user.setUserMetadata('nickname', nickname);
      return; // Success!
      
    } catch (error) {
      if (error.response?.status === 409 && 
          error.response?.data?.detail?.toLowerCase().includes('username')) {
        // Username collision - generate random 6-digit suffix
        // This avoids predictable patterns and potential DoS attacks
        const randomSuffix = Math.floor(100000 + Math.random() * 900000);
        nickname = `${baseNickname}${randomSuffix}`;
        attempt++;
        console.log(`Username collision on attempt ${attempt}, trying: ${nickname}`);
      } else {
        // Other error - log but don't fail registration
        console.error('User provisioning failed:', error.response?.data || error.message);
        console.error('User registered in Auth0 but not in database. Manual sync may be required.');
        return;
      }
    }
  }
  
  console.error('Failed to find unique username after', maxAttempts, 'attempts for user:', event.user.user_id);
  console.error('User registered in Auth0 but not in database. Manual provisioning required.');
};
```

**Dependencies**:
- axios: latest

**Secrets**:
- `FASTAPI_URL`: Your API URL (e.g., `https://api-staging.trigpointing.me`)
- `M2M_TOKEN`: M2M access token (obtain via client credentials flow)

**Deploy and Add to Flow**:
1. Deploy the Action
2. Actions → Flows → Post User Registration
3. Add custom action to flow
4. Apply

### 5. Obtaining M2M Token for Action

The M2M token should be obtained programmatically via client credentials flow:

```bash
curl --request POST \
  --url https://YOUR_DOMAIN.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"YOUR_M2M_CLIENT_ID",
    "client_secret":"YOUR_M2M_CLIENT_SECRET",
    "audience":"https://api.trigpointing.me/v1/",
    "grant_type":"client_credentials"
  }'
```

Store the returned `access_token` in Auth0 Action secrets as `M2M_TOKEN`.

**Important**: M2M tokens expire. Consider:
- Using long-lived tokens (24h+)
- Implementing token refresh in Action
- Monitoring Action logs for auth failures

## Terraform Setup

The complete Auth0 configuration can be managed via Terraform. See `terraform/common/auth0.tf` for:
- Database connection configuration
- M2M application setup
- Post User Registration Action definition
- Action secrets configuration

Import existing resources:
```bash
cd terraform/common
./import-auth0.sh
```

## Testing

### Unit Tests
```bash
# Test CRUD function
pytest tests/test_crud_user_creation.py -v

# Test POST endpoint
pytest tests/test_user_provisioning.py -v

# Test PATCH endpoint with sync
pytest tests/test_user_profile_sync.py -v

# Integration tests
pytest tests/test_auth0_provisioning_flow.py -v
```

### Manual Testing

1. **Test Webhook Endpoint**:
```bash
# Get M2M token
M2M_TOKEN=$(curl -s --request POST \
  --url https://YOUR_DOMAIN.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id":"YOUR_M2M_CLIENT_ID",
    "client_secret":"YOUR_M2M_CLIENT_SECRET",
    "audience":"YOUR_API_AUDIENCE",
    "grant_type":"client_credentials"
  }' | jq -r '.access_token')

# Test user creation
curl -X POST https://api-staging.trigpointing.me/v1/users \
  -H "Authorization: Bearer $M2M_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "auth0_user_id": "auth0|test123"
  }'
```

2. **Test Registration Flow**:
- Go to Auth0 Universal Login
- Click "Sign Up"
- Enter email and password (nickname generated from email by Action)
- Verify user created in database:
  ```sql
  SELECT id, name, email, auth0_user_id, firstname, surname, cryptpw 
  FROM user 
  WHERE email = 'test@example.com';
  ```
- Verify `name` column contains generated nickname (e.g., email prefix)

3. **Test Profile Update**:
- Get user token
- Update profile via API:
  ```bash
  curl -X PATCH https://api-staging.trigpointing.me/v1/users/me \
    -H "Authorization: Bearer $USER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "firstname": "Test",
      "surname": "User",
      "name": "newusername"
    }'
  ```
- Verify name synced to Auth0 in dashboard

## Troubleshooting

### Issue: User Registered in Auth0 But Not in Database

**Symptom**: User can log in to Auth0 but API returns 401 or user not found.

**Cause**: Post-registration Action failed or wasn't triggered.

**Solutions**:
1. Check Auth0 Action logs for errors
2. Verify M2M token is valid
3. Verify FASTAPI_URL is correct
4. Check FastAPI logs for webhook calls
5. Manually provision user via API

**Fallback**: Existing legacy migration logic will sync user on first API call.

### Issue: Name/Email Update Not Syncing to Auth0

**Symptom**: Database updated but Auth0 still shows old value.

**Cause**: Auth0 Management API call failed.

**Solutions**:
1. Check FastAPI logs for Auth0 sync errors
2. Verify M2M client has `update:users` permission
3. Database is still updated - user can continue using site
4. Manual sync via Auth0 Management API if needed

### Issue: M2M Token Expired

**Symptom**: Webhook returns 401, new registrations fail to provision.

**Cause**: M2M token in Action secrets expired.

**Solutions**:
1. Generate new M2M token via client credentials flow
2. Update Action secret `M2M_TOKEN`
3. Consider implementing token refresh in Action

### Issue: Duplicate User Errors

**Symptom**: 409 conflict when creating user.

**Cause**: Username, email, or auth0_user_id already exists.

**Solutions**:
1. Check if user already exists in database
2. Verify Auth0 Action not being triggered multiple times
3. Check for race conditions in concurrent registrations

### Issue: Users Assigned Random Number Suffixes

**Symptom**: User gets nickname like "john432524" instead of "john".

**Cause**: Username collision - "john" already taken. Action automatically appended random 6-digit number.

**Solutions**:
1. This is expected behaviour for common email prefixes
2. User can change nickname via:
   ```bash
   PATCH /v1/users/me
   {
     "name": "preferred_nickname"
   }
   ```
3. New nickname must be unique - API returns 409 if taken
4. Consider UX: show onboarding prompt suggesting users customize their nickname
5. The random suffix prevents DoS attacks on common names

## Migration Path

### Phase 1: Dual Mode (Current)
- Legacy users: Register via legacy system → migrate to Auth0 on login
- New users: Still use legacy registration

### Phase 2: Auth0 Native (Implementing)
- Legacy users: Continue to migrate on login
- New users: Register via Auth0 → webhook creates database user

### Phase 3: Full Auth0 (Future)
- All users in Auth0
- Legacy registration disabled
- Database user table remains for profile/preferences

## Security Considerations

1. **M2M Token**: Store securely, rotate regularly
2. **Webhook Endpoint**: Protected by M2M token validation
3. **Rate Limiting**: Consider Cloudflare rate limiting (100 req/min)
4. **Monitoring**: Alert on webhook failures or high error rates
5. **Audit Logging**: All user creation/updates logged

## Monitoring

### Metrics to Track
- User registration success rate
- Webhook call success rate
- Auth0 sync success rate
- Time from Auth0 registration to database provisioning

### CloudWatch Logs
Search for:
- `User created via Auth0 webhook`
- `User creation failed`
- `Auth0 sync failed`
- `M2M token validation failed`

### Auth0 Logs
Monitor:
- Post User Registration Action executions
- Action failures
- Webhook errors in Action logs

## References

- [Auth0 Actions Documentation](https://auth0.com/docs/actions)
- [Auth0 Management API](https://auth0.com/docs/api/management/v2)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- Project: `app/api/v1/endpoints/users.py` (webhook endpoint)
- Project: `app/crud/user.py` (user creation logic)
- Project: `terraform/common/auth0.tf` (infrastructure as code)

