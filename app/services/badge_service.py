"""
Badge generation service for user statistics.
"""

import io
from pathlib import Path
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.core.tracing import trace_function
from app.crud.user import get_user_by_id
from app.models import TLog, TPhoto


class BadgeService:
    """Service for generating user statistics badges."""

    def __init__(self):
        self.base_width = 200
        self.base_height = 50
        # Look for logo under /app/res in container, fallback to repo relative path
        candidate_paths = [
            Path("/app/res/tuk_logo.png"),
            Path(__file__).parent.parent.parent / "res" / "tuk_logo.png",
        ]
        for p in candidate_paths:
            if p.exists():
                self.logo_path = p
                break
        else:  # pragma: no cover - runtime safeguard
            self.logo_path = candidate_paths[-1]

    @trace_function("service.badge.get_user_statistics")
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

    @trace_function("service.badge.generate_badge")
    def generate_badge(
        self, db: Session, user_id: int, scale: float = 1.0
    ) -> io.BytesIO:
        """
        Generate a PNG badge for a user showing their statistics.

        Args:
            db: Database session
            user_id: ID of the user
            scale: Scale factor for badge size (default: 1.0)

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

        # Calculate scaled dimensions
        badge_width = int(self.base_width * scale)
        badge_height = int(self.base_height * scale)

        # Get statistics
        distinct_trigs, total_photos = self.get_user_statistics(db, user_id)

        # Load and resize logo
        if not self.logo_path.exists():
            raise FileNotFoundError(f"Logo file not found: {self.logo_path}")

        logo: Image.Image = Image.open(self.logo_path)
        # Resize logo to fit within the left 20% of the badge (scaled)
        logo_max_width = int(badge_width * 0.2)
        logo_max_height = badge_height - int(
            4 * scale
        )  # Leave scaled padding top/bottom

        # Calculate scaling to maintain aspect ratio
        logo_ratio = min(logo_max_width / logo.width, logo_max_height / logo.height)
        new_logo_size = (int(logo.width * logo_ratio), int(logo.height * logo_ratio))
        logo = logo.resize(new_logo_size, Image.Resampling.LANCZOS)

        # Create badge background with scaled dimensions
        badge = Image.new("RGB", (badge_width, badge_height), "white")

        # Paste logo on the left side, centred vertically (scaled)
        logo_x = int(2 * scale)
        logo_y = (badge_height - logo.height) // 2
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
                font_small = ImageFont.truetype(font_path, int(9 * scale))
                font_bold = ImageFont.truetype(font_path, int(13 * scale))
        except Exception:
            # Fallback to default fonts explicitly
            font_small = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        # Calculate text area (right 80% of badge) with scaling
        text_start_x = logo_x + logo.width + int(5 * scale)

        # Prepare text lines
        username = str(user.name)[:20]  # Truncate if too long
        stats_line = f"logged: {distinct_trigs} / photos: {total_photos}"
        footer_line = "Trigpointing.UK"

        # Calculate text positioning with equal spacing between lines (scaled)
        # Estimate text heights for better positioning
        username_height = int(13 * scale)  # Bold font is larger
        stats_height = int(9 * scale)  # Small font
        footer_height = int(9 * scale)  # Small font

        # Calculate equal spacing between the three lines
        total_text_height = username_height + stats_height + footer_height
        available_space = badge_height - total_text_height
        gap_between_lines = available_space // 4  # 4 gaps: top, middle, middle, bottom

        # Position each line with equal gaps (scaled)
        username_y = gap_between_lines - int(2 * scale)  # Move up scaled pixels
        stats_y = (
            username_y + username_height + gap_between_lines + int(1 * scale)
        )  # Scaled offset
        footer_y = stats_y + stats_height + gap_between_lines

        # Draw text lines with equal spacing
        draw.text((text_start_x, username_y), username, font=font_bold, fill="black")

        draw.text(
            (text_start_x, stats_y),
            stats_line,
            font=font_small,
            fill="black",
        )

        draw.text(
            (text_start_x, footer_y),
            footer_line,
            font=font_small,
            fill="black",
        )

        # Save to BytesIO
        img_bytes = io.BytesIO()
        badge.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes
