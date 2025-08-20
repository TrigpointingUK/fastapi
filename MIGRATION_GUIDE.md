# Migration Guide: PHP to FastAPI

This guide will help you gradually migrate your 20-year-old PHP/MySQL website to the new FastAPI-based architecture.

## Overview

The migration strategy is designed to be **gradual and safe**, allowing you to migrate functionality piece by piece while maintaining service continuity.

## Phase 1: Initial Setup and Parallel Deployment

### 1.1 Deploy FastAPI Alongside PHP

1. **Set up the FastAPI application** using this project
2. **Configure database access** to your existing MySQL database
3. **Deploy to a subdomain** (e.g., `api.yourdomain.com`) while keeping PHP on main domain
4. **Verify both endpoints work**:
   - `GET /api/v1/tlog/trig-count/{trig_id}` - Test with existing data
   - `POST /api/v1/auth/login` - Test with existing user credentials

### 1.2 User Migration

Your existing users need to be compatible with the new authentication system:

```sql
-- Check if your user table has the required columns
DESCRIBE user;

-- If password_hash column doesn't exist, add it:
ALTER TABLE user ADD COLUMN password_hash VARCHAR(255);

-- Migrate existing passwords (if they're using a different format)
-- This example assumes you're moving from MD5/SHA1 to bcrypt
-- You'll need to force users to reset passwords or implement dual validation
```

### 1.3 Test Data Verification

```bash
# Test the tlog endpoint
curl "http://localhost:8000/api/v1/tlog/trig-count/1"

# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"

# Test protected endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v1/users/email/1"
```

## Phase 2: Identify and Plan Migration Targets

### 2.1 Audit Your PHP Application

Create an inventory of your PHP endpoints:

```bash
# Example audit script (adapt to your PHP structure)
find /path/to/php/app -name "*.php" -exec grep -l "mysql_query\|mysqli_query\|PDO" {} \;
```

Common patterns to look for:
- **User authentication/login**
- **Data retrieval APIs**
- **Form submissions**
- **File uploads**
- **Email functionality**
- **Payment processing**

### 2.2 Prioritize Migration Order

Recommended migration order:
1. **Read-only endpoints** (safest to start with)
2. **Authentication/session management**
3. **Simple CRUD operations**
4. **Complex business logic**
5. **File handling/uploads**
6. **Payment/sensitive operations** (last)

### 2.3 Document Current Functionality

For each PHP endpoint, document:
- **URL pattern**
- **HTTP method**
- **Input parameters**
- **Output format**
- **Database queries**
- **Business logic**
- **Dependencies**

## Phase 3: Migrate Core Endpoints

### 3.1 Add New FastAPI Endpoints

Example migration of a PHP user profile endpoint:

**PHP (existing):**
```php
// get_user_profile.php
$user_id = $_GET['user_id'];
$sql = "SELECT * FROM user WHERE user_id = $user_id";
$result = mysqli_query($conn, $sql);
echo json_encode(mysqli_fetch_assoc($result));
```

**FastAPI (new):**
```python
# app/api/v1/endpoints/users.py
@router.get("/profile/{user_id}", response_model=UserProfile)
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_id != user_id and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
```

### 3.2 Update Database Models

Add new models for additional tables:

```python
# app/models/legacy.py
class LegacyTable(Base):
    __tablename__ = "legacy_table_name"
    
    id = Column(Integer, primary_key=True)
    # Add columns matching your existing schema
```

### 3.3 Create Migration Scripts

Create scripts to help with data validation:

```python
# scripts/validate_migration.py
import requests

def compare_endpoints(php_url, fastapi_url, test_cases):
    """Compare responses between PHP and FastAPI endpoints"""
    for case in test_cases:
        php_response = requests.get(f"{php_url}/{case}")
        fastapi_response = requests.get(f"{fastapi_url}/{case}")
        
        assert php_response.status_code == fastapi_response.status_code
        # Add more validation as needed
```

## Phase 4: Frontend Integration

### 4.1 Gradual Frontend Migration

Use feature flags or routing to gradually switch to new endpoints:

```javascript
// JavaScript example
const USE_NEW_API = true; // Feature flag

function getUserProfile(userId) {
    const baseUrl = USE_NEW_API 
        ? 'https://api.yourdomain.com/api/v1' 
        : 'https://yourdomain.com/legacy';
    
    return fetch(`${baseUrl}/users/profile/${userId}`);
}
```

