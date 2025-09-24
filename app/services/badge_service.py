"""
Badge generation service for user statistics.
"""

import io
from pathlib import Path
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.crud.user import get_user_by_id
from app.models import TLog, TPhoto


class BadgeService:
    """Service for generating user statistics badges."""

    def __init__(self):
        self.badge_width = 200
        self.badge_height = 50
        self.logo_path = Path(__file__).parent.parent.parent / "res" / "tuk_logo.png"

    def get_user_statistics(self, db: Session, user_id: int) -> Tuple[int, int]:
        """
        Get user statistics: distinct trigpoints logged and total photos.

        Returns:
            Tuple of (distinct_trigpoints_logged, total_photos)
        """
        # Count distinct trigpoints logged by the user
        distinct_trigs = (
            db.query(TLog.trig_id).filter(TLog.user_id == user_id).distinct().count()
        )

        # Count total photos uploaded by the user (via tlog relationship)
        total_photos = (
            db.query(TPhoto)
            .join(TLog, TPhoto.tlog_id == TLog.id)
            .filter(TLog.user_id == user_id)
            .filter(TPhoto.deleted_ind != "Y")  # Exclude soft-deleted photos
            .count()
        )

        return distinct_trigs, total_photos

    def generate_badge(self, db: Session, user_id: int) -> io.BytesIO:
        """
        Generate a PNG badge for a user showing their statistics.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            BytesIO object containing the PNG image data

        Raises:
            ValueError: If user not found
            FileNotFoundError: If logo file not found
        """
        # Get user data
        user = get_user_by_id(db, user_id=user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Get statistics
        distinct_trigs, total_photos = self.get_user_statistics(db, user_id)

        # Load and resize logo
        if not self.logo_path.exists():
            raise FileNotFoundError(f"Logo file not found: {self.logo_path}")

        logo: Image.Image = Image.open(self.logo_path)
        # Resize logo to fit within the left 20% of the badge (40px width max)
        logo_max_width = int(self.badge_width * 0.2)
        logo_max_height = self.badge_height - 4  # Leave 2px padding top/bottom

        # Calculate scaling to maintain aspect ratio
        logo_ratio = min(logo_max_width / logo.width, logo_max_height / logo.height)
        new_logo_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
        logo = logo.resize(new_logo_size, Image.Resampling.LANCZOS)

        # Create badge background
        badge = Image.new("RGB", (self.badge_width, self.badge_height), "white")

        # Paste logo on the left side, centred vertically
        logo_x = 2
        logo_y = (self.badge_height - logo.height) // 2
        badge.paste(logo, (logo_x, logo_y), logo if logo.mode == "RGBA" else None)

        # Set up drawing context
        draw = ImageDraw.Draw(badge)

        # Try to use a system font, fallback to default
        # Predeclare as Any to satisfy mypy across different font classes
        font_small: Any = ImageFont.load_default()
        font_bold: Any = ImageFont.load_default()
        try:
            # Common font paths on Linux systems
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/arial.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
            font_path = None
            for path in font_paths:
                if Path(path).exists():
                    font_path = path
                    break

            if font_path:
                font_small = ImageFont.truetype(font_path, 9)
                font_bold = ImageFont.truetype(font_path, 12)
        except Exception:
            # Fallback to default fonts explicitly
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        # Calculate text area (right 80% of badge)
        text_start_x = logo_x + logo.width + 5

        # Prepare text lines
        username = str(user.name)[:20]  # Truncate if too long
        stats_line = f"logged: {distinct_trigs} / photos: {total_photos}"
        footer_line = "Trigpointing.UK"

        # Calculate text positioning
        line_height = 12
        total_text_height = 3 * line_height
        start_y = (self.badge_height - total_text_height) // 2

        # Draw text lines with bold username
        draw.text((text_start_x, start_y), username, font=font_bold, fill="black")

        draw.text(
            (text_start_x, start_y + line_height),
            stats_line,
            font=font_small,
            fill="black",
        )

        draw.text(
            (text_start_x, start_y + 2 * line_height),
            footer_line,
            font=font_small,
            fill="black",
        )

        # Save to BytesIO
        img_bytes = io.BytesIO()
        badge.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes
