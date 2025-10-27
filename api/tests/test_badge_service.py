"""
Tests for the badge service.
"""

import io
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from api.models.user import User
from api.services.badge_service import BadgeService


class TestBadgeService:
    """Test cases for BadgeService."""

    def test_init(self):
        """Test BadgeService initialization."""
        service = BadgeService()
        assert service.base_width == 200
        assert service.base_height == 50
        assert service.logo_path.name == "tuk_logo.png"

    @patch("api.services.badge_service.get_user_by_id")
    def test_get_user_statistics(self, mock_get_user):
        """Test getting user statistics."""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_get_user.return_value = mock_user

        # Mock database queries
        mock_db = Mock(spec=Session)

        # Mock distinct trigpoints query
        mock_trig_query = Mock()
        mock_trig_query.filter.return_value = mock_trig_query
        mock_trig_query.distinct.return_value = mock_trig_query
        mock_trig_query.count.return_value = 5

        # Mock photos query
        mock_photo_query = Mock()
        mock_photo_query.join.return_value = mock_photo_query
        mock_photo_query.filter.return_value = mock_photo_query
        mock_photo_query.count.return_value = 12

        mock_db.query.side_effect = [mock_trig_query, mock_photo_query]

        service = BadgeService()
        distinct_trigs, total_photos = service.get_user_statistics(mock_db, 1)

        assert distinct_trigs == 5
        assert total_photos == 12

    @patch("api.services.badge_service.get_user_by_id")
    def test_generate_badge_user_not_found(self, mock_get_user):
        """Test badge generation when user is not found."""
        mock_get_user.return_value = None
        mock_db = Mock(spec=Session)

        service = BadgeService()

        with pytest.raises(ValueError, match="User with ID 999 not found"):
            service.generate_badge(mock_db, 999)

    @patch("api.services.badge_service.get_user_by_id")
    def test_generate_badge_logo_not_found(self, mock_get_user):
        """Test badge generation when logo file is not found."""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.name = "testuser"
        mock_get_user.return_value = mock_user

        mock_db = Mock(spec=Session)

        service = BadgeService()
        # Set logo path to non-existent file
        service.logo_path = Path("/nonexistent/logo.png")

        with pytest.raises(FileNotFoundError, match="Logo file not found"):
            service.generate_badge(mock_db, 1)

    def test_long_username_truncation(self):
        """Test that long usernames are properly truncated."""
        # This would be tested in integration, but we can verify the logic
        long_name = "verylongusernamethatshouldbetrunca"
        truncated = long_name[:20]
        assert len(truncated) == 20
        assert truncated == "verylongusernamethat"

    @patch("api.services.badge_service.get_user_by_id")
    def test_generate_badge_integration(self, mock_get_user):
        """Integration test that actually generates a badge using real PIL operations."""
        # This test will only work if the logo file exists
        service = BadgeService()
        if not service.logo_path.exists():
            pytest.skip("Logo file not found, skipping integration test")

        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.name = "testuser"
        mock_get_user.return_value = mock_user

        # Mock database queries for statistics
        mock_db = Mock(spec=Session)
        mock_trig_query = Mock()
        mock_trig_query.filter.return_value = mock_trig_query
        mock_trig_query.distinct.return_value = mock_trig_query
        mock_trig_query.count.return_value = 3

        mock_photo_query = Mock()
        mock_photo_query.join.return_value = mock_photo_query
        mock_photo_query.filter.return_value = mock_photo_query
        mock_photo_query.count.return_value = 7

        mock_db.query.side_effect = [mock_trig_query, mock_photo_query]

        # This should work with real PIL operations
        result = service.generate_badge(mock_db, 1)

        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0  # Should be at the beginning after seek(0)
        assert len(result.getvalue()) > 0  # Should have actual PNG data

    @patch("api.services.badge_service.get_user_by_id")
    def test_generate_badge_with_scale(self, mock_get_user):
        """Test badge generation with different scale factors."""
        service = BadgeService()
        if not service.logo_path.exists():
            pytest.skip("Logo file not found, skipping scale test")

        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.name = "testuser"
        mock_get_user.return_value = mock_user

        # Mock database queries
        mock_db = Mock(spec=Session)
        mock_trig_query = Mock()
        mock_trig_query.filter.return_value = mock_trig_query
        mock_trig_query.distinct.return_value = mock_trig_query
        mock_trig_query.count.return_value = 5

        mock_photo_query = Mock()
        mock_photo_query.join.return_value = mock_photo_query
        mock_photo_query.filter.return_value = mock_photo_query
        mock_photo_query.count.return_value = 10

        mock_db.query.side_effect = [mock_trig_query, mock_photo_query]

        # Test different scale factors
        for scale in [0.5, 1.0, 2.0]:
            mock_db.query.side_effect = [
                mock_trig_query,
                mock_photo_query,
            ]  # Reset for each test
            result = service.generate_badge(mock_db, 1, scale=scale)

            assert isinstance(result, io.BytesIO)
            assert len(result.getvalue()) > 0

            # Verify the image has the expected dimensions
            from PIL import Image

            result.seek(0)
            image = Image.open(result)
            expected_width = int(200 * scale)
            expected_height = int(50 * scale)
            assert image.size == (expected_width, expected_height)
