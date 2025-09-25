"""
Tests for AWS Rekognition service.
"""

import io
from unittest.mock import Mock, patch

from PIL import Image

from app.services.rekognition import RekognitionService, get_image_dimensions


def create_test_image_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create test image bytes using PIL."""
    image = Image.new("RGB", (width, height), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_get_image_dimensions():
    """Test image dimension extraction."""
    image_bytes = create_test_image_bytes(200, 150)
    width, height = get_image_dimensions(image_bytes)

    assert width == 200
    assert height == 150


def test_get_image_dimensions_invalid():
    """Test image dimension extraction with invalid data."""
    width, height = get_image_dimensions(b"invalid image data")

    assert width is None
    assert height is None


@patch("boto3.client")
def test_rekognition_service_init_success(mock_boto_client):
    """Test successful Rekognition service initialisation."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    service = RekognitionService()

    assert service.client == mock_client
    mock_boto_client.assert_called_once_with("rekognition", region_name="eu-west-1")


@patch("boto3.client")
def test_rekognition_service_init_failure(mock_boto_client):
    """Test Rekognition service initialisation failure."""
    mock_boto_client.side_effect = Exception("AWS credentials not configured")

    service = RekognitionService()

    assert service.client is None


@patch("boto3.client")
def test_analyse_orientation_success(mock_boto_client):
    """Test successful orientation analysis."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    # Mock response with text detections
    mock_client.detect_text.return_value = {
        "TextDetections": [
            {
                "Type": "WORD",
                "Geometry": {"BoundingBox": {"Width": 0.1, "Height": 0.05}},
            },
            {
                "Type": "WORD",
                "Geometry": {"BoundingBox": {"Width": 0.05, "Height": 0.1}},
            },
        ]
    }

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.analyse_orientation(image_bytes)

    assert result is not None
    assert "orientation_confidence" in result
    assert "likely_incorrect" in result
    assert "suggested_rotation" in result

    # Check confidence scores are present
    confidence = result["orientation_confidence"]
    assert "0" in confidence
    assert "90" in confidence
    assert "180" in confidence
    assert "270" in confidence


@patch("boto3.client")
def test_analyse_orientation_uses_labels_and_sky(mock_boto_client):
    """When no text or faces, labels and sky bias should influence scores."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    # No text detections
    mock_client.detect_text.return_value = {"TextDetections": []}
    # No faces
    mock_client.detect_faces.return_value = {"FaceDetails": []}
    # Labels include a Tower instance that's wide, suggesting 90/270
    mock_client.detect_labels.return_value = {
        "Labels": [
            {
                "Name": "Tower",
                "Confidence": 95.0,
                "Instances": [
                    {"BoundingBox": {"Width": 0.5, "Height": 0.2}, "Confidence": 92.0}
                ],
            }
        ]
    }

    service = RekognitionService()
    # Create an image with blue on the left to bias towards 90° as well
    img = Image.new("RGB", (100, 100), color="white")
    for x in range(0, 50):
        for y in range(0, 100):
            img.putpixel((x, y), (50, 80, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    result = service.analyse_orientation(image_bytes)

    assert result is not None
    conf = result["orientation_confidence"]
    # Expect non-uniform scores favouring 90/270 due to tower aspect and left sky
    assert conf["90"] > 25.0 or conf["270"] > 25.0


@patch("boto3.client")
def test_analyse_orientation_model_boosts_when_weak_signal(
    mock_boto_client, monkeypatch
):
    """Model prediction should boost a weak raw signal when enabled and confident."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    # No text or faces or labels -> weak signal
    mock_client.detect_text.return_value = {"TextDetections": []}
    mock_client.detect_faces.return_value = {"FaceDetails": []}
    mock_client.detect_labels.return_value = {"Labels": []}

    # Enable model via settings patch
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "ORIENTATION_MODEL_ENABLED", True)
    monkeypatch.setattr(cfg.settings, "ORIENTATION_MODEL_THRESHOLD", 0.5)

    # Stub classifier to return 90° with high confidence
    from app.services import rekognition as rek

    class StubClassifier:
        def predict(self, _):
            return ("90", 0.9)

    monkeypatch.setattr(
        rek, "OrientationClassifier", lambda *_args, **_kw: StubClassifier()
    )

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.analyse_orientation(image_bytes)
    assert result is not None
    conf = result["orientation_confidence"]
    assert conf["90"] > conf["0"]


@patch("boto3.client")
def test_analyse_orientation_no_client(mock_boto_client):
    """Test orientation analysis with no client."""
    mock_boto_client.side_effect = Exception("No AWS")

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.analyse_orientation(image_bytes)

    assert result is None


@patch("boto3.client")
def test_moderate_content_success(mock_boto_client):
    """Test successful content moderation."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    # Mock response with moderation labels
    mock_client.detect_moderation_labels.return_value = {
        "ModerationLabels": [
            {"Name": "Violence", "Confidence": 85.5, "ParentName": "Explicit Nudity"},
            {"Name": "Suggestive", "Confidence": 65.2, "ParentName": ""},
        ]
    }

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.moderate_content(image_bytes)

    assert result is not None
    assert "findings" in result
    assert "categories" in result
    assert "max_confidence" in result
    assert "is_inappropriate" in result
    assert "total_labels" in result

    # Check findings structure
    findings = result["findings"]
    assert len(findings) == 2
    assert findings[0]["label"] == "Violence"
    assert findings[0]["confidence"] == 85.5

    # Check categories
    categories = result["categories"]
    assert categories["violence"] is True
    assert categories["inappropriate"] is True
    assert result["is_inappropriate"] is True
    assert result["max_confidence"] == 85.5


@patch("boto3.client")
def test_moderate_content_clean_image(mock_boto_client):
    """Test content moderation with clean image."""
    mock_client = Mock()
    mock_boto_client.return_value = mock_client

    # Mock response with no moderation labels
    mock_client.detect_moderation_labels.return_value = {"ModerationLabels": []}

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.moderate_content(image_bytes)

    assert result is not None
    assert result["findings"] == []
    assert result["is_inappropriate"] is False
    assert result["max_confidence"] == 0.0
    assert result["total_labels"] == 0


@patch("boto3.client")
def test_moderate_content_no_client(mock_boto_client):
    """Test content moderation with no client."""
    mock_boto_client.side_effect = Exception("No AWS")

    service = RekognitionService()
    image_bytes = create_test_image_bytes()

    result = service.moderate_content(image_bytes)

    assert result is None
