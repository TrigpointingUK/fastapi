from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw

from api.utils.geocalibrate import calibrate_affine_from_coastline


def _rasterise_polyline(
    points: List[Tuple[float, float]], size=(600, 800)
) -> Image.Image:
    im = Image.new("L", size, color=255)
    draw = ImageDraw.Draw(im)
    # Draw thick polyline to ensure edges
    draw.line(points, fill=0, width=8, joint="curve")
    return im.convert("RGB")


def test_calibration_recovers_affine(tmp_path: Path) -> None:
    # Create a synthetic coastline polyline in lon/lat space
    _ = np.random.default_rng(42)
    base = np.stack(
        [
            np.linspace(-8.0, 2.0, 200),  # longitude
            55.0 + 3.0 * np.sin(np.linspace(0, 5 * math.pi, 200)),  # latitude wiggle
        ],
        axis=1,
    )
    coastline = [(float(lon), float(lat)) for lon, lat in base]

    # Create a ground-truth affine lon/lat → pixel with on-canvas extents
    A_true = np.array([[60.0, 5.0, 450.0], [2.0, -70.0, 4300.0]], dtype=float)
    xy = (A_true @ np.c_[base, np.ones(base.shape[0])].T).T
    # Rasterise a simple path as our "map image"
    pts = [(float(x), float(y)) for x, y in xy]
    im = _rasterise_polyline(pts, size=(900, 900))
    img_path = tmp_path / "synthetic_map.png"
    im.save(img_path)

    result = calibrate_affine_from_coastline(
        image_path=str(img_path), coastline_lonlat=coastline
    )

    # Compare affine matrices up to a similarity tolerance
    assert result.affine.shape == (2, 3)
    # Normalise for sign/scale inconsistencies by testing projection errors
    test_lonlat = np.array([[-7.1, 54.2], [-1.3, 52.9], [1.9, 56.0], [-0.5, 51.0]])
    gt_xy = (A_true @ np.c_[test_lonlat, np.ones(test_lonlat.shape[0])].T).T
    pr_xy = (result.affine @ np.c_[test_lonlat, np.ones(test_lonlat.shape[0])].T).T
    rmse = float(np.sqrt(np.mean(np.sum((gt_xy - pr_xy) ** 2, axis=1))))
    assert rmse < 50.0  # relaxed due to discrete edges and ICP simplifications
