"""
Tests for username sanitization functionality.
"""

from api.utils.username_sanitizer import (
    find_duplicate_sanitized_usernames,
    get_username_mapping,
    sanitize_username_for_auth0,
)


class TestUsernameSanitizer:
    """Test cases for username sanitization."""

    def test_basic_alphanumeric_username(self):
        """Test that basic alphanumeric usernames are unchanged."""
        assert sanitize_username_for_auth0("user123") == "user123"
        assert sanitize_username_for_auth0("User123") == "User123"
        assert sanitize_username_for_auth0("USER123") == "USER123"

    def test_allowed_special_characters(self):
        """Test that allowed special characters are preserved."""
        assert sanitize_username_for_auth0("user_name") == "user_name"
        assert sanitize_username_for_auth0("user+name") == "user+name"
        assert sanitize_username_for_auth0("user-name") == "user-name"
        assert sanitize_username_for_auth0("user.name") == "user.name"
        assert sanitize_username_for_auth0("user!name") == "user!name"
        assert sanitize_username_for_auth0("user#name") == "user#name"
        assert sanitize_username_for_auth0("user$name") == "user$name"
        assert sanitize_username_for_auth0("user'name") == "user'name"
        assert sanitize_username_for_auth0("user^name") == "user^name"
        assert sanitize_username_for_auth0("user`name") == "user`name"
        assert sanitize_username_for_auth0("user~name") == "user~name"
        assert sanitize_username_for_auth0("user@example.com") == "user@example.com"

    def test_disallowed_characters_replaced_with_underscore(self):
        """Test that disallowed characters are replaced with underscores."""
        assert sanitize_username_for_auth0("user name") == "user_name"
        assert sanitize_username_for_auth0("user/name") == "user_name"
        assert sanitize_username_for_auth0("user%name") == "user_name"
        assert sanitize_username_for_auth0("user(name)") == "user_name"
        assert sanitize_username_for_auth0("user[name]") == "user_name"
        assert sanitize_username_for_auth0("user{name}") == "user_name"
        assert sanitize_username_for_auth0("user|name") == "user_name"
        assert sanitize_username_for_auth0("user\\name") == "user_name"
        assert sanitize_username_for_auth0("user:name") == "user_name"
        assert sanitize_username_for_auth0("user;name") == "user_name"
        assert sanitize_username_for_auth0("user<name>") == "user_name"
        assert sanitize_username_for_auth0("user=name") == "user_name"
        assert sanitize_username_for_auth0("user?name") == "user_name"

    def test_multiple_disallowed_characters(self):
        """Test multiple consecutive disallowed characters."""
        assert sanitize_username_for_auth0("user  name") == "user_name"
        assert sanitize_username_for_auth0("user//name") == "user_name"
        assert sanitize_username_for_auth0("user%%name") == "user_name"
        assert sanitize_username_for_auth0("user((name))") == "user_name"
        assert sanitize_username_for_auth0("user[[name]]") == "user_name"

    def test_leading_trailing_underscores_removed(self):
        """Test that leading and trailing underscores are removed."""
        assert sanitize_username_for_auth0("_username") == "username"
        assert sanitize_username_for_auth0("username_") == "username"
        assert sanitize_username_for_auth0("_username_") == "username"
        assert sanitize_username_for_auth0("__username__") == "username"

    def test_empty_username_handling(self):
        """Test handling of empty or None usernames."""
        assert sanitize_username_for_auth0("") == ""
        assert sanitize_username_for_auth0(None) == ""

    def test_username_after_sanitization_empty(self):
        """Test that empty usernames after sanitization return 'user'."""
        assert sanitize_username_for_auth0("!!!") == "!!!"
        assert sanitize_username_for_auth0("///") == "user"
        assert sanitize_username_for_auth0("   ") == "user"

    def test_unicode_normalization(self):
        """Test that unicode characters are normalized."""
        assert sanitize_username_for_auth0("café") == "cafe"
        assert sanitize_username_for_auth0("naïve") == "nai_ve"
        assert sanitize_username_for_auth0("résumé") == "re_sume"

    def test_length_limit(self):
        """Test that usernames are truncated to 128 characters."""
        long_username = "a" * 200
        result = sanitize_username_for_auth0(long_username)
        assert len(result) <= 128
        assert result == "a" * 128

    def test_length_limit_preserves_last_character(self):
        """Test that truncation preserves the last character if it's not an underscore."""
        long_username = "a" * 127 + "b"
        result = sanitize_username_for_auth0(long_username)
        assert len(result) == 128
        assert result.endswith("b")

    def test_length_limit_removes_trailing_underscores(self):
        """Test that truncation removes trailing underscores."""
        long_username = "a" * 127 + "_"
        result = sanitize_username_for_auth0(long_username)
        assert len(result) == 127
        assert not result.endswith("_")

    def test_complex_real_world_examples(self):
        """Test complex real-world username examples."""
        assert (
            sanitize_username_for_auth0("john.doe@example.com")
            == "john.doe@example.com"
        )
        assert sanitize_username_for_auth0("user-name_123") == "user-name_123"
        assert (
            sanitize_username_for_auth0("user name with spaces")
            == "user_name_with_spaces"
        )
        assert sanitize_username_for_auth0("user/with/slashes") == "user_with_slashes"
        assert (
            sanitize_username_for_auth0("user(with)parentheses")
            == "user_with_parentheses"
        )
        assert sanitize_username_for_auth0("user[with]brackets") == "user_with_brackets"
        assert sanitize_username_for_auth0("user{with}braces") == "user_with_braces"
        assert sanitize_username_for_auth0("user|with|pipes") == "user_with_pipes"
        assert (
            sanitize_username_for_auth0("user\\with\\backslashes")
            == "user_with_backslashes"
        )
        assert sanitize_username_for_auth0("user:with:colons") == "user_with_colons"
        assert (
            sanitize_username_for_auth0("user;with;semicolons")
            == "user_with_semicolons"
        )
        assert sanitize_username_for_auth0("user<with>angles") == "user_with_angles"
        assert sanitize_username_for_auth0("user=with=equals") == "user_with_equals"
        assert (
            sanitize_username_for_auth0("user?with?questions") == "user_with_questions"
        )
        assert sanitize_username_for_auth0("user%with%percent") == "user_with_percent"
        assert (
            sanitize_username_for_auth0("user&with&ampersand") == "user_with_ampersand"
        )
        assert sanitize_username_for_auth0("user*with*asterisk") == "user_with_asterisk"
        assert (
            sanitize_username_for_auth0("user+with+plus") == "user+with+plus"
        )  # Plus is allowed
        assert (
            sanitize_username_for_auth0("user!with!exclamation")
            == "user!with!exclamation"
        )  # Exclamation is allowed
        assert (
            sanitize_username_for_auth0("user#with#hash") == "user#with#hash"
        )  # Hash is allowed
        assert (
            sanitize_username_for_auth0("user$with$dollar") == "user$with$dollar"
        )  # Dollar is allowed
        assert (
            sanitize_username_for_auth0("user'with'apostrophe")
            == "user'with'apostrophe"
        )  # Apostrophe is allowed
        assert (
            sanitize_username_for_auth0("user^with^caret") == "user^with^caret"
        )  # Caret is allowed
        assert (
            sanitize_username_for_auth0("user`with`backtick") == "user`with`backtick"
        )  # Backtick is allowed
        assert (
            sanitize_username_for_auth0("user~with~tilde") == "user~with~tilde"
        )  # Tilde is allowed
        assert (
            sanitize_username_for_auth0("user@with@at") == "user@with@at"
        )  # At is allowed


