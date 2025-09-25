"""
AWS Rekognition service for image analysis.
"""

import io
import logging
import math
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

        Uses multiple approaches:
        1. Text detection and rotation analysis
        2. Face detection and orientation
        3. Object detection patterns

        Returns orientation confidence scores for 0°, 90°, 180°, 270° rotations.
        """
        if not self.client:
            logger.warning("Rekognition client not available for orientation analysis")
            return None

        logger.info(
            f"Starting orientation analysis for image ({len(image_bytes)} bytes)"
        )

        try:
            # Try text detection first
            logger.debug("Calling Rekognition detect_text API")
            text_response = self.client.detect_text(
                Image={"Bytes": image_bytes},
                Filters={
                    "WordFilter": {
                        "MinConfidence": 30.0,  # Lower threshold for better detection
                    }
                },
            )

            text_detections = text_response.get("TextDetections", [])
            logger.info(f"Found {len(text_detections)} text detections")

            # Analyse text orientations to infer image orientation
            orientations = {"0": 0, "90": 0, "180": 0, "270": 0}
            text_analysis_data = []

            for i, detection in enumerate(text_detections):
                if detection.get("Type") == "WORD":
                    geometry = detection.get("Geometry", {})
                    bbox = geometry.get("BoundingBox", {})
                    detected_text = detection.get("DetectedText", "")
                    confidence = detection.get("Confidence", 0)

                    # Get polygon points for more accurate rotation analysis
                    polygon = geometry.get("Polygon", [])

                    width = bbox.get("Width", 0)
                    height = bbox.get("Height", 0)

                    if width > 0 and height > 0 and len(polygon) >= 4:
                        aspect_ratio = width / height

                        # Calculate rotation from polygon points
                        angle_deg = 0
                        if len(polygon) >= 2:
                            p1, p2 = polygon[0], polygon[1]
                            dx = p2.get("X", 0) - p1.get("X", 0)
                            dy = p2.get("Y", 0) - p1.get("Y", 0)

                            # Calculate angle in degrees
                            angle_rad = math.atan2(dy, dx)
                            angle_deg = math.degrees(angle_rad)

                            # Normalize to 0-360
                            if angle_deg < 0:
                                angle_deg += 360

                        text_info = {
                            "text": detected_text,
                            "confidence": confidence,
                            "aspect_ratio": aspect_ratio,
                            "angle": angle_deg,
                            "bbox": bbox,
                        }
                        text_analysis_data.append(text_info)

                        # Log detailed info for first few detections
                        if i < 5:
                            logger.debug(
                                f"Text '{detected_text}': angle={angle_deg:.1f}°, "
                                f"aspect={aspect_ratio:.2f}, conf={confidence:.1f}"
                            )

                        # Classify orientation based on angle
                        weight = confidence / 100.0  # Use confidence as weight

                        if -15 <= angle_deg <= 15 or 345 <= angle_deg <= 360:
                            orientations["0"] += weight
                        elif 75 <= angle_deg <= 105:
                            orientations["90"] += weight
                        elif 165 <= angle_deg <= 195:
                            orientations["180"] += weight
                        elif 255 <= angle_deg <= 285:
                            orientations["270"] += weight
                        else:
                            # For angles in between, use aspect ratio heuristic
                            if aspect_ratio > 2.5:  # Very wide text
                                orientations["90"] += weight * 0.5
                                orientations["270"] += weight * 0.5
                            elif aspect_ratio < 0.4:  # Very tall text
                                orientations["0"] += weight * 0.5
                                orientations["180"] += weight * 0.5
                            else:
                                orientations["0"] += weight * 0.3

            logger.info(f"Text-based raw orientation scores: {orientations}")

            # Try face detection for additional orientation clues
            faces_count = 0
            try:
                logger.debug("Calling Rekognition detect_faces API")
                face_response = self.client.detect_faces(
                    Image={"Bytes": image_bytes}, Attributes=["POSE"]
                )

                faces = face_response.get("FaceDetails", [])
                faces_count = len(faces)
                logger.info(f"Found {faces_count} faces")

                for face in faces:
                    pose = face.get("Pose", {})
                    roll = pose.get("Roll", 0)  # Roll angle indicates rotation
                    confidence = face.get("Confidence", 0)

                    logger.debug(f"Face roll angle: {roll}°, confidence: {confidence}")

                    # Use face roll to adjust orientation scores
                    weight = confidence / 100.0 * 2  # Faces are strong indicators

                    if -15 <= roll <= 15:
                        orientations["0"] += weight
                    elif 75 <= roll <= 105:
                        orientations[
                            "270"
                        ] += weight  # Face roll is opposite to image rotation
                    elif roll >= 165 or roll <= -165:
                        orientations["180"] += weight
                    elif -105 <= roll <= -75:
                        orientations["90"] += weight

            except Exception as face_error:
                logger.debug(f"Face detection failed (not critical): {face_error}")

            # Convert scores to confidence percentages
            total = sum(orientations.values())
            logger.info(f"Final raw scores: {orientations}, total: {total}")

            if total == 0:
                logger.warning(
                    "No orientation indicators found, defaulting to equal probabilities"
                )
                confidence_scores = {"0": 25.0, "90": 25.0, "180": 25.0, "270": 25.0}
            else:
                confidence_scores = {
                    angle: (score / total) * 100
                    for angle, score in orientations.items()
                }

            # Determine most likely incorrect orientation
            max_incorrect = max(
                confidence_scores["90"],
                confidence_scores["180"],
                confidence_scores["270"],
            )

            likely_incorrect = max_incorrect > confidence_scores["0"]

            if likely_incorrect:
                suggested_rotation = max(
                    [
                        (angle, score)
                        for angle, score in confidence_scores.items()
                        if angle != "0"
                    ],
                    key=lambda x: x[1],
                )[0]
            else:
                suggested_rotation = "0"

            result = {
                "orientation_confidence": confidence_scores,
                "likely_incorrect": likely_incorrect,
                "suggested_rotation": suggested_rotation,
                "debug_info": {
                    "text_detections_count": len(text_detections),
                    "faces_count": faces_count,
                    "raw_scores": orientations,
                    "total_score": total,
                    "sample_text_data": text_analysis_data[:3],  # First 3 for debugging
                },
            }

            logger.info(
                f"Orientation analysis result: likely_incorrect={likely_incorrect}, "
                f"suggested={suggested_rotation}°, confidence_0={confidence_scores['0']:.1f}%"
            )
            return result

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
            logger.warning("Rekognition client not available for content moderation")
            return None

        logger.info(f"Starting content moderation for image ({len(image_bytes)} bytes)")

        try:
            logger.debug("Calling Rekognition detect_moderation_labels API")
            response = self.client.detect_moderation_labels(
                Image={"Bytes": image_bytes}, MinConfidence=50.0
            )

            moderation_labels = response.get("ModerationLabels", [])
            logger.info(f"Found {len(moderation_labels)} moderation labels")

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

            result = {
                "findings": findings,
                "categories": categories,
                "max_confidence": max_confidence,
                "is_inappropriate": categories["inappropriate"],
                "total_labels": len(moderation_labels),
            }

            logger.info(
                f"Content moderation result: {len(findings)} findings, "
                f"inappropriate={categories['inappropriate']}, max_conf={max_confidence:.1f}"
            )
            return result

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
