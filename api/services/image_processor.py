"""
Image processing service for photo uploads.
"""

import io
import logging
from typing import Optional, Tuple

from PIL import Image, ImageOps

from api.core.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Service for processing uploaded images."""

    def __init__(self):
        """Initialise the image processor."""
        pass

    def process_image(self, image_bytes: bytes) -> Tuple[
        Optional[bytes],
        Optional[bytes],
        Optional[Tuple[int, int]],
        Optional[Tuple[int, int]],
    ]:
        """
        Process uploaded image: resize, create thumbnail, apply EXIF orientation.

        Args:
            image_bytes: Raw image data

        Returns:
            Tuple of (processed_image_bytes, thumbnail_bytes, image_dimensions, thumbnail_dimensions)
        """
        try:
            # Open image and apply EXIF orientation
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Apply EXIF orientation
                img = ImageOps.exif_transpose(img)
                if img is None:
                    return None, None, None, None

                # Get original dimensions
                original_width, original_height = img.size

                # Calculate new dimensions for main image (max 4000x4000, preserve aspect ratio)
                image_dimensions = self._calculate_dimensions(
                    original_width, original_height, settings.MAX_IMAGE_DIMENSION
                )

                # Resize main image
                if image_dimensions != (original_width, original_height):
                    img = img.resize(image_dimensions, Image.Resampling.LANCZOS)

                # Convert to RGB if necessary (strip EXIF and ensure compatibility)
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Save processed image
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=95, optimize=True)
                processed_image_bytes = output.getvalue()

                # Calculate thumbnail dimensions (max 120x120, preserve aspect ratio)
                thumbnail_dimensions = self._calculate_dimensions(
                    original_width, original_height, settings.THUMBNAIL_SIZE
                )

                # Create thumbnail
                if thumbnail_dimensions != (original_width, original_height):
                    thumbnail = img.resize(
                        thumbnail_dimensions, Image.Resampling.LANCZOS
                    )
                else:
                    thumbnail = img.copy()

                # Save thumbnail
                thumbnail_output = io.BytesIO()
                thumbnail.save(
                    thumbnail_output, format="JPEG", quality=85, optimize=True
                )
                thumbnail_bytes = thumbnail_output.getvalue()

                logger.info(
                    f"Processed image: {original_width}x{original_height} -> "
                    f"{image_dimensions[0]}x{image_dimensions[1]}, "
                    f"thumbnail: {thumbnail_dimensions[0]}x{thumbnail_dimensions[1]}"
                )

                return (
                    processed_image_bytes,
                    thumbnail_bytes,
                    image_dimensions,
                    thumbnail_dimensions,
                )

        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return None, None, None, None

    def _calculate_dimensions(
        self, width: int, height: int, max_size: int
    ) -> Tuple[int, int]:
        """Calculate new dimensions preserving aspect ratio."""
        if width <= max_size and height <= max_size:
            return width, height

        aspect_ratio = width / height

        if width > height:
            new_width = min(width, max_size)
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = min(height, max_size)
            new_width = int(new_height * aspect_ratio)

        # Ensure neither dimension exceeds max_size
        new_width = min(new_width, max_size)
        new_height = min(new_height, max_size)

        return new_width, new_height

    def validate_image(self, image_bytes: bytes) -> Tuple[bool, str]:
        """Validate uploaded image file."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Check file size
                if len(image_bytes) > settings.MAX_IMAGE_SIZE:
                    return (
                        False,
                        f"File size exceeds maximum of {settings.MAX_IMAGE_SIZE // (1024 * 1024)}MB",
                    )

                # Check format
                if img.format not in ["JPEG", "JPG"]:
                    return False, "Only JPEG images are supported"

                # Check if image is valid
                img.verify()

                return True, "Image is valid"

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False, f"Invalid image file: {str(e)}"
