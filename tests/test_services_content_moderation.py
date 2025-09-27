"""
Tests for content moderation service.
"""

from unittest.mock import Mock, patch

from app.services.content_moderation import ContentModerationService


class TestContentModerationService:
    """Test cases for content moderation service."""

    def test_init(self):
        """Test service initialization."""
        service = ContentModerationService()
        assert service is not None

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_success(self, mock_post):
        """Test successful text moderation."""
        service = ContentModerationService()

        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "flagged": False,
                "categories": {
                    "sexual": 0.1,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
                "category_scores": {
                    "sexual": 0.1,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = service.moderate_text("This is a test message")
        assert result is not None
        assert "flagged" in result
        assert "categories" in result
        assert "category_scores" in result

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_flagged(self, mock_post):
        """Test text moderation with flagged content."""
        service = ContentModerationService()

        # Mock response with flagged content
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "flagged": True,
                "categories": {
                    "sexual": 0.9,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
                "category_scores": {
                    "sexual": 0.9,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = service.moderate_text("This contains inappropriate content")
        assert result is not None
        assert result["flagged"] is True
        assert result["categories"]["sexual"] > 0.8

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_api_error(self, mock_post):
        """Test text moderation with API error."""
        service = ContentModerationService()

        # Mock API error
        mock_post.side_effect = Exception("API Error")

        result = service.moderate_text("Test message")
        assert result is None

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_http_error(self, mock_post):
        """Test text moderation with HTTP error."""
        service = ContentModerationService()

        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_post.return_value = mock_response

        result = service.moderate_text("Test message")
        assert result is None

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_empty_message(self, mock_post):
        """Test text moderation with empty message."""
        service = ContentModerationService()

        result = service.moderate_text("")
        assert result is None

    @patch("app.services.content_moderation.requests.post")
    def test_moderate_text_long_message(self, mock_post):
        """Test text moderation with very long message."""
        service = ContentModerationService()

        # Mock successful response for long message
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": {
                "flagged": False,
                "categories": {
                    "sexual": 0.0,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
                "category_scores": {
                    "sexual": 0.0,
                    "hate": 0.0,
                    "harassment": 0.0,
                    "self-harm": 0.0,
                    "sexual/minors": 0.0,
                    "hate/threatening": 0.0,
                    "violence": 0.0,
                    "violence/graphic": 0.0,
                },
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        long_message = "x" * 10000  # Very long message
        result = service.moderate_text(long_message)
        assert result is not None
        assert result["flagged"] is False

    def test_check_content_allowed(self):
        """Test content checking with allowed content."""
        service = ContentModerationService()

        # Mock the moderate_text method
        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = {
                "flagged": False,
                "categories": {"sexual": 0.1, "hate": 0.0},
                "category_scores": {"sexual": 0.1, "hate": 0.0},
            }

            result = service.check_content("Safe content")
            assert result["allowed"] is True
            assert result["reason"] == "Content passed moderation"

    def test_check_content_blocked_sexual(self):
        """Test content checking with blocked sexual content."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = {
                "flagged": True,
                "categories": {"sexual": 0.9, "hate": 0.0},
                "category_scores": {"sexual": 0.9, "hate": 0.0},
            }

            result = service.check_content("Inappropriate sexual content")
            assert result["allowed"] is False
            assert "sexual content" in result["reason"]

    def test_check_content_blocked_hate(self):
        """Test content checking with blocked hate content."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = {
                "flagged": True,
                "categories": {"sexual": 0.0, "hate": 0.9},
                "category_scores": {"sexual": 0.0, "hate": 0.9},
            }

            result = service.check_content("Hate speech content")
            assert result["allowed"] is False
            assert "hate content" in result["reason"]

    def test_check_content_moderation_error(self):
        """Test content checking when moderation fails."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = None  # Moderation failed

            result = service.check_content("Test content")
            assert result["allowed"] is True  # Allow when moderation fails
            assert "moderation unavailable" in result["reason"]

    def test_check_content_empty_text(self):
        """Test content checking with empty text."""
        service = ContentModerationService()

        result = service.check_content("")
        assert result["allowed"] is True
        assert result["reason"] == "Empty content"

    def test_check_content_whitespace_only(self):
        """Test content checking with whitespace only."""
        service = ContentModerationService()

        result = service.check_content("   \n\t   ")
        assert result["allowed"] is True
        assert result["reason"] == "Empty content"

    def test_is_content_safe(self):
        """Test the is_content_safe method."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            # Safe content
            mock_moderate.return_value = {
                "flagged": False,
                "categories": {"sexual": 0.0, "hate": 0.0},
                "category_scores": {"sexual": 0.0, "hate": 0.0},
            }

            assert service.is_content_safe("Safe content") is True

            # Unsafe content
            mock_moderate.return_value = {
                "flagged": True,
                "categories": {"sexual": 0.9, "hate": 0.0},
                "category_scores": {"sexual": 0.9, "hate": 0.0},
            }

            assert service.is_content_safe("Unsafe content") is False

            # Moderation failure
            mock_moderate.return_value = None
            assert (
                service.is_content_safe("Unknown content") is True
            )  # Allow when moderation fails

    def test_get_moderation_details(self):
        """Test getting detailed moderation information."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = {
                "flagged": True,
                "categories": {"sexual": 0.9, "hate": 0.1},
                "category_scores": {"sexual": 0.9, "hate": 0.1},
            }

            details = service.get_moderation_details("Test content")
            assert details["flagged"] is True
            assert details["highest_category"] == "sexual"
            assert details["highest_score"] == 0.9

    def test_get_moderation_details_safe_content(self):
        """Test getting moderation details for safe content."""
        service = ContentModerationService()

        with patch.object(service, "moderate_text") as mock_moderate:
            mock_moderate.return_value = {
                "flagged": False,
                "categories": {"sexual": 0.1, "hate": 0.0},
                "category_scores": {"sexual": 0.1, "hate": 0.0},
            }

            details = service.get_moderation_details("Safe content")
            assert details["flagged"] is False
            assert details["highest_category"] == "sexual"
            assert details["highest_score"] == 0.1
