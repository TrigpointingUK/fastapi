#!/usr/bin/env python3
"""
Apply styling (recolouring, coastline stroke) and scaling to a UK map PNG.

Reads a source [.png, .json] pair, applies colour transformations and optional
scaling, then outputs a new [.png, .json] pair with adjusted affine calibration.

This script is used to pre-generate styled map variants for the /trigs/{id}/map
endpoint, which then only needs to load the pre-styled image and draw a dot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def recolour_and_stroke(
    base: Image.Image,
    land_colour: str | None = None,
    coastline_colour: str | None = None,
) -> Image.Image:
    """
    Recolour land areas and apply coastline stroke to a transparent PNG.

    Args:
        base: RGBA image with transparent background and opaque land
        land_colour: Hex colour for land fill (e.g. '#dddddd'), or None to skip
        coastline_colour: Hex colour for coastline stroke (e.g. '#666666')

    Returns:
        Styled RGBA image
    """
    if not land_colour or land_colour.strip().lower() == "none":
        return base

    # Parse land colour
    hc = land_colour.strip()
    if hc.startswith("#"):
        hc = hc[1:]
    if len(hc) != 6:
        raise ValueError(f"Invalid land_colour hex: {land_colour}")

    r = int(hc[0:2], 16)
    g = int(hc[2:4], 16)
    b = int(hc[4:6], 16)

    # Replace RGB but preserve alpha channel
    alpha_ch = base.getchannel("A")
    recoloured = Image.new("RGBA", base.size, (r, g, b, 255))
    recoloured.putalpha(alpha_ch)

    # Apply coastline stroke
    if coastline_colour:
        edge_mask = alpha_ch.filter(ImageFilter.FIND_EDGES)
        try:
            edge_mask = edge_mask.filter(ImageFilter.MaxFilter(3))
        except Exception:  # pragma: no cover - Pillow compatibility fallback
            edge_mask = edge_mask

        # Parse coastline colour
        sc = coastline_colour.strip()
        if sc.startswith("#"):
            sc = sc[1:]
        if len(sc) == 6:
            stroke_rgb = (int(sc[0:2], 16), int(sc[2:4], 16), int(sc[4:6], 16), 255)
        else:
            stroke_rgb = (102, 102, 102, 255)

        stroke_layer = Image.new("RGBA", base.size, stroke_rgb)
        recoloured.paste(stroke_layer, (0, 0), edge_mask)

    return recoloured


def scale_image(img: Image.Image, target_height: int | None) -> Image.Image:
    """
    Scale image to target height, preserving aspect ratio.

    Args:
        img: Source image
        target_height: Target height in pixels, or None to skip scaling

    Returns:
        Scaled image
    """
    if target_height is None or target_height <= 0 or img.height == target_height:
        return img

    scale = float(target_height) / float(img.height)
    new_w = max(1, int(round(img.width * scale)))

    try:
        resample = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - Pillow compatibility
        try:  # pragma: no cover
            resample = Image.Resampling.NEAREST  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            resample = 0  # type: ignore[assignment]

    return img.resize((new_w, target_height), resample=resample)


def scale_calibration(
    calib: dict, original_size: tuple[int, int], new_size: tuple[int, int]
) -> dict:
    """
    Scale affine transformation to match resized image.

    Args:
        calib: Original calibration dict with 'affine', 'inverse', 'pixel_bbox', 'bounds_geo'
        original_size: (width, height) of original image
        new_size: (width, height) of scaled image

    Returns:
        New calibration dict with scaled affine matrices and pixel_bbox
    """
    orig_w, orig_h = original_size
    new_w, new_h = new_size

    scale_x = new_w / orig_w
    scale_y = new_h / orig_h

    # Scale affine transformation
    A = np.array(calib["affine"], dtype=float)
    # Affine is [[sx, 0, tx], [0, sy, ty]]
    # Scale factors multiply sx, sy; translations multiply by scale
    A_scaled = A.copy()
    A_scaled[0, 0] *= scale_x  # sx
    A_scaled[0, 2] *= scale_x  # tx
    A_scaled[1, 1] *= scale_y  # sy
    A_scaled[1, 2] *= scale_y  # ty

    # Compute inverse of scaled affine
    A_3x3 = np.vstack([A_scaled, [0, 0, 1]])
    A_inv = np.linalg.inv(A_3x3)[:2]

    return {
        "affine": A_scaled.tolist(),
        "inverse": A_inv.tolist(),
        "pixel_bbox": [0, 0, new_w, new_h],
        "bounds_geo": calib.get("bounds_geo", [-11.0, 49.0, 2.5, 61.5]),  # unchanged
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Style and scale a UK map PNG with calibration JSON"
    )
    parser.add_argument(
        "--input-png",
        required=True,
        help="Input PNG file path (e.g. res/ukmap_wgs84_stretched53.png)",
    )
    parser.add_argument(
        "--input-json",
        required=True,
        help="Input calibration JSON (e.g. res/uk_map_calibration_wgs84_stretched53.json)",
    )
    parser.add_argument(
        "--output-png", required=True, help="Output PNG file path (e.g. res/style1.png)"
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Output calibration JSON (e.g. res/style1.json)",
    )
    parser.add_argument(
        "--land-colour",
        default=None,
        help="Hex colour for land fill (e.g. '#dddddd'), or 'none' to skip recolouring",
    )
    parser.add_argument(
        "--coastline-colour",
        default=None,
        help="Hex colour for coastline stroke (e.g. '#666666')",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Target height in pixels (width scaled proportionally)",
    )

    args = parser.parse_args()

    # Load input image and calibration
    input_png = Path(args.input_png)
    input_json = Path(args.input_json)

    if not input_png.exists():
        raise FileNotFoundError(f"Input PNG not found: {input_png}")
    if not input_json.exists():
        raise FileNotFoundError(f"Input JSON not found: {input_json}")

    img = Image.open(input_png).convert("RGBA")
    with open(input_json, "r") as f:
        calib = json.load(f)

    original_size = img.size

    # Apply styling
    if args.land_colour:
        img = recolour_and_stroke(img, args.land_colour, args.coastline_colour)

    # Apply scaling
    if args.height:
        img = scale_image(img, args.height)

    # Update calibration if scaled
    new_calib = calib
    if img.size != original_size:
        new_calib = scale_calibration(calib, original_size, img.size)

    # Save outputs
    output_png = Path(args.output_png)
    output_json = Path(args.output_json)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    img.save(output_png, format="PNG")
    with open(output_json, "w") as f:
        json.dump(new_calib, f, indent=2)

    print(f"✓ Wrote {output_png} ({img.width}×{img.height})")
    print(f"✓ Wrote {output_json}")


if __name__ == "__main__":
    main()