class TestDuplicateFinder:
    """Test cases for duplicate username finding."""

    def test_no_duplicates(self):
        """Test with no duplicate usernames."""
        usernames = ["user1", "user2", "user3"]
        result = find_duplicate_sanitized_usernames(usernames)
        assert result == {}

    def test_simple_duplicates(self):
        """Test with simple duplicate usernames."""
        usernames = ["user name", "user-name", "user_name"]
        result = find_duplicate_sanitized_usernames(usernames)
        expected = {"user_name": ["user name", "user_name"]}
        assert result == expected

    def test_mixed_duplicates_and_unique(self):
        """Test with mixed duplicates and unique usernames."""
        usernames = [
            "user name",
            "user-name",
            "user_name",
            "unique_user",
            "another unique",
        ]
        result = find_duplicate_sanitized_usernames(usernames)
        expected = {"user_name": ["user name", "user_name"]}
        assert result == expected

    def test_multiple_groups_of_duplicates(self):
        """Test with multiple groups of duplicate usernames."""
        usernames = [
            "user name",
            "user-name",
            "user_name",
            "admin user",
            "admin-user",
            "admin_user",
            "unique_user",
        ]
        result = find_duplicate_sanitized_usernames(usernames)
        expected = {
            "user_name": ["user name", "user_name"],
            "admin_user": ["admin user", "admin_user"],
        }
        assert result == expected

    def test_email_duplicates(self):
        """Test with email address duplicates."""
        usernames = ["user@example.com", "user@test.com"]
        result = find_duplicate_sanitized_usernames(usernames)
        expected = {}
        assert result == expected

    def test_empty_list(self):
        """Test with empty username list."""
        result = find_duplicate_sanitized_usernames([])
        assert result == {}

    def test_single_username(self):
        """Test with single username."""
        result = find_duplicate_sanitized_usernames(["single_user"])
        assert result == {}


