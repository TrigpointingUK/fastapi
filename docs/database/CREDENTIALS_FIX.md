# Database Credentials Fix

## Issue
The database credentials secrets contained the port number in the host field, causing application errors:

```
ValueError: invalid literal for int() with base 10: '3306:3306'
```

## Root Cause
The AWS Secrets Manager secrets had the following format:
```json
{
  "host": "fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com:3306",
  "port": 3306
}
```

The application was trying to parse the host field (including the port) as an integer for the `DB_PORT` field.

## Solution
Updated both credentials secrets to remove the port number from the host field:

### Before:
```json
{
  "host": "fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com:3306",
  "port": 3306
}
```

### After:
```json
{
  "host": "fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com",
  "port": 3306
}
```

## Commands Used
```bash
# Update staging credentials
aws secretsmanager update-secret \
  --secret-id fastapi-staging-credentials \
  --region eu-west-2 \
  --secret-string '{"dbInstanceIdentifier":"fastapi-db","dbname":"tuk_staging","engine":"mysql","host":"fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com","password":"dhKE[&P.wSbjWFm%l=.*R4b#-a8q])F:","port":3306,"username":"fastapi_staging"}'

# Update production credentials
aws secretsmanager update-secret \
  --secret-id fastapi-production-credentials \
  --region eu-west-2 \
  --secret-string '{"dbInstanceIdentifier":"fastapi-db","dbname":"tuk_production","engine":"mysql","host":"fastapi-db.cvsoze6aw56h.eu-west-2.rds.amazonaws.com","password":"r7N+Y8Gk8cMsOeApt*Aux,2|x=Rc?9or","port":3306,"username":"fastapi_production"}'
```

## Verification
Both secrets now have the correct format with separate host and port fields:
- `fastapi-staging-credentials` ✅
- `fastapi-production-credentials` ✅

## Notes
- Ansible scripts already handle this correctly using `cut -d: -f1` to strip port from host
- Application now correctly parses `DB_HOST` and `DB_PORT` as separate fields
- This fix resolves the database connection errors in both staging and production
