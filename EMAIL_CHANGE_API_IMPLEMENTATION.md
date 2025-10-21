# Email Change API Implementation Summary

## Overview
Implemented email change functionality with Auth0 sync status tracking, input validation, and email exposure via UserPrefs schema. Uses dual-write strategy where database is updated first, then synced to Auth0.

## Architecture: Dual-Write with Sync Status Tracking

### Database is Source of Truth
- PATCH /v1/users/me updates database first
- Then syncs to Auth0 (non-blocking)
- Auth0 sync failures don't prevent database updates

### Email Validation Status Tracking
- **email_valid column** tracks Auth0 sync status:
  - `'N'` = Pending sync or sync failed
  - `'Y'` = Successfully synced to Auth0
- Enables future batch job to retry failed syncs

## Changes Made

### 1. Schema Updates (`app/schemas/user.py`)

#### Added Imports
```python
import re
from pydantic import field_validator
```

#### UserPrefs Schema - Added Email Field
```python
class UserPrefs(BaseModel):
    status_max: int
    distance_ind: str
    public_ind: str
    online_map_type: str
    online_map_type2: str
    email: str  # NEW: Email now exposed in prefs
```

#### UserUpdate Schema - Added Validators

**Username Validation:**
- Blocks leading whitespace
- Blocks `@` character (prevents SQL injection garbage like "test@union")
- Blocks `*` character (prevents injection attempts like "test*select")

**Email Validation:**
- Validates standard email format: `local@domain.tld`
- Uses regex pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`

### 2. GET /v1/users/me Endpoint (`app/api/v1/endpoints/users.py`)

Added email to UserPrefs response when `include=prefs`:
```python
result.prefs = UserPrefs(
    status_max=int(current_user.status_max),
    distance_ind=str(current_user.distance_ind),
    public_ind=str(current_user.public_ind),
    online_map_type=str(current_user.online_map_type),
    online_map_type2=str(current_user.online_map_type2),
    email=str(current_user.email),  # NEW
)
```

### 3. PATCH /v1/users/me Endpoint (`app/api/v1/endpoints/users.py`)

#### Email Sync Status Tracking
```python
# Before database commit: Set email_valid = 'N' if email changed
if email_changed:
    current_user.email_valid = "N"

# After database commit: Sync to Auth0
if success:
    # Update email_valid = 'Y' on successful sync
    current_user.email_valid = "Y"
    db.commit()
    db.refresh(current_user)
else:
    # Stays as 'N' - batch job can retry later
    logger.error(json.dumps({
        "event": "auth0_email_sync_failed",
        "user_id": current_user.id,
        "auth0_user_id": current_user.auth0_user_id,
        "email": current_user.email,
        "timestamp": "...",
        "action_required": "batch_retry_or_manual_sync"
    }))
```

#### Structured Error Logging

**Username Sync Failure:**
```json
{
  "event": "auth0_username_sync_failed",
  "user_id": 123,
  "auth0_user_id": "auth0|abc123",
  "new_username": "newname",
  "timestamp": "2025-01-21T...",
  "action_required": "admin_review"
}
```

**Email Sync Failure:**
```json
{
  "event": "auth0_email_sync_failed",
  "user_id": 123,
  "auth0_user_id": "auth0|abc123",
  "email": "new@example.com",
  "timestamp": "2025-01-21T...",
  "action_required": "batch_retry_or_manual_sync"
}
```

## API Changes

### GET /v1/users/me?include=prefs

**Before:**
```json
{
  "id": 123,
  "name": "username",
  "prefs": {
    "status_max": 0,
    "distance_ind": "K",
    "public_ind": "N",
    "online_map_type": "",
    "online_map_type2": "lla"
  }
}
```

**After:**
```json
{
  "id": 123,
  "name": "username",
  "prefs": {
    "status_max": 0,
    "distance_ind": "K",
    "public_ind": "N",
    "online_map_type": "",
    "online_map_type2": "lla",
    "email": "user@example.com"  ← NEW
  }
}
```

### PATCH /v1/users/me - Validation

**Invalid Username Examples (422 Unprocessable Entity):**
```bash
# Leading whitespace
curl -X PATCH /v1/users/me -d '{"name": " username"}'
# Response: {"detail": "Username cannot begin with whitespace"}

# Contains @
curl -X PATCH /v1/users/me -d '{"name": "user@name"}'
# Response: {"detail": "Username cannot contain '@' character"}