class TestUsernameMapping:
    """Test cases for username mapping functionality."""

    def test_basic_mapping(self):
        """Test basic username mapping."""
        usernames = ["user name", "user-name", "user@example.com"]
        result = get_username_mapping(usernames)
        expected = {
            "user name": "user_name",
            "user-name": "user-name",
            "user@example.com": "user@example.com",
        }
        assert result == expected

    def test_empty_mapping(self):
        """Test mapping with empty list."""
        result = get_username_mapping([])
        assert result == {}

    def test_single_username_mapping(self):
        """Test mapping with single username."""
        result = get_username_mapping(["single_user"])
        assert result == {"single_user": "single_user"}


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_username(self):
        """Test with very long username."""
        long_username = "a" * 300
        result = sanitize_username_for_auth0(long_username)
        assert len(result) <= 128
        assert result == "a" * 128

    def test_username_with_only_special_chars(self):
        """Test username with only special characters."""
        assert sanitize_username_for_auth0("!@#$%^&*()") == "!@#$_^"
        assert sanitize_username_for_auth0("!@#$%^&*()_+") == "!@#$_^_+"

    def test_username_with_only_disallowed_chars(self):
        """Test username with only disallowed characters."""
        assert sanitize_username_for_auth0("()[]{}") == "user"
        assert sanitize_username_for_auth0("///") == "user"

    def test_username_with_mixed_unicode(self):
        """Test username with mixed unicode characters."""
        assert sanitize_username_for_auth0("café_123") == "cafe_123"
        assert sanitize_username_for_auth0("naïve_user") == "nai_ve_user"

    def test_username_with_numbers_only(self):
        """Test username with only numbers."""
        assert sanitize_username_for_auth0("123456") == "123456"
        assert sanitize_username_for_auth0("000000") == "000000"

    def test_username_with_underscores_only(self):
        """Test username with only underscores."""
        assert sanitize_username_for_auth0("___") == "user"
        assert sanitize_username_for_auth0("_") == "user"

    def test_username_with_spaces_only(self):
        """Test username with only spaces."""
        assert sanitize_username_for_auth0("   ") == "user"
        assert sanitize_username_for_auth0(" ") == "user"
