"""
Tests for admin dependency functions.
"""

import pytest

from app.api.deps import get_current_admin_user
from app.models.user import User
from fastapi import HTTPException


def test_get_current_admin_user_with_admin_user(test_admin_user):
    """Test get_current_admin_user with admin user."""
    # This should not raise an exception
    result = get_current_admin_user(test_admin_user)
    assert result == test_admin_user


def test_get_current_admin_user_with_non_admin_user(test_user):
    """Test get_current_admin_user with non-admin user raises 403."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(test_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin privileges required"


def test_get_current_admin_user_with_admin_ind_n():
    """Test get_current_admin_user with user having admin_ind='N'."""
    non_admin_user = User(
        id=9999,
        name="nonadmin",
        firstname="Non",
        surname="Admin",
        email="nonadmin@example.com",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(non_admin_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin privileges required"


def test_get_current_admin_user_with_admin_ind_empty():
    """Test get_current_admin_user with user having empty admin_ind."""
    empty_admin_user = User(
        id=9998,
        name="emptyadmin",
        firstname="Empty",
        surname="Admin",
        email="emptyadmin@example.com",
        admin_ind="",
        email_valid="Y",
        public_ind="Y",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(empty_admin_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin privileges required"


def test_get_current_admin_user_with_admin_ind_none():
    """Test get_current_admin_user with user having None admin_ind."""
    none_admin_user = User(
        id=9997,
        name="noneadmin",
        firstname="None",
        surname="Admin",
        email="noneadmin@example.com",
        admin_ind=None,
        email_valid="Y",
        public_ind="Y",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_admin_user(none_admin_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Admin privileges required"