### 4.2 Update Authentication

Migrate from PHP sessions to JWT tokens:

```javascript
// Store JWT token
localStorage.setItem('token', response.data.access_token);

// Use token in requests
fetch('/api/v1/protected-endpoint', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
    }
});
```

## Phase 5: Database Changes

### 5.1 Schema Updates

Some changes might be needed for better FastAPI integration:

```sql
-- Add indexes for better performance
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_tlog_trig_id ON tlog(trig_id);

-- Add timestamp columns if not present
ALTER TABLE user ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE user ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

### 5.2 Data Migration Scripts

Create scripts for any necessary data transformations:

```python
# scripts/migrate_passwords.py
def migrate_user_passwords():
    """Migrate from old password format to bcrypt"""
    # Implementation depends on your current password storage
    pass
```

## Phase 6: Testing Strategy

### 6.1 Parallel Testing

Run both systems side by side and compare outputs:

```bash
# Compare responses
./scripts/compare_endpoints.sh

# Load testing
ab -n 1000 -c 10 http://api.yourdomain.com/api/v1/tlog/trig-count/1
```

### 6.2 User Acceptance Testing

1. **Create test scenarios** covering all migrated functionality
2. **Test with real user data** (use staging environment)
3. **Performance testing** to ensure new system meets requirements
4. **Security testing** for authentication and authorization

## Phase 7: Production Cutover

### 7.1 Gradual Traffic Migration

Use load balancer or proxy to gradually shift traffic:

```nginx
# Nginx example - gradually increase traffic to new API
upstream legacy_backend {
    server old-php-server:80 weight=70;
}

upstream new_backend {
    server new-fastapi-server:8000 weight=30;
}
```

### 7.2 Monitoring and Rollback Plan

1. **Set up comprehensive monitoring**
2. **Define rollback triggers** (error rates, response times)
3. **Prepare rollback procedures**
4. **Monitor for 24-48 hours** after each migration step

## Phase 8: Cleanup and Optimization

### 8.1 Remove Legacy Code

Only after successful migration and monitoring period:

```bash
# Archive old PHP files
mkdir legacy_backup
mv old_php_files/* legacy_backup/
```

### 8.2 Optimize New System

1. **Database query optimization**
2. **Caching implementation**
3. **Performance tuning**
4. **Security hardening**

## Common Migration Challenges

### Challenge 1: Different Data Types

**Problem:** PHP might return strings where FastAPI expects integers
**Solution:** Use Pydantic validators

```python
class ResponseModel(BaseModel):
    count: int
    
    @validator('count', pre=True)
    def parse_count(cls, v):
        return int(v) if isinstance(v, str) else v
```

### Challenge 2: Session vs JWT

**Problem:** PHP sessions don't translate to JWT
**Solution:** Implement dual authentication during transition

```python
def get_current_user_dual(
    request: Request,
    db: Session = Depends(get_db)
):
    # Try JWT first
    try:
        return get_current_user_jwt(request, db)
    except HTTPException:
        # Fall back to PHP session validation
        return validate_php_session(request, db)
```

### Challenge 3: Different Error Handling

**Problem:** PHP and FastAPI have different error formats
**Solution:** Create compatibility layer

```python
def legacy_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "code": exc.status_code
        }
    )
```

## Rollback Procedures

If issues arise during migration:

1. **Immediate rollback** - switch traffic back to PHP
2. **Investigate issues** in staging environment
3. **Fix problems** and re-test
4. **Gradual re-migration** once issues resolved

## Success Metrics

Track these metrics throughout migration:

- **Response times** (should improve)
- **Error rates** (should decrease)
- **Security incidents** (should decrease)
- **Developer productivity** (should improve)
- **System reliability** (should improve)

## Final Checklist

Before declaring migration complete:

- [ ] All PHP endpoints migrated to FastAPI
- [ ] All tests passing
- [ ] Performance meets or exceeds original system
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on new system
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery tested
- [ ] Legacy system safely archived

Remember: **Take your time** with this migration. It's better to migrate gradually and safely than to rush and cause downtime or data issues.
