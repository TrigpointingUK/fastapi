"""
Comprehensive tests for core security functions.
"""

from app.core.security import (
    extract_scopes,
    get_password_hash,
    verify_password,
)


class TestSecurityFunctions:
    """Test cases for core security functions."""

    def test_extract_scopes_valid_token(self):
        """Test extracting scopes from a valid JWT token."""
        token_payload = {
            "scope": "trig:read trig:write user:admin",
            "token_type": "auth0",
        }
        scopes = extract_scopes(token_payload)
        assert scopes == {"trig:read", "trig:write", "user:admin"}

    def test_extract_scopes_empty_scope(self):
        """Test extracting scopes from token with empty scope."""
        token_payload = {"scope": "", "token_type": "auth0"}
        scopes = extract_scopes(token_payload)
        assert scopes == set()

    def test_extract_scopes_no_scope_key(self):
        """Test extracting scopes from token without scope key."""
        token_payload = {"token_type": "auth0"}
        scopes = extract_scopes(token_payload)
        assert scopes == set()

    def test_extract_scopes_whitespace_scope(self):
        """Test extracting scopes with whitespace."""
        token_payload = {
            "scope": "  trig:read   trig:write  user:admin  ",
            "token_type": "auth0",
        }
        scopes = extract_scopes(token_payload)
        assert scopes == {"trig:read", "trig:write", "user:admin"}

    def test_verify_password_valid(self):
        """Test password verification with valid password."""
        plain_password = "testpassword123"
        hashed_password = get_password_hash(plain_password)
        assert verify_password(plain_password, hashed_password)
        assert not verify_password("wrongpassword", hashed_password)

    def test_verify_password_invalid(self):
        """Test password verification with invalid password."""
        plain_password = "testpassword123"
        hashed_password = get_password_hash(plain_password)
        assert not verify_password("wrongpassword", hashed_password)

    def test_get_password_hash(self):
        """Test password hashing function."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify the original password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_get_password_hash_consistency(self):
        """Test that password hashing is consistent."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        # But both should verify the original password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_verification_edge_cases(self):
        """Test password verification with edge cases."""
        # Empty password
        empty_hash = get_password_hash("")
        assert verify_password("", empty_hash)

        # Very long password
        long_password = "a" * 1000
        long_hash = get_password_hash(long_password)
        assert verify_password(long_password, long_hash)

        # Password with special characters
        special_password = "!@#$%^&*()_+{}[]|\\:;\"'<>?,./"
        special_hash = get_password_hash(special_password)
        assert verify_password(special_password, special_hash)
