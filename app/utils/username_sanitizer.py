"""
Username sanitization utilities for Auth0 compatibility.

Auth0 usernames can only contain alphanumeric characters and the following special characters:
'_', '+', '-', '.', '!', '#', '$', ''', '^', '`', '~' and '@'
"""

import re
import unicodedata
from typing import Dict, List


def sanitize_username_for_auth0(username: str) -> str:
    """
    Sanitize a username to be compatible with Auth0 username requirements.

    Auth0 usernames can only contain:
    - Alphanumeric characters (a-z, A-Z, 0-9)
    - Special characters: '_', '+', '-', '.', '!', '#', '$', ''', '^', '`', '~', '@'

    Args:
        username: The original username to sanitize

    Returns:
        Sanitized username compatible with Auth0

    Examples:
        >>> sanitize_username_for_auth0("user@example.com")
        "user@example.com"
        >>> sanitize_username_for_auth0("user name")
        "user_name"
        >>> sanitize_username_for_auth0("user/name")
        "user_name"
        >>> sanitize_username_for_auth0("user%name")
        "user_name"
        >>> sanitize_username_for_auth0("user(name)")
        "user_name"
        >>> sanitize_username_for_auth0("user[name]")
        "user_name"
        >>> sanitize_username_for_auth0("user{name}")
        "user_name"
        >>> sanitize_username_for_auth0("user|name")
        "user_name"
        >>> sanitize_username_for_auth0("user\\name")
        "user_name"
        >>> sanitize_username_for_auth0("user:name")
        "user_name"
        >>> sanitize_username_for_auth0("user;name")
        "user_name"
        >>> sanitize_username_for_auth0("user<name>")
        "user_name"
        >>> sanitize_username_for_auth0("user=name")
        "user_name"
        >>> sanitize_username_for_auth0("user?name")
        "user_name"
        >>> sanitize_username_for_auth0("user!name")
        "user!name"
        >>> sanitize_username_for_auth0("user#name")
        "user#name"
        >>> sanitize_username_for_auth0("user$name")
        "user$name"
        >>> sanitize_username_for_auth0("user'name")
        "user'name"
        >>> sanitize_username_for_auth0("user^name")
        "user^name"
        >>> sanitize_username_for_auth0("user`name")
        "user`name"
        >>> sanitize_username_for_auth0("user~name")
        "user~name"
        >>> sanitize_username_for_auth0("user+name")
        "user+name"
        >>> sanitize_username_for_auth0("user-name")
        "user-name"
        >>> sanitize_username_for_auth0("user.name")
        "user.name"
        >>> sanitize_username_for_auth0("user_name")
        "user_name"
    """
    if not username:
        return ""

    # Normalize unicode characters (e.g., é -> e, ï -> i)
    normalized = unicodedata.normalize("NFKD", username)

    # Replace any character that's not in the allowed set with underscore
    # Allowed: a-z, A-Z, 0-9, _, +, -, ., !, #, $, ', ^, `, ~, @
    sanitized = re.sub(r"[^a-zA-Z0-9_\+\.\!\#\$\'\^\`\~@-]", "_", normalized)

    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip("_")

    # Ensure the username is not empty after sanitization
    if not sanitized:
        return "user"

    # Auth0 has a maximum length limit (typically 128 characters)
    # Truncate if necessary but preserve the last character if it's not an underscore
    if len(sanitized) > 128:
        sanitized = sanitized[:128]
        if sanitized.endswith("_"):
            sanitized = sanitized.rstrip("_")

    return sanitized


def find_duplicate_sanitized_usernames(usernames: List[str]) -> Dict[str, List[str]]:
    """
    Find duplicate sanitized usernames from a list of original usernames.

    Args:
        usernames: List of original usernames to check

    Returns:
        Dictionary mapping sanitized usernames to lists of original usernames that map to them

    Example:
        >>> usernames = ["user name", "user-name", "user_name", "user@example.com", "user@test.com"]
        >>> find_duplicate_sanitized_usernames(usernames)
        {
            "user_name": ["user name", "user-name", "user_name"],
            "user@example.com": ["user@example.com"],
            "user@test.com": ["user@test.com"]
        }
    """
    sanitized_to_original: Dict[str, List[str]] = {}

    for username in usernames:
        sanitized = sanitize_username_for_auth0(username)
        if sanitized not in sanitized_to_original:
            sanitized_to_original[sanitized] = []
        sanitized_to_original[sanitized].append(username)

    # Return only entries with duplicates
    return {k: v for k, v in sanitized_to_original.items() if len(v) > 1}


def get_username_mapping(usernames: List[str]) -> Dict[str, str]:
    """
    Get a mapping of original usernames to their sanitized versions.

    Args:
        usernames: List of original usernames

    Returns:
        Dictionary mapping original usernames to sanitized usernames
    """
    return {username: sanitize_username_for_auth0(username) for username in usernames}
