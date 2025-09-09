#!/usr/bin/env python3
"""
Debug script for Auth0 token validation.

This script helps debug Auth0 token issues by providing detailed information
about token validation without requiring the full FastAPI application.

Usage:
    python debug_auth0_token.py "your_auth0_token_here"
"""

import json
import sys
from datetime import datetime, timezone

# Add the app directory to the path so we can import modules
sys.path.insert(0, "/home/ianh/dev/fastapi")

from jose import jwt  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import auth0_validator, validate_any_token  # noqa: E402


def debug_auth0_token(token: str):
    """Debug an Auth0 token and print detailed information."""

    print("=" * 80)
    print("AUTH0 TOKEN DEBUG INFORMATION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}Z")
    print(f"Token length: {len(token)}")
    print()

    # Configuration info
    print("CONFIGURATION:")
    print(f"  Auth0 enabled: {settings.AUTH0_ENABLED}")
    print(f"  Auth0 domain: {settings.AUTH0_DOMAIN}")
    print(f"  Auth0 connection: {settings.AUTH0_CONNECTION}")
    print()

    # Token header
    print("TOKEN HEADER:")
    try:
        header = jwt.get_unverified_header(token)
        print(f"  Algorithm: {header.get('alg', 'N/A')}")
        print(f"  Key ID: {header.get('kid', 'N/A')}")
        print(f"  Type: {header.get('typ', 'N/A')}")
        print(f"  Full header: {json.dumps(header, indent=2)}")
    except Exception as e:
        print(f"  Error decoding header: {e}")
    print()

    # JWKS information
    print("JWKS INFORMATION:")
    try:
        jwks = auth0_validator._get_jwks()
        if jwks:
            print("  JWKS available: Yes")
            print(f"  Number of keys: {len(jwks.get('keys', []))}")
            print(
                f"  Available key IDs: {[key.get('kid') for key in jwks.get('keys', [])]}"
            )
        else:
            print("  JWKS available: No")
    except Exception as e:
        print(f"  Error getting JWKS: {e}")
    print()

    # Audience information
    print("AUDIENCE INFORMATION:")
    try:
        audience = auth0_validator._get_auth0_audience()
        print(f"  Audience: {audience}")
    except Exception as e:
        print(f"  Error getting audience: {e}")
    print()

    # Token validation
    print("TOKEN VALIDATION:")
    try:
        payload = validate_any_token(token)
        if payload:
            print("  Validation: SUCCESS")
            print(f"  Token type: {payload.get('token_type', 'N/A')}")
            print(f"  Subject: {payload.get('sub', 'N/A')}")
            print(f"  Audience: {payload.get('aud', 'N/A')}")
            print(f"  Issuer: {payload.get('iss', 'N/A')}")
            print(f"  Expires: {payload.get('exp', 'N/A')}")
            print(f"  Issued at: {payload.get('iat', 'N/A')}")
            print(f"  Auth0 user ID: {payload.get('auth0_user_id', 'N/A')}")
            print(
                f"  Full payload: {json.dumps({k: v for k, v in payload.items() if k not in ['iat', 'exp', 'nbf']}, indent=2)}"
            )
        else:
            print("  Validation: FAILED")
    except Exception as e:
        print(f"  Error during validation: {e}")
    print()

    # Try to decode without validation
    print("UNVERIFIED TOKEN DECODE:")
    try:
        unverified_payload = jwt.get_unverified_claims(token)
        print(f"  Subject: {unverified_payload.get('sub', 'N/A')}")
        print(f"  Audience: {unverified_payload.get('aud', 'N/A')}")
        print(f"  Issuer: {unverified_payload.get('iss', 'N/A')}")
        print(f"  Expires: {unverified_payload.get('exp', 'N/A')}")
        print(f"  Issued at: {unverified_payload.get('iat', 'N/A')}")
        print(
            f"  Full payload: {json.dumps({k: v for k, v in unverified_payload.items() if k not in ['iat', 'exp', 'nbf']}, indent=2)}"
        )
    except Exception as e:
        print(f"  Error decoding unverified claims: {e}")
    print()

    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_auth0_token.py 'your_auth0_token_here'")
        sys.exit(1)

    token = sys.argv[1]
    debug_auth0_token(token)
