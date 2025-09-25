"""
AWS Rekognition service for image analysis.
"""

import io
import logging
from typing import Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image

logger = logging.getLogger(__name__)


class RekognitionService:
    """Service for AWS Rekognition image analysis."""

    def __init__(self, region_name: str = "eu-west-1"):
        """Initialise the Rekognition client."""
        try:
            self.client = boto3.client("rekognition", region_name=region_name)
        except Exception as e:
            logger.error(f"Failed to initialise Rekognition client: {e}")
            self.client = None

    def analyse_orientation(self, image_bytes: bytes) -> Optional[Dict]:
        """
        Analyse image orientation using AWS Rekognition.

        Returns orientation confidence scores for 0°, 90°, 180°, 270° rotations.
        """
        if not self.client:
            return None

        try:
            response = self.client.detect_text(
                Image={"Bytes": image_bytes},
                Filters={
                    "WordFilter": {
                        "MinConfidence": 50.0,
                    }
                },
            )

            # Analyse text orientations to infer image orientation
            orientations = {"0": 0, "90": 0, "180": 0, "270": 0}
            text_detections = response.get("TextDetections", [])

            for detection in text_detections:
                if detection.get("Type") == "WORD":
                    geometry = detection.get("Geometry", {})
                    bbox = geometry.get("BoundingBox", {})

                    # Simple heuristic: if text is very wide vs tall, likely rotated
                    width = bbox.get("Width", 0)
                    height = bbox.get("Height", 0)

                    if width > 0 and height > 0:
                        aspect_ratio = width / height
                        if aspect_ratio > 3:  # Very wide text suggests 90/270° rotation
                            orientations["90"] += 1
                            orientations["270"] += 1
                        elif aspect_ratio < 0.3:  # Very tall text suggests normal/180°
                            orientations["0"] += 1
                            orientations["180"] += 1
                        else:
                            orientations["0"] += 1

            # Convert counts to confidence percentages
            total = sum(orientations.values()) or 1
            confidence_scores = {
                angle: (count / total) * 100 for angle, count in orientations.items()
            }

            # Determine most likely incorrect orientation
            max_incorrect = max(
                confidence_scores["90"],
                confidence_scores["180"],
                confidence_scores["270"],
            )

            return {
                "orientation_confidence": confidence_scores,
                "likely_incorrect": max_incorrect > confidence_scores["0"],
                "suggested_rotation": (
                    max(
                        confidence_scores.items(),
                        key=lambda x: x[1] if x[0] != "0" else 0,
                    )[0]
                    if max_incorrect > confidence_scores["0"]
                    else "0"
                ),
            }

        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Rekognition orientation analysis failed: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Orientation analysis failed: {e}")
            return {"error": str(e)}

    def moderate_content(self, image_bytes: bytes) -> Optional[Dict]:
        """
        Analyse image for inappropriate content using AWS Rekognition.

        Detects violence, pornography, advertisements, etc.
        """
        if not self.client:
            return None

        try:
            response = self.client.detect_moderation_labels(
                Image={"Bytes": image_bytes}, MinConfidence=50.0
            )

            moderation_labels = response.get("ModerationLabels", [])

            # Categorise findings
            categories = {
                "inappropriate": False,
                "violence": False,
                "adult_content": False,
                "suggestive": False,
                "drugs": False,
                "tobacco": False,
                "alcohol": False,
                "gambling": False,
                "hate_symbols": False,
            }

            findings = []
            max_confidence = 0.0

            for label in moderation_labels:
                confidence = label.get("Confidence", 0)
                name = label.get("Name", "")
                parent_name = label.get("ParentName", "")

                max_confidence = max(max_confidence, confidence)

                finding = {
                    "label": name,
                    "confidence": confidence,
                    "parent": parent_name,
                }
                findings.append(finding)

                # Categorise the finding
                name_lower = name.lower()
                parent_lower = parent_name.lower()

                if any(
                    term in name_lower or term in parent_lower
                    for term in ["violence", "weapon", "blood"]
                ):
                    categories["violence"] = True
                    categories["inappropriate"] = True

                if any(
                    term in name_lower or term in parent_lower
                    for term in ["nudity", "explicit"]
                ):
                    categories["adult_content"] = True
                    categories["inappropriate"] = True

                if any(
                    term in name_lower or term in parent_lower
                    for term in ["suggestive", "revealing"]
                ):
                    categories["suggestive"] = True
                    categories["inappropriate"] = True

                if any(
                    term in name_lower or term in parent_lower
                    for term in ["drug", "narcotic"]
                ):
                    categories["drugs"] = True
                    categories["inappropriate"] = True

                if "tobacco" in name_lower or "tobacco" in parent_lower:
                    categories["tobacco"] = True
                    categories["inappropriate"] = True

                if "alcohol" in name_lower or "alcohol" in parent_lower:
                    categories["alcohol"] = True

                if "gambling" in name_lower or "gambling" in parent_lower:
                    categories["gambling"] = True
                    categories["inappropriate"] = True

                if any(
                    term in name_lower or term in parent_lower
                    for term in ["hate", "nazi", "confederate"]
                ):
                    categories["hate_symbols"] = True
                    categories["inappropriate"] = True

            return {
                "findings": findings,
                "categories": categories,
                "max_confidence": max_confidence,
                "is_inappropriate": categories["inappropriate"],
                "total_labels": len(moderation_labels),
            }

        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Rekognition content moderation failed: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Content moderation failed: {e}")
            return {"error": str(e)}


def get_image_dimensions(image_bytes: bytes) -> tuple[Optional[int], Optional[int]]:
    """Get image dimensions from bytes using PIL."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.width, image.height
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e}")
        return None, None
