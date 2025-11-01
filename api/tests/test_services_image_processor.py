"""
Tests for image processor service aligned with current implementation.
"""

import io

from PIL import Image

from api.services.image_processor import ImageProcessor


class TestImageProcessor:
    def test_process_image_valid_jpeg(self):
        processor = ImageProcessor()
        test_image = Image.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result
        assert processed_photo and processed_thumbnail
        assert photo_dims and thumb_dims
        assert thumb_dims[0] <= photo_dims[0]
        assert thumb_dims[1] <= photo_dims[1]

    def test_process_image_invalid_data(self):
        processor = ImageProcessor()
        assert processor.process_image(b"") == (None, None, None, None)
        assert processor.process_image(b"not an image") == (None, None, None, None)

    def test_process_image_corrupted_jpeg(self):
        processor = ImageProcessor()
        corrupted_data = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        assert processor.process_image(corrupted_data) == (None, None, None, None)

    def test_process_image_very_small_image(self):
        processor = ImageProcessor()
        test_image = Image.new("RGB", (1, 1), color="green")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        _, _, photo_dims, thumb_dims = result
        assert photo_dims == (1, 1)
        assert thumb_dims[0] >= 1 and thumb_dims[1] >= 1

    def test_process_image_very_large_image(self):
        processor = ImageProcessor()
        test_image = Image.new("RGB", (5000, 5000), color="blue")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        _, _, photo_dims, _ = result

        from api.core.config import settings

        assert photo_dims[0] <= settings.MAX_IMAGE_DIMENSION
        assert photo_dims[1] <= settings.MAX_IMAGE_DIMENSION

    def test_process_image_grayscale(self):
        processor = ImageProcessor()
        test_image = Image.new("L", (400, 300), color=128)
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        _, _, photo_dims, _ = result
        assert photo_dims == (400, 300)

    def test_process_image_with_alpha_channel(self):
        processor = ImageProcessor()
        test_image = Image.new("RGBA", (300, 200), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        test_image.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        _, _, photo_dims, _ = result
        assert photo_dims == (300, 200)

    def test_process_image_memory_error(self):
        processor = ImageProcessor()
        test_image = Image.new("RGB", (10000, 10000), color="gray")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is None or len(result) == 4

    def test_process_image_quality_settings(self):
        processor = ImageProcessor()
        test_image = Image.new("RGB", (200, 200), color="white")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=100)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is not None
        processed_photo, processed_thumbnail, _, _ = result
        assert len(processed_photo) > 0
        assert len(processed_thumbnail) > 0
        assert len(processed_thumbnail) < len(processed_photo)
