# Passkeys (WebAuthn) Configuration

## Overview

Passkeys (also known as WebAuthn or FIDO2) have been enabled for all database connections, providing users with a secure, passwordless authentication option.

## What Are Passkeys?

Passkeys are a modern authentication method that replaces passwords with cryptographic keys stored on the user's device (phone, tablet, computer) or security key. They provide:

- **Enhanced Security**: Resistant to phishing, credential stuffing, and password breaches
- **Better UX**: No passwords to remember, faster login with biometrics or PIN
- **Cross-Platform**: Sync across devices via iCloud Keychain, Google Password Manager, or hardware keys

## Configuration

### Terraform Configuration

Passkeys are configured in `terraform/modules/auth0/main.tf`:

#### 1. Database Connection with Passkey Authentication

```hcl
resource "auth0_connection" "database" {
  options {
    authentication_methods {
      password {
        enabled = true  # Keep password as fallback
      }
      passkey {
        enabled = true  # Enable passkey authentication
      }
    }
  }
}
```

#### 2. Identifier First Prompt (Required for Passkeys)

```hcl
resource "auth0_prompt" "identifier_first" {
  identifier_first               = true  # Enable identifier-first flow
  webauthn_platform_first_factor = true  # Allow passkey as first factor
}
```

### Configuration Options

- **`authentication_methods.passkey.enabled = true`**: Enables passkey authentication method
- **`authentication_methods.password.enabled = true`**: Keeps password as fallback (required by Auth0)
- **`identifier_first = true`**: Enables identifier-first authentication flow (required for passkeys)
- **`webauthn_platform_first_factor = true`**: Allows passkeys to be used as the first authentication factor

## User Experience

### First-Time Login
1. User logs in with email + password (existing flow)
2. After successful login, Auth0 prompts: "Create a passkey for faster sign-ins?"
3. User can:
   - **Create passkey**: Save passkey to device/browser
   - **Skip**: Continue without passkey (can create later)

### Subsequent Logins (with Passkey)
1. User navigates to login page
2. Browser autofill suggests passkey, OR user clicks "Continue with a passkey"
3. User authenticates with biometric (Touch ID, Face ID) or device PIN
4. Instant login - no password needed

### Fallback
- **Password still required**: Auth0 requires passwords as a fallback for:
  - Devices that don't support passkeys
  - Lost/broken devices
  - User preference

## Prerequisites (Already Met)

✅ **Custom Domain**: Configured (`auth.trigpointing.me`, `auth.trigpointing.uk`)
- Passkeys are tied to the domain they're created on
- Custom domain must be configured BEFORE enabling passkeys

✅ **New Universal Login**: Enabled (default for modern tenants)

✅ **Identifier First Flow**: Configured via `auth0_prompt` resource
- Required for passkeys to function properly

✅ **Requires Username**: Disabled
- Already configured in `auth0_connection.database.options.requires_username = false`

## Browser/Device Support

### Supported Platforms
- **macOS/iOS**: Safari, Chrome, Firefox (via iCloud Keychain)
- **Windows**: Chrome, Edge, Firefox (via Windows Hello)
- **Android**: Chrome, Firefox (via Google Password Manager)
- **Linux**: Chrome, Firefox (via hardware keys or compatible password managers)

### Hardware Keys
- YubiKey
- Titan Security Key
- Any FIDO2-compliant hardware key

## Security Considerations

### Benefits
1. **Phishing-Resistant**: Passkeys are domain-bound, can't be used on fake sites
2. **No Shared Secrets**: Private key never leaves the device
3. **Replay Attack Protection**: Each authentication creates unique signature
4. **No Credential Stuffing**: No password databases to leak

### Password Requirement
- Auth0 currently requires passwords as a backup method
- Users must still set a password during registration
- Passkeys are an *additional* authentication method, not a replacement (yet)

## Management

### For Users
Users can manage their passkeys via:
- Device settings (Keychain on macOS/iOS, Password Manager on Android/Chrome)
- Auth0 account profile (if self-service is enabled)

### For Administrators
- View passkey enrollment statistics in Auth0 Dashboard
- Users with passkeys show `authentication_methods` in their profile
- Can remove passkeys via Auth0 Management API if needed

## Deployment

### Applying Changes

```bash
# Staging
cd terraform/staging
terraform plan
terraform apply

# Production (after testing)
cd terraform/production
terraform plan
terraform apply
```

### Verification

1. Log in with email + password
2. Check for passkey enrollment prompt after login
3. Create a passkey
4. Log out and log back in using the passkey

## Troubleshooting

### Passkey Not Offered
- **Check browser support**: Visit https://webauthn.me to test
- **Verify custom domain**: Passkeys must be on custom domain (not `*.auth0.com`)
- **Check enrollment prompt**: May only appear once after password login

### Passkey Not Working
- **Domain change**: Passkeys are invalidated if domain changes
- **Browser/device issue**: Try different browser or clear browser data
- **Fallback to password**: Users can always use password if passkey fails

### Can't Find Passkey
- **Check device settings**:
  - macOS/iOS: System Settings → Passwords
  - Android: Settings → Google → Autofill → Password Manager
  - Windows: Settings → Accounts → Sign-in options → Passkeys

## References

- [Auth0 Passkeys Documentation](https://auth0.com/docs/authenticate/database-connections/passkeys)
- [WebAuthn Guide](https://webauthn.guide/)
- [FIDO Alliance](https://fidoalliance.org/)
- [Passkeys.dev](https://passkeys.dev/)

## Future Enhancements

Potential improvements (not yet implemented):
- **Passwordless-only accounts**: Allow users to skip password entirely (requires Auth0 support)
- **Passkey management API**: Allow users to view/delete passkeys via API
- **Passkey-only login option**: Hide password field for users with passkeys
- **Recovery codes**: Provide backup codes in case of passkey loss

