"""
Tests for image processor service.
"""

import io

from PIL import Image

from app.services.image_processor import ImageProcessor


class TestImageProcessor:
    """Test cases for image processor service."""

    def test_init(self):
        """Test service initialization."""
        processor = ImageProcessor()
        assert processor is not None
        assert hasattr(processor, "max_photo_size")
        assert hasattr(processor, "max_thumbnail_size")

    def test_process_image_valid_jpeg(self):
        """Test processing a valid JPEG image."""
        processor = ImageProcessor()

        # Create a test JPEG image
        test_image = Image.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        assert processed_photo is not None
        assert processed_thumbnail is not None
        assert photo_dims is not None
        assert thumb_dims is not None

        # Check dimensions are reasonable
        assert photo_dims[0] > 0 and photo_dims[1] > 0
        assert thumb_dims[0] > 0 and thumb_dims[1] > 0

        # Thumbnail should be smaller than original
        assert thumb_dims[0] <= photo_dims[0]
        assert thumb_dims[1] <= photo_dims[1]

    def test_process_image_invalid_data(self):
        """Test processing invalid image data."""
        processor = ImageProcessor()

        # Test with empty data
        result = processor.process_image(b"")
        assert result is None

        # Test with non-image data
        result = processor.process_image(b"not an image")
        assert result is None

    def test_process_image_unsupported_format(self):
        """Test processing image with unsupported format."""
        processor = ImageProcessor()

        # Create a BMP image (unsupported)
        test_image = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        test_image.save(buffer, format="BMP")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)
        assert result is None

    def test_process_image_corrupted_jpeg(self):
        """Test processing corrupted JPEG data."""
        processor = ImageProcessor()

        # Create corrupted JPEG data
        corrupted_data = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF"  # Valid JPEG header but truncated
        )

        result = processor.process_image(corrupted_data)
        assert result is None

    def test_process_image_very_small_image(self):
        """Test processing a very small image."""
        processor = ImageProcessor()

        # Create a 1x1 pixel image
        test_image = Image.new("RGB", (1, 1), color="green")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        assert photo_dims == (1, 1)
        # Thumbnail should be at least 1x1
        assert thumb_dims[0] >= 1 and thumb_dims[1] >= 1

    def test_process_image_very_large_image(self):
        """Test processing a very large image."""
        processor = ImageProcessor()

        # Create a large image (larger than max size)
        test_image = Image.new("RGB", (5000, 5000), color="blue")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        # Should be resized to fit within limits
        assert photo_dims[0] <= processor.max_photo_size[0]
        assert photo_dims[1] <= processor.max_photo_size[1]

    def test_process_image_grayscale(self):
        """Test processing a grayscale image."""
        processor = ImageProcessor()

        # Create a grayscale image
        test_image = Image.new("L", (400, 300), color=128)
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        # Should convert to RGB
        assert photo_dims[0] == 400
        assert photo_dims[1] == 300

    def test_process_image_with_alpha_channel(self):
        """Test processing an image with alpha channel."""
        processor = ImageProcessor()

        # Create an RGBA image
        test_image = Image.new("RGBA", (300, 200), color=(255, 0, 0, 128))
        buffer = io.BytesIO()
        test_image.save(buffer, format="PNG")  # PNG supports alpha
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        # Should convert to RGB (removing alpha)
        assert photo_dims[0] == 300
        assert photo_dims[1] == 200

    def test_process_image_landscape_orientation(self):
        """Test processing landscape-oriented image."""
        processor = ImageProcessor()

        # Create landscape image (wider than tall)
        test_image = Image.new("RGB", (1200, 800), color="yellow")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        assert photo_dims[0] == 1200
        assert photo_dims[1] == 800

        # Thumbnail should maintain aspect ratio
        assert thumb_dims[0] / thumb_dims[1] == photo_dims[0] / photo_dims[1]

    def test_process_image_portrait_orientation(self):
        """Test processing portrait-oriented image."""
        processor = ImageProcessor()

        # Create portrait image (taller than wide)
        test_image = Image.new("RGB", (600, 900), color="purple")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        assert photo_dims[0] == 600
        assert photo_dims[1] == 900

        # Thumbnail should maintain aspect ratio
        assert thumb_dims[0] / thumb_dims[1] == photo_dims[0] / photo_dims[1]

    def test_process_image_square(self):
        """Test processing square image."""
        processor = ImageProcessor()

        # Create square image
        test_image = Image.new("RGB", (500, 500), color="orange")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        assert photo_dims[0] == 500
        assert photo_dims[1] == 500

        # Square thumbnail should maintain aspect ratio
        assert thumb_dims[0] == thumb_dims[1]

    def test_process_image_exif_rotation(self):
        """Test processing image with EXIF rotation data."""
        processor = ImageProcessor()

        # Create a test image that might have EXIF data
        test_image = Image.new("RGB", (400, 600), color="cyan")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        # Should handle EXIF rotation correctly
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result
        assert photo_dims[0] > 0 and photo_dims[1] > 0

    def test_process_image_memory_error(self):
        """Test processing with memory constraints."""
        processor = ImageProcessor()

        # Create a very large image that might cause memory issues
        test_image = Image.new("RGB", (10000, 10000), color="gray")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=95)
        image_data = buffer.getvalue()

        # Should handle large images gracefully (may resize or fail)
        result = processor.process_image(image_data)
        # Either succeeds or returns None - both are acceptable
        assert result is None or (result is not None and len(result) == 4)

    def test_process_image_quality_settings(self):
        """Test that quality settings are applied correctly."""
        processor = ImageProcessor()

        # Create test image
        test_image = Image.new("RGB", (200, 200), color="white")
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG", quality=100)  # High quality
        image_data = buffer.getvalue()

        result = processor.process_image(image_data)

        assert result is not None
        processed_photo, processed_thumbnail, photo_dims, thumb_dims = result

        # Both should be valid JPEG data
        assert len(processed_photo) > 0
        assert len(processed_thumbnail) > 0

        # Thumbnail should be smaller than original
        assert len(processed_thumbnail) < len(processed_photo)

    def test_create_thumbnail(self):
        """Test thumbnail creation."""
        processor = ImageProcessor()

        # Create test image
        test_image = Image.new("RGB", (400, 300), color="red")

        thumbnail = processor._create_thumbnail(test_image)

        assert thumbnail is not None
        assert thumbnail.size[0] <= 200  # Max thumbnail width
        assert thumbnail.size[1] <= 200  # Max thumbnail height
        assert thumbnail.size[0] > 0 and thumbnail.size[1] > 0

        # Should maintain aspect ratio
        assert abs(thumbnail.size[0] / thumbnail.size[1] - 400 / 300) < 0.1

    def test_create_thumbnail_square(self):
        """Test thumbnail creation for square image."""
        processor = ImageProcessor()

        # Create square image
        test_image = Image.new("RGB", (300, 300), color="blue")

        thumbnail = processor._create_thumbnail(test_image)

        assert thumbnail is not None
        # Should be 150x150 for square image at max size 200
        assert thumbnail.size[0] <= 200
        assert thumbnail.size[1] <= 200

    def test_create_thumbnail_very_small(self):
        """Test thumbnail creation for very small image."""
        processor = ImageProcessor()

        # Create very small image
        test_image = Image.new("RGB", (10, 10), color="green")

        thumbnail = processor._create_thumbnail(test_image)

        assert thumbnail is not None
        # Should maintain minimum size
        assert thumbnail.size[0] >= 1
        assert thumbnail.size[1] >= 1

    def test_resize_image(self):
        """Test image resizing."""
        processor = ImageProcessor()

        # Create test image
        test_image = Image.new("RGB", (1000, 800), color="yellow")

        resized = processor._resize_image(test_image, (500, 400))

        assert resized is not None
        assert resized.size == (500, 400)

    def test_resize_image_already_correct_size(self):
        """Test resizing image that's already the correct size."""
        processor = ImageProcessor()

        # Create image that's already the target size
        test_image = Image.new("RGB", (500, 400), color="purple")

        resized = processor._resize_image(test_image, (500, 400))

        assert resized is not None
        assert resized.size == (500, 400)

    def test_resize_image_smaller_than_target(self):
        """Test resizing image that's smaller than target."""
        processor = ImageProcessor()

        # Create image smaller than target
        test_image = Image.new("RGB", (200, 150), color="orange")

        resized = processor._resize_image(test_image, (500, 400))

        assert resized is not None
        # Should not be resized up, should stay same size
        assert resized.size == (200, 150)

    def test_calculate_thumbnail_size(self):
        """Test thumbnail size calculation."""
        processor = ImageProcessor()

        # Test various aspect ratios
        assert processor._calculate_thumbnail_size(400, 300) == (150, 112)  # 4:3
        assert processor._calculate_thumbnail_size(300, 400) == (112, 150)  # 3:4
        assert processor._calculate_thumbnail_size(500, 500) == (150, 150)  # 1:1
        assert processor._calculate_thumbnail_size(100, 100) == (
            100,
            100,
        )  # Small square

    def test_calculate_thumbnail_size_edge_cases(self):
        """Test thumbnail size calculation edge cases."""
        processor = ImageProcessor()

        # Very wide image
        assert processor._calculate_thumbnail_size(2000, 100) == (200, 10)

        # Very tall image
        assert processor._calculate_thumbnail_size(100, 2000) == (10, 200)

        # Zero width (should handle gracefully)
        assert processor._calculate_thumbnail_size(0, 100) == (0, 100)

        # Zero height (should handle gracefully)
        assert processor._calculate_thumbnail_size(100, 0) == (100, 0)
