# Auth0 Audience Configuration Guide

This document explains how to configure Auth0 audiences for different environments and purposes.

## Overview

The application uses **two separate audiences** for different purposes:

1. **Management API Audience**: For accessing Auth0's Management API (user sync, profile updates, etc.)
2. **API Audience**: For validating tokens from your API clients

## Why Two Audiences?

- **Security**: Tokens can't be used interchangeably between different services
- **Clarity**: Clear separation of concerns between management operations and API access
- **Standards Compliance**: Follows OAuth2/JWT best practices

## Configuration

### Environment Variables

Add these to your environment configuration:

```bash
# Auth0 Basic Configuration
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_SECRET_NAME=your-auth0-secret-name
AUTH0_CONNECTION=Username-Password-Authentication

# Auth0 Audience Configuration
AUTH0_MANAGEMENT_API_AUDIENCE=https://your-domain.auth0.com/api/v2/
AUTH0_API_AUDIENCE=https://your-api-domain.com/api/v1/
```

### Environment-Specific Examples

#### Staging Environment
```bash
AUTH0_DOMAIN=trigpointing.eu.auth0.com
AUTH0_SECRET_NAME=trigpointing-auth0-staging
AUTH0_MANAGEMENT_API_AUDIENCE=https://trigpointing.eu.auth0.com/api/v2/
AUTH0_API_AUDIENCE=https://api.trigpointing.me/api/v1/
```

#### Production Environment
```bash
AUTH0_DOMAIN=trigpointing.eu.auth0.com
AUTH0_SECRET_NAME=trigpointing-auth0-production
AUTH0_MANAGEMENT_API_AUDIENCE=https://trigpointing.eu.auth0.com/api/v2/
AUTH0_API_AUDIENCE=https://api.trigpointing.uk/api/v1/
```

## Auth0 Dashboard Configuration

### 1. Management API Application
- **Purpose**: Server-to-server communication with Auth0
- **Audience**: `https://trigpointing.eu.auth0.com/api/v2/`
- **Grant Types**: Client Credentials
- **Scopes**: `read:users`, `create:users`, `update:users`, `delete:users`

### 2. API Application
- **Purpose**: Your API that clients will access
- **Audience**: `https://api.trigpointing.me/api/v1/` (staging) or `https://api.trigpointing.uk/api/v1/` (production)
- **Grant Types**: Authorization Code, Client Credentials
- **Scopes**: `api:admin`, `api:write`, `api:read-pii`

## How It Works

### Management API Audience
- Used by `Auth0Service` for user synchronization
- Stored in `AUTH0_MANAGEMENT_API_AUDIENCE` environment variable
- Used when obtaining access tokens for Management API calls

### API Audience
- Used by `Auth0TokenValidator` for token validation
- Stored in `AUTH0_API_AUDIENCE` environment variable
- Used when validating tokens from API clients

## Troubleshooting

### Common Issues

1. **Audience Mismatch**: Ensure the audience in your token matches `AUTH0_API_AUDIENCE`
2. **Management API Access**: Ensure `AUTH0_MANAGEMENT_API_AUDIENCE` is correctly configured
3. **Environment Variables**: Verify all required environment variables are set

### Debug Endpoints

Use the debug endpoint to troubleshoot token issues:
```bash
curl -X POST "https://your-api.com/api/v1/auth/auth0-debug" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "your-token-here"}'
```

### Debug Script

Use the debug script for local testing:
```bash
python debug_auth0_token.py "your-token-here"
```

## Security Considerations

- Never expose audience configuration in client-side code
- Use environment variables for all sensitive configuration
- Regularly rotate Auth0 credentials
- Monitor token usage and validation logs

## Migration Notes

This configuration replaces the previous single audience approach:
- **Before**: Single audience from AWS Secrets Manager
- **After**: Separate audiences from environment variables
- **Benefit**: Better security, clearer separation of concerns, environment-specific configuration