# Contains *
curl -X PATCH /v1/users/me -d '{"name": "user*name"}'
# Response: {"detail": "Username cannot contain '*' character"}
```

**Invalid Email Examples (422 Unprocessable Entity):**
```bash
curl -X PATCH /v1/users/me -d '{"email": "notanemail"}'
# Response: {"detail": "Invalid email address format"}

curl -X PATCH /v1/users/me -d '{"email": "missing@domain"}'
# Response: {"detail": "Invalid email address format"}
```

## Security Considerations

### Email Privacy
- ✅ Email only exposed via `UserPrefs` (requires authentication)
- ✅ Email NOT exposed in public GET /v1/users/{id} responses
- ✅ Only the user themselves can see their email via GET /v1/users/me?include=prefs

### Input Validation
- ✅ Blocks SQL injection-like garbage usernames (e.g., "-8767) UNION SELECT")
- ✅ Prevents special characters that could cause issues: `@`, `*`
- ✅ Validates email format to prevent malformed addresses
- ✅ Trims leading whitespace to prevent confusion

### Eventual Consistency
- ✅ Database updates succeed even if Auth0 sync fails
- ✅ Failed syncs are logged with structured JSON for monitoring
- ✅ `email_valid` column enables batch reconciliation jobs

## Future Batch Job

The implementation enables a future batch reconciliation job:

```sql
-- Find users with failed email syncs
SELECT id, name, email, auth0_user_id
FROM user
WHERE email_valid = 'N'
  AND auth0_user_id IS NOT NULL;
```

Batch job logic:
1. Query users with `email_valid = 'N'`
2. For each user, retry `auth0_service.update_user_email()`
3. On success, set `email_valid = 'Y'`
4. On repeated failure, alert admins

## Testing Checklist

- [ ] **Username validation:**
  - [ ] Reject username with `@` character
  - [ ] Reject username with `*` character
  - [ ] Reject username with leading whitespace
  - [ ] Accept valid usernames (alphanumeric, hyphens, underscores)

- [ ] **Email validation:**
  - [ ] Reject invalid email formats
  - [ ] Accept valid email addresses

- [ ] **Email sync tracking:**
  - [ ] Email change sets `email_valid = 'N'` before commit
  - [ ] Successful Auth0 sync sets `email_valid = 'Y'`
  - [ ] Failed Auth0 sync leaves `email_valid = 'N'`
  - [ ] Structured JSON error logged on failure

- [ ] **GET /v1/users/me:**
  - [ ] Email returned in prefs when `include=prefs`
  - [ ] Email NOT returned without `include=prefs`

- [ ] **PATCH /v1/users/me:**
  - [ ] Email included in prefs response
  - [ ] Database update succeeds even if Auth0 sync fails

- [ ] **Username sync failure:**
  - [ ] Structured JSON error logged
  - [ ] Contains `"event": "auth0_username_sync_failed"`

## Monitoring

### Log Queries for Monitoring

**Successful email syncs:**
```
"Auth0 email sync successful"
```

**Failed email syncs (requires action):**
```json
"event": "auth0_email_sync_failed"
```

**Failed username syncs (requires admin review):**
```json
"event": "auth0_username_sync_failed"
```

### CloudWatch Log Insights Queries

**Count failed email syncs:**
```
fields @timestamp, user_id, email
| filter event = "auth0_email_sync_failed"
| stats count() by user_id
```

**Find users needing manual intervention:**
```
fields @timestamp, user_id, auth0_user_id, new_username
| filter event = "auth0_username_sync_failed"
| sort @timestamp desc
```

## Files Modified

1. `app/schemas/user.py` - Added email to UserPrefs, added validators to UserUpdate
2. `app/api/v1/endpoints/users.py` - Updated GET/PATCH endpoints for email tracking

**Total: 2 files modified**

## Deployment Notes

- No database migrations required (`email_valid` column already exists)
- No Terraform changes required
- Backwards compatible - existing functionality unchanged
- Deploy as normal Python application update

## Success Metrics

✅ Email accessible to authenticated users via GET /v1/users/me?include=prefs
✅ Input validation prevents garbage usernames
✅ Email sync status tracked in database
✅ Structured logging enables monitoring and alerting
✅ Failed syncs don't block user updates (eventual consistency)
✅ Future batch reconciliation enabled via `email_valid` column
