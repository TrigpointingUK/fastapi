"""
Tests for CRUD user utility functions to improve coverage.
"""

from app.crud.user import is_admin, is_cacher, is_trigger
from app.models.user import User


class TestCRUDUserUtilities:
    """Test utility functions in CRUD user module."""

    def test_is_cacher_y(self):
        """Test is_cacher with 'Y' value."""
        user = User()
        user.cacher_ind = "Y"
        assert is_cacher(user) is True

    def test_is_cacher_n(self):
        """Test is_cacher with 'N' value."""
        user = User()
        user.cacher_ind = "N"
        assert is_cacher(user) is False

    def test_is_cacher_empty(self):
        """Test is_cacher with empty value."""
        user = User()
        user.cacher_ind = ""
        assert is_cacher(user) is False

    def test_is_cacher_none(self):
        """Test is_cacher with None value."""
        user = User()
        user.cacher_ind = None
        assert is_cacher(user) is False

    def test_is_trigger_y(self):
        """Test is_trigger with 'Y' value."""
        user = User()
        user.trigger_ind = "Y"
        assert is_trigger(user) is True

    def test_is_trigger_n(self):
        """Test is_trigger with 'N' value."""
        user = User()
        user.trigger_ind = "N"
        assert is_trigger(user) is False

    def test_is_trigger_empty(self):
        """Test is_trigger with empty value."""
        user = User()
        user.trigger_ind = ""
        assert is_trigger(user) is False

    def test_is_trigger_none(self):
        """Test is_trigger with None value."""
        user = User()
        user.trigger_ind = None
        assert is_trigger(user) is False

    def test_is_admin_y(self):
        """Test is_admin with 'Y' value."""
        user = User()
        user.admin_ind = "Y"
        assert is_admin(user) is True

    def test_is_admin_n(self):
        """Test is_admin with 'N' value."""
        user = User()
        user.admin_ind = "N"
        assert is_admin(user) is False

    def test_is_admin_empty(self):
        """Test is_admin with empty value."""
        user = User()
        user.admin_ind = ""
        assert is_admin(user) is False

    def test_is_admin_none(self):
        """Test is_admin with None value."""
        user = User()
        user.admin_ind = None
        assert is_admin(user) is False

    def test_is_cacher_case_sensitive(self):
        """Test is_cacher is case sensitive."""
        user = User()
        user.cacher_ind = "y"  # lowercase
        assert is_cacher(user) is False

    def test_is_trigger_case_sensitive(self):
        """Test is_trigger is case sensitive."""
        user = User()
        user.trigger_ind = "t"  # lowercase
        assert is_trigger(user) is False

    def test_is_admin_case_sensitive(self):
        """Test is_admin is case sensitive."""
        user = User()
        user.admin_ind = "a"  # lowercase
        assert is_admin(user) is False
